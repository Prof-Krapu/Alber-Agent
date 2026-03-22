"""
Validateur d'entrées pour Albert IA Agentic.
Utilise Pydantic pour validation robuste et typage.
"""

import re
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ChatModel(str, Enum):
    MISTRAL_8B = "mistralai/Ministral-3-8B-Instruct-2512"
    MISTRAL_24B = "mistralai/Mistral-Small-3.2-24B-Instruct-2506"
    GPT_OSS = "openai/gpt-oss-120b"
    QWEN_CODER = "Qwen/Qwen3-Coder-30B-A3B-Instruct"

    @classmethod
    def values(cls) -> List[str]:
        return [e.value for e in cls]


class ChatRequest(BaseModel):
    """Schéma de validation pour les requêtes de chat."""

    message: str = Field(
        ..., min_length=1, max_length=10000, description="Message utilisateur"
    )
    model: str = Field(
        default="mistralai/Ministral-3-8B-Instruct-2512",
        description="Modèle à utiliser",
    )

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        """Nettoie le message de caractères dangereux."""
        if not v or not v.strip():
            raise ValueError("Message ne peut pas être vide")
        # Supprimer les null bytes et caractères de contrôle
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", v)
        return cleaned.strip()

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Valide que le modèle est supported."""
        if v not in ChatModel.values():
            raise ValueError(
                f"Modèle inconnu: {v}. Modèles disponibles: {ChatModel.values()}"
            )
        return v


class ToolExecutionRequest(BaseModel):
    """Schéma de validation pour l'exécution d'outils."""

    tool_name: str = Field(
        ..., min_length=1, max_length=100, description="Nom de l'outil"
    )
    arguments: dict = Field(default_factory=dict, description="Arguments de l'outil")

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Valide le nom de l'outil."""
        # Uniquement alphanumérique et underscores
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(
                "Nom d'outil invalide (caractères autorisés: a-z, A-Z, 0-9, _)"
            )

        # Longueur max pour éviter DoS
        if len(v) > 50:
            raise ValueError("Nom d'outil trop long")

        return v

    @field_validator("arguments")
    @classmethod
    def validate_arguments(cls, v: dict) -> dict:
        """Valide les arguments de l'outil."""
        # Limiter la taille des arguments pour éviter DoS
        import json

        args_size = len(json.dumps(v))
        if args_size > 50000:  # 50KB max
            raise ValueError("Arguments trop volumineux (>50KB)")
        return v


class FilePathValidator:
    """
    Validateur de chemins de fichiers pour prévenir les path traversal.
    """

    def __init__(self, allowed_root: str):
        import os

        self.allowed_root = os.path.abspath(allowed_root)

    def validate(self, file_path: str) -> Optional[str]:
        """
        Valide qu'un chemin est dans le workspace autorisé.
        Returns: Le chemin absolu si valide, None sinon.
        """
        import os

        if not file_path:
            return None

        # Supprimer les null bytes
        file_path = file_path.replace("\x00", "")

        # Empêcher les path traversal explicites
        if ".." in file_path or file_path.startswith("/"):
            return None

        try:
            abs_path = os.path.abspath(os.path.join(self.allowed_root, file_path))

            # Vérifier que le chemin final est dans allowed_root
            if not abs_path.startswith(self.allowed_root):
                return None

            return abs_path
        except (ValueError, OSError):
            return None

    def is_safe_filename(self, filename: str) -> bool:
        """Vérifie qu'un nom de fichier est sûr."""
        if not filename:
            return False

        # Pas de slash ni backslash
        if "/" in filename or "\\" in filename:
            return False

        # Pas de null bytes
        if "\x00" in filename:
            return False

        # Pas de fichiers cachés (commençant par .)
        if filename.startswith("."):
            return False

        # Extensions autorisées pour les uploads
        allowed_extensions = {".py", ".tex", ".txt", ".md", ".json", ".csv"}
        ext = os.path.splitext(filename)[1].lower()
        if ext and ext not in allowed_extensions:
            return False

        return True


class LatexValidator:
    """
    Validateur de code LaTeX pour prévenir les injections.
    """

    # Patterns dangereux à détecter
    DANGEROUS_PATTERNS = [
        r"\input\{",  # Inclusion de fichiers
        r"\include\{",  # Inclusion avec page break
        r"\ verbatim",  # Environment verbatim (peut être utilisé pour injecter)
        r"\ write",  # Écriture dans fichiers
        r"\immediate",  # Commandes immédiates
        r"\special\{",  # Commandes specials (danger)
        r"\走私",  # Injections UTF-8 suspectes
        r"\ documentclass.*\{.*\}",  # Multiple documentclass (suspicious)
    ]

    @classmethod
    def validate(cls, latex: str) -> tuple[bool, Optional[str]]:
        """
        Valide le code LaTeX.
        Returns: (is_safe, error_message)
        """
        if not latex or len(latex) > 500000:  # 500KB max
            return False, "Code LaTeX trop long ou vide"

        # Vérifier les patterns dangereux
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, latex, re.IGNORECASE):
                return False, f"Pattern potentiellement dangereux détecté: {pattern}"

        # Vérifier l'équilibre des accolades
        open_count = latex.count("{")
        close_count = latex.count("}")
        if open_count != close_count:
            return False, "Accolades déséquilibrées dans le code LaTeX"

        return True, None

    @classmethod
    def sanitize(cls, latex: str) -> str:
        """Nettoie le code LaTeX (supprime les commentaires)."""
        # Supprimer les lignes de commentaire
        lines = latex.split("\n")
        cleaned_lines = []

        for line in lines:
            # Detecteur de commentaires LaTeX (%)
            comment_pos = -1
            in_math = False

            for i, char in enumerate(line):
                if char == "$":
                    in_math = not in_math
                elif char == "%" and not in_math:
                    comment_pos = i
                    break

            if comment_pos >= 0:
                line = line[:comment_pos]

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)


def sanitize_shell_command(command: str) -> tuple[bool, Optional[str]]:
    """
    Valide une commande shell pour prévenir les injections.
    Returns: (is_safe, error_message)
    """
    # Liste blanche de caractères autorisés
    # Accepte: lettres, chiffres, espaces, -_./:=,[]{}
    if not re.match(r"^[a-zA-Z0-9 \t\-_./:=,\[\]{}|+@\n]+$", command):
        return False, "Caractères non autorisés dans la commande"

    # Vérifier les patterns d'injection courants
    dangerous = ["&&", "||", ";", "|", "`", "$(", ">", "<", "\n\n"]

    for pattern in dangerous:
        if pattern in command:
            # Exceptions pour certains patterns légitimes
            if pattern == "\n\n" and command.count("\n\n") == 1:
                continue
            return False, f"Pattern potentiellement dangereux: {pattern}"

    # Commande vide
    if not command.strip():
        return False, "Commande vide"

    # Longueur max
    if len(command) > 5000:
        return False, "Commande trop longue"

    return True, None
