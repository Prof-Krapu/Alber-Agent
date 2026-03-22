import os
from secure_executor import SecurePythonExecutor, get_executor


def test_executor_rejects_dangerous_imports():
    code = "import os\nprint('hello')"
    exe = SecurePythonExecutor(timeout=1, memory_limit_mb=64, workspace=".")
    out, err = exe.execute(code)
    assert err is not None
    assert "Import interdit" in err or "Pattern dangereux" in err


def test_executor_runs_simple_code():
    code = "print('42')"
    exe = SecurePythonExecutor(timeout=2, memory_limit_mb=64, workspace=".")
    out, err = exe.execute(code)
    assert err is None
    assert "42" in out
