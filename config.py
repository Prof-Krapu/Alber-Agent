"""
Configuration centralisée d'Albert IA Agentic.
Charge les variables d'environnement et fournit des valeurs par défaut.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Charger le .env si présent
load_dotenv()


@dataclass
class Config:
    # Sécurité
    ALBERT_API_KEY: str = ""
    BOT_ACCESS_TOKEN: str = "change-me-in-production"

    # Serveur
    HOST: str = "0.0.0.0"
    PORT: int = 8090
    DEBUG: bool = False

    # Workspace
    WORKSPACE_ROOT: str = "./workspace"
    OUTPUT_DIR: str = "./workspace/output"
    TOOLS_DIR: str = "./tools"
    SKILLS_DIR: str = "./skills"

    # Limites
    API_TIMEOUT: int = 120
    PYTHON_EXEC_TIMEOUT: int = 30
    PYTHON_MEMORY_LIMIT: int = 256
    RATE_LIMIT_REQUESTS: int = 30
    MAX_CHAT_HISTORY: int = 100

    # CORS
    ALLOWED_ORIGINS: str = "*"

    # API Albert
    ALBERT_BASE_URL: str = "https://albert.api.etalab.gouv.fr/v1"

    @property
    def api_key_set(self) -> bool:
        return bool(self.ALBERT_API_KEY and self.ALBERT_API_KEY != "")

    @property
    def token_set(self) -> bool:
        return self.BOT_ACCESS_TOKEN != "change-me-in-production"

    def get_workspace_path(self) -> Path:
        """Retourne le chemin absolu du workspace."""
        return Path(self.WORKSPACE_ROOT).resolve()

    def get_output_path(self) -> Path:
        """Retourne le chemin absolu du dossier output."""
        return Path(self.OUTPUT_DIR).resolve()

    def get_tools_path(self) -> Path:
        """Retourne le chemin absolu du dossier tools (skills dynamiques)."""
        return Path(self.TOOLS_DIR).resolve()

    def get_skills_path(self) -> Path:
        """Retourne le chemin absolu du dossier skills."""
        return Path(self.SKILLS_DIR).resolve()

    def get_allowed_origins(self) -> list:
        """Retourne la liste des origines CORS autorisées."""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


def get_config() -> Config:
    """Factory function pour récupérer la config depuis l'environnement."""
    return Config(
        ALBERT_API_KEY=os.environ.get("ALBERT_API_KEY", ""),
        BOT_ACCESS_TOKEN=os.environ.get("BOT_ACCESS_TOKEN", "change-me-in-production"),
        HOST=os.environ.get("HOST", "0.0.0.0"),
        PORT=int(os.environ.get("PORT", "8090")),
        DEBUG=os.environ.get("DEBUG", "false").lower() == "true",
        WORKSPACE_ROOT=os.environ.get("WORKSPACE_ROOT", "./workspace"),
        OUTPUT_DIR=os.environ.get("OUTPUT_DIR", "./workspace/output"),
        TOOLS_DIR=os.environ.get("TOOLS_DIR", "./tools"),
        SKILLS_DIR=os.environ.get("SKILLS_DIR", "./skills"),
        API_TIMEOUT=int(os.environ.get("API_TIMEOUT", "120")),
        PYTHON_EXEC_TIMEOUT=int(os.environ.get("PYTHON_EXEC_TIMEOUT", "30")),
        PYTHON_MEMORY_LIMIT=int(os.environ.get("PYTHON_MEMORY_LIMIT", "256")),
        RATE_LIMIT_REQUESTS=int(os.environ.get("RATE_LIMIT_REQUESTS", "30")),
        MAX_CHAT_HISTORY=int(os.environ.get("MAX_CHAT_HISTORY", "100")),
        ALLOWED_ORIGINS=os.environ.get("ALLOWED_ORIGINS", "*"),
        ALBERT_BASE_URL=os.environ.get(
            "ALBERT_BASE_URL", "https://albert.api.etalab.gouv.fr/v1"
        ),
    )


# Config singleton (chargée une seule fois au démarrage)
config = get_config()
