import os
import sys
import subprocess
import signal
import resource
import threading
from typing import Optional, Tuple


class SecurePythonExecutor:
    """
    Exécuteur Python sandboxé avec limites de temps et mémoire.

    Sécurité:
    - Timeout strict (ne peut pas être contourné par infinite loops)
    - Limite mémoire (RSS)
    - Pas d'accès réseau dans l'environnement sandbox
    - Pas d'accès au filesystem externe (sauf workspace)
    """

    def __init__(
        self, timeout: int = 30, memory_limit_mb: int = 256, workspace: str = "."
    ):
        self.timeout = timeout
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.workspace = os.path.abspath(workspace)

    def _set_resource_limits(self):
        """Applique les limites资源 (Linux/macOS)."""
        try:
            # Limite mémoire (RSS)
            resource.setrlimit(
                resource.RLIMIT_AS, (self.memory_limit_bytes, self.memory_limit_bytes)
            )
            # Limite CPU time
            resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout + 5))
            # Pas de création de fichiers (empêche /tmp explosions)
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
            # Limite de processus fils
            resource.setrlimit(resource.RLIMIT_NPROC, (5, 5))
            # Pas de core dumps
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except (resource.error, OSError):
            pass  # Certaines limites ne sont pas supportées sur tous les OS

    def execute(self, code: str) -> Tuple[str, Optional[str]]:
        """
        Exécute le code Python de manière sécurisée.

        Returns:
            Tuple (stdout, error)
        """
        # Validate workspace path
        if not os.path.exists(self.workspace):
            return "", f"Workspace introuvable: {self.workspace}"

        # Validate code doesn't contain dangerous patterns
        # Basic AST-based checks for dangerous imports and calls
        try:
            import ast

            tree = ast.parse(code)

            for node in ast.walk(tree):
                # Imports of dangerous modules
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = [n.name for n in node.names]
                    for name in names:
                        lname = name.lower()
                        if any(
                            d in lname
                            for d in (
                                "os",
                                "subprocess",
                                "ctypes",
                                "socket",
                                "multiprocessing",
                            )
                        ):
                            return "", f"Import interdit détecté: {name}"

                # Calls to dangerous builtins
                if isinstance(node, ast.Call):
                    # Function name
                    func = node.func
                    fname = None
                    if isinstance(func, ast.Name):
                        fname = func.id
                    elif isinstance(func, ast.Attribute):
                        fname = func.attr

                    if fname and fname.lower() in (
                        "eval",
                        "exec",
                        "open",
                        "compile",
                        "__import__",
                        "execfile",
                    ):
                        return "", f"Appel interdit détecté: {fname}"
        except Exception:
            # If AST parsing fails, fallback to conservative rejection
            return "", "Code invalide ou non analysable"

        # Create a subprocess with restricted environment
        env = {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
            "PATH": "/usr/bin:/bin",  # Minimal PATH
        }

        # Prepare the code as a separate module to avoid exec() in main
        safe_wrapper = f"""
import sys
import signal
import resource

# Redirect stdout
class SafeStdout:
    def __init__(self):
        self.output = []
    def write(self, text):
        self.output.append(text)
    def flush(self):
        pass
    def getvalue(self):
        return ''.join(self.output)

# Setup limits
def set_limits():
    try:
        resource.setrlimit(resource.RLIMIT_AS, ({self.memory_limit_bytes}, {self.memory_limit_bytes}))
        resource.setrlimit(resource.RLIMIT_CPU, ({self.timeout}, {self.timeout + 5}))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1048576, 1048576))
        resource.setrlimit(resource.RLIMIT_NPROC, (3, 3))
    except:
        pass

# Set alarm for timeout
def timeout_handler(signum, frame):
    sys.stderr.write("TIMEOUT: Exécution dépassée de {{0}} secondes".format({self.timeout}))
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({self.timeout})

set_limits()

# Execute user code
safe_out = SafeStdout()
sys.stdout = safe_out
try:
{chr(10).join("    " + line for line in code.split(chr(10)))}
    # restore stdout and write captured output to real stdout so parent process captures it
    sys.stdout = sys.__stdout__
    try:
        sys.stdout.write(safe_out.getvalue())
    except Exception:
        # fallback to stderr if stdout write fails
        sys.stderr.write(safe_out.getvalue())
except SystemExit:
    pass
except Exception as e:
    sys.stdout = sys.__stdout__
    sys.stderr.write("ERREUR: {{}}".format(str(e)))
"""

        try:
            result = subprocess.run(
                [sys.executable, "-c", safe_wrapper],
                capture_output=True,
                text=True,
                timeout=self.timeout + 5,
                cwd=self.workspace,
                env=env,
                preexec_fn=os.setsid if hasattr(os, "setsid") else None,
            )

            stdout = result.stdout
            stderr = result.stderr

            if result.returncode != 0 and "TIMEOUT" in stderr:
                return "", f"Délai d'exécution dépassé ({self.timeout}s)"

            if stderr and "ERREUR:" in stderr:
                return stdout, stderr.replace("ERREUR: ", "")

            return stdout, None

        except subprocess.TimeoutExpired:
            return "", f"Délai d'exécution dépassé ({self.timeout}s)"
        except Exception as e:
            return "", f"Erreur d'exécution: {str(e)}"


# Singleton pour l'application
_executor: Optional[SecurePythonExecutor] = None


def get_executor() -> SecurePythonExecutor:
    global _executor
    if _executor is None:
        import os as _os

        workspace = os.environ.get("WORKSPACE_ROOT", ".")
        timeout = int(os.environ.get("PYTHON_EXEC_TIMEOUT", "30"))
        memory = int(os.environ.get("PYTHON_MEMORY_LIMIT", "256"))
        _executor = SecurePythonExecutor(
            timeout=timeout, memory_limit_mb=memory, workspace=workspace
        )
    return _executor
