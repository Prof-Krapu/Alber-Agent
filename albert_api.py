"""
Albert IA Agentic - Backend FastAPI
Serveur moderne avec sécurité, validation et streaming.
"""

import os
import sys
import json
import asyncio
import subprocess
import tempfile
import re
import importlib.util
import inspect
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import deque
from functools import wraps
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    UploadFile,
    File,
    Form,
)
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import httpx

from config import config, get_config
from validators import (
    ChatRequest,
    FilePathValidator,
    LatexValidator,
    sanitize_shell_command,
)
from rate_limiter import get_rate_limiter, rate_limit, get_client_ip
from secure_executor import get_executor, SecurePythonExecutor
from tool_maker import ToolMakerEngine
from file_processor import (
    process_file,
    attachment_to_content_blocks,
    get_mime_type_from_ext,
    Attachment,
    MAX_FILE_SIZE,
    MAX_FILES,
)
import base64


# ==================== APP LIFESPAN ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application."""
    # Startup
    print("=" * 50)
    print("🤖 ALBERT IA AGENTIC - FastAPI Backend")
    print("=" * 50)
    print(f"Port: {config.PORT}")
    print(f"Workspace: {config.get_workspace_path()}")
    print(f"Modèles: {len(MODELS)}")
    print(f"API Key: {'✅ Configurée' if config.api_key_set else '❌ Manquante!'}")
    print(f"Token: {'✅ Configuré' if config.token_set else '⚠️ Par défaut!'}")
    print("=" * 50)

    # Safety: prevent accidental startup in production with default access token
    if not config.token_set and not config.DEBUG:
        raise RuntimeError(
            "BOT_ACCESS_TOKEN is using the default value. Set BOT_ACCESS_TOKEN in your environment or .env before starting the server in production."
        )

    # Initialisation du tool manager
    init_tool_manager()

    # Créer les répertoires
    config.get_workspace_path().mkdir(parents=True, exist_ok=True)
    config.get_output_path().mkdir(parents=True, exist_ok=True)
    config.get_tools_path().mkdir(parents=True, exist_ok=True)

    # Lancer une tâche de nettoyage périodique pour attachments_storage
    async def cleanup_attachments_task():
        from asyncio import sleep

        TTL_SECONDS = 3600  # 1 heure
        while True:
            try:
                now = datetime.utcnow()
                async with attachments_lock:
                    to_delete = []
                    for aid, att in list(attachments_storage.items()):
                        created = getattr(att, "created_at", None)
                        if created:
                            created_dt = datetime.fromisoformat(created)
                            if (now - created_dt).total_seconds() > TTL_SECONDS:
                                to_delete.append(aid)
                    for aid in to_delete:
                        del attachments_storage[aid]
                await sleep(60)
            except Exception:
                await sleep(60)

    # Lancer en tâche de fond (non bloquante)
    try:
        import asyncio

        asyncio.create_task(cleanup_attachments_task())
    except Exception:
        pass

    # Nettoyage périodique du rate limiter (éviter memory leak)
    async def cleanup_rate_limiter_task():
        from asyncio import sleep

        while True:
            try:
                limiter = get_rate_limiter()
                limiter.cleanup_inactive(max_age_seconds=3600)
                await sleep(300)  # Toutes les 5 minutes
            except Exception:
                await sleep(300)

    try:
        asyncio.create_task(cleanup_rate_limiter_task())
    except Exception:
        pass

    yield

    # Shutdown
    print("\n🛑 Arrêt d'Albert IA Agentic")

    # Background: cleanup attachments older than TTL


# ==================== FASTAPI APP ====================

app = FastAPI(
    title="Albert IA Agentic",
    description="Backend agentique avec capacités de tools et streaming",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if config.DEBUG else None,
    redoc_url="/redoc" if config.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== MODÈLES ====================

MODELS = {
    "mistralai/Ministral-3-8B-Instruct-2512": {
        "id": "mistralai/Ministral-3-8B-Instruct-2512",
        "name": "Ministral 3 8B",
        "description": "Rapide et efficace",
        "emoji": "⚡",
        "timeout": 30,
        "max_tokens": 4000,
    },
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506": {
        "id": "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
        "name": "Mistral Small 24B",
        "description": "Équilibre puissance/vitesse",
        "emoji": "⚖️",
        "timeout": 45,
        "max_tokens": 8000,
    },
    "openai/gpt-oss-120b": {
        "id": "openai/gpt-oss-120b",
        "name": "GPT-OSS-120B",
        "description": "Très puissant",
        "emoji": "🚀",
        "timeout": 120,
        "max_tokens": 16000,
    },
    "Qwen/Qwen3-Coder-30B-A3B-Instruct": {
        "id": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "name": "Qwen Coder 30B",
        "description": "Expert en code et outils",
        "emoji": "💻",
        "timeout": 60,
        "max_tokens": 8000,
    },
}


# ==================== PYDANTIC MODELS ====================


class ChatRequestIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    model: str = Field(default="mistralai/Mistral-Small-3.2-24B-Instruct-2506")
    attachments: List[str] = Field(
        default_factory=list, description="IDs des fichiers attachés"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Analyse ce document",
                    "model": "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
                    "attachments": ["uuid-123", "uuid-456"],
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    success: bool
    reply: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None
    iterations: Optional[int] = None


class UploadResponse(BaseModel):
    success: bool
    files: List[Dict[str, Any]]
    error: Optional[str] = None


class ToolInfo(BaseModel):
    id: str
    name: str
    description: str
    dangerous: bool = False


class StatusResponse(BaseModel):
    success: bool = True
    status: str = "online"
    port: int
    tools_count: int
    models_count: int
    timestamp: str


# ==================== ATTACHMENTS STORAGE ====================

# Stockage temporaire des fichiers uploadés (en mémoire)
# TTL: les fichiers sont supprimés après 1 heure
attachments_storage: Dict[str, Attachment] = {}
attachments_lock = asyncio.Lock()


# ==================== AUTHENTIFICATION ====================


async def verify_token(request: Request) -> bool:
    """Vérifie le token d'accès."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    api_key = request.headers.get("X-API-Key", "")

    provided = token or api_key
    if not provided or provided != config.BOT_ACCESS_TOKEN:
        raise HTTPException(
            status_code=401, detail="Unauthorized: Invalid or missing access token"
        )

    return True


async def require_auth(request: Request):
    """Dependency pour les routes protégées."""
    await verify_token(request)


# ==================== RATE LIMITING ====================


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware pour rate limiting global."""
    # Skip rate limiting for status/docs
    if request.url.path in ["/api/status", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    limiter = get_rate_limiter()
    ip = get_client_ip(request)
    allowed, retry_after = limiter.check(identifier=ip, request=request)

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": "Rate limit exceeded",
                "retry_after": int(retry_after) if retry_after else 60,
            },
        )

    response = await call_next(request)
    return response


# ==================== TOOL MANAGER ====================

tool_manager: Optional[ToolMakerEngine] = None


def init_tool_manager():
    """Initialise le gestionnaire d'outils."""
    global tool_manager
    tool_manager = ToolMakerEngine(skills_dir=str(config.get_tools_path()))
    # IMPORTANT: legacy tools d'abord, puis discover_skills
    # Cela garantit que les outils sécurisés (legacy) ne sont pas écrasés
    # par des versions non-sécurisées sur disque
    register_legacy_tools(tool_manager)
    tool_manager.discover_skills()
    print(f"DEBUG: Outils chargés: {list(tool_manager.tools.keys())}")


def register_legacy_tools(engine: ToolMakerEngine):
    """Enregistre les outils legacy (sécurisés)."""

    def execute_command(command: str) -> str:
        """Exécute une commande shell (CLI) de manière sécurisée."""
        safe, error = sanitize_shell_command(command)
        if not safe:
            return f"Erreur: {error}"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(config.get_workspace_path()),
                timeout=30,
            )
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Erreur: Commande dépassée (timeout 30s)"
        except Exception as e:
            return f"Erreur: {str(e)}"

    def execute_python(code: str) -> str:
        """Exécute du code Python de manière sécurisée."""
        executor = get_executor()
        stdout, error = executor.execute(code)
        if error:
            return f"Erreur: {error}"
        return stdout or "Exécution terminée sans sortie."

    def list_files(directory: str = ".") -> str:
        """Liste les fichiers dans un répertoire."""
        validator = FilePathValidator(str(config.get_workspace_path()))
        target = validator.validate(directory)
        if not target:
            return "Accès refusé: Répertoire hors workspace"

        try:
            files = []
            for item in Path(target).iterdir():
                size = item.stat().st_size if item.is_file() else 0
                files.append(
                    {
                        "name": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": size,
                    }
                )
            return json.dumps(files, ensure_ascii=False)
        except Exception as e:
            return str(e)

    def read_file(filename: str) -> str:
        """Lit le contenu d'un fichier texte."""
        validator = FilePathValidator(str(config.get_workspace_path()))
        target = validator.validate(filename)
        if not target:
            return "Accès refusé"
        try:
            return target.read_text(encoding="utf-8")
        except Exception as e:
            return str(e)

    def write_file(filename: str, content: str) -> str:
        """Écrit du contenu dans un fichier."""
        validator = FilePathValidator(str(config.get_workspace_path()))
        target = validator.validate(filename)
        if not target:
            return "Accès refusé"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"Fichier {filename} écrit avec succès."
        except Exception as e:
            return str(e)

    def compile_latex(latex_source: str) -> str:
        """Compile un document LaTeX en PDF."""
        safe, error = LatexValidator.validate(latex_source)
        if not safe:
            return f"Erreur: {error}"

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"document_{timestamp}"
            output_dir = config.get_output_path()

            is_full_doc = "\\documentclass" in latex_source

            if is_full_doc:
                packages = [
                    (
                        r"\\usepackage\{tikz\}",
                        r"\\usepackage{tikz}\n\\usetikzlibrary{babel}",
                    ),
                    (
                        r"\\usepackage\{circuitikz\}",
                        r"\\usepackage[siunitx,european,cuteappendices]{circuitikz}",
                    ),
                ]
                full_latex = latex_source
                for pattern, pkg in packages:
                    if not re.search(pattern, full_latex):
                        full_latex = re.sub(
                            r"(\\documentclass[^{]*\{[^}]*\})",
                            f"\\1\n{pkg}",
                            full_latex,
                            count=1,
                        )
            else:
                full_latex = (
                    "\\documentclass[12pt,a4paper]{article}\n"
                    "\\usepackage[utf8]{inputenc}\n"
                    "\\usepackage[french]{babel}\n"
                    "\\usepackage{amsmath,amssymb,geometry}\n"
                    "\\usepackage{tikz}\n"
                    "\\usetikzlibrary{babel}\n"
                    "\\usepackage[siunitx,european,cuteappendices]{circuitikz}\n"
                    "\\begin{document}\n"
                    f"{latex_source}\n"
                    "\\end{document}"
                )

            tex_dest = output_dir / f"{base_name}.tex"
            tex_dest.write_text(full_latex, encoding="utf-8")

            with tempfile.TemporaryDirectory() as tmpdir:
                tex_file = Path(tmpdir) / "temp.tex"
                tex_file.write_text(full_latex, encoding="utf-8")

                for _ in range(2):
                    subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", "temp.tex"],
                        cwd=tmpdir,
                        capture_output=True,
                    )

                pdf_path = Path(tmpdir) / "temp.pdf"
                if pdf_path.exists():
                    import shutil

                    pdf_dest = output_dir / f"{base_name}.pdf"
                    shutil.copy(pdf_path, pdf_dest)
                    return (
                        f"Succès ! Fichiers générés: {base_name}.pdf et {base_name}.tex"
                    )

                log_file = Path(tmpdir) / "temp.log"
                if log_file.exists():
                    logs = log_file.read_text(errors="ignore")[-1000:]
                    return f"Échec compilation. Logs:\n{logs}"

                return "Échec compilation: fichier log introuvable"
        except Exception as e:
            return f"Erreur critique: {str(e)}"

    def effacer_fichiers(pattern: str) -> str:
        """Supprime des fichiers correspondant à un motif."""
        try:
            import glob

            workspace = config.get_workspace_path()
            files = glob.glob(str(workspace / pattern))
            count = 0
            for f in files:
                fpath = Path(f)
                if fpath.is_file() and str(fpath).startswith(str(workspace)):
                    fpath.unlink()
                    count += 1
            if "tools/" in pattern or "skills/" in pattern:
                tool_manager.discover_skills()
            return f"{count} fichiers supprimés."
        except Exception as e:
            return str(e)

    def fetch_url(url: str) -> str:
        """Récupère le contenu d'une URL."""
        if not url.startswith(("http://", "https://")):
            return "Erreur: URL invalide (doit commencer par http:// ou https://)"
        try:
            response = httpx.get(url, timeout=10, follow_redirects=True)
            return response.text[:5000]
        except Exception as e:
            return f"Erreur: {str(e)}"

    # Enregistrement
    engine.register_tool(execute_command, internal=True)
    engine.register_tool(execute_python, internal=True)
    engine.register_tool(list_files, internal=True)
    engine.register_tool(read_file, internal=True)
    engine.register_tool(write_file, internal=True)
    engine.register_tool(compile_latex, internal=True)
    engine.register_tool(effacer_fichiers, internal=True)
    engine.register_tool(fetch_url, internal=True)


# ==================== HISTORIQUE DE CHAT ====================


class ChatHistory:
    """Gestionnaire d'historique de chat avec limite."""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.sessions: Dict[str, deque] = {}

    def get_session(self, session_id: str = "default") -> deque:
        if session_id not in self.sessions:
            self.sessions[session_id] = deque(maxlen=self.max_size)
        return self.sessions[session_id]

    def add(self, role: str, content: str, session_id: str = "default"):
        history = self.get_session(session_id)
        history.append({"role": role, "content": content})

    def get_history(self, session_id: str = "default") -> List[Dict]:
        return list(self.get_session(session_id))

    def clear(self, session_id: str = "default"):
        if session_id in self.sessions:
            self.sessions[session_id].clear()


chat_history = ChatHistory(max_size=config.MAX_CHAT_HISTORY)

SYSTEM_PROMPT = r"""Tu es Albert IA Agentic, un assistant conversationnel expert. Tu dois TOUJOURS répondre en Markdown clair et rédigé (langage naturel), JAMAIS sous forme de bloc JSON brut.

# GESTION DES DOCUMENTS ET ARCHIVES (CRITIQUE)
1. **AUCUNE ÉCRITURE À LA RACINE** : Il est strictement interdit de créer ou d'écrire des fichiers directement à la racine du projet.
2. **DOSSIER OUTPUT** : Tous les fichiers persistants doivent être créés exclusivement dans le dossier `output/`.
3. **COMPILATION LATEX** : Utilise l'outil `compile_latex`. Les packages `circuitikz` (style européen forcé), `mhchem`, `chemfig` et `pgfplots` sont supportés.
4. **SCIENCES (IMPORTANT)** :
   - **Électricité** : Utilise TOUJOURS `circuitikz` en style EUROPEAN (résistances rectangulaires).
   - **Chimie** : Utilise `\ce{...}` (mhchem) et `\chemfig{...}`.
   - **Graphiques** : Utilise `pgfplots` (axis).
5. **AUTO-CORRECTION** : Si la compilation échoue, lis les logs renvoyés et corrige-toi.

# RÈGLE DE FORMATAGE LATEX CRITIQUE
1. **Délimiteurs** : TOUT symbole mathématique doit être encadré par des dollars `$`.
2. **Syntaxe Standard** : Utilise un SEUL antislash (ex: `\nabla`, `\alpha`).
3. **Équations isolées** : Utilise `$$...$$` pour les blocs d'équations centrés.
"""


# ==================== API ENDPOINTS ====================


@app.get("/", response_class=HTMLResponse)
async def root():
    """Sert l'interface web."""
    html_path = Path(__file__).parent / "albert_agentic_ui.html"
    if html_path.exists():
        return html_path.read_text()
    return "<h1>Albert IA Agentic</h1><p>Interface non trouvée</p>"


# ==================== FILE UPLOAD ENDPOINTS ====================


@app.post("/api/upload", response_model=UploadResponse)
async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    """
    Upload plusieurs fichiers (images, PDF, DOCX, XLSX, TXT).
    Retourne la liste des fichiers traités avec leur contenu.
    """
    await require_auth(request)

    if len(files) > MAX_FILES:
        return UploadResponse(
            success=False, files=[], error=f"Trop de fichiers (max: {MAX_FILES})"
        )

    processed_files = []
    errors = []

    for file in files:
        try:
            # Lire le contenu
            content = await file.read()

            # Vérifier la taille
            if len(content) > MAX_FILE_SIZE:
                errors.append(f"{file.filename}: Fichier trop grand (max 10MB)")
                continue

            # Déterminer le MIME type
            mime_type = file.content_type or get_mime_type_from_ext(file.filename)

            # Traiter le fichier
            attachment = process_file(content, file.filename, mime_type)

            if attachment is None:
                errors.append(f"{file.filename}: Type de fichier non supporté")
                continue

            # Stocker temporairement (metadata only) and schedule cleanup via created timestamp
            attachment_meta = attachment
            attachment_meta.created_at = datetime.utcnow().isoformat()
            async with attachments_lock:
                attachments_storage[attachment.id] = attachment_meta

            # Préparer la réponse
            file_info = {
                "id": attachment.id,
                "name": attachment.name,
                "type": attachment.file_type.value,
                "size": attachment.size,
                "has_preview": bool(attachment.content),
                "has_text": bool(attachment.text_content),
                "pages_count": len(attachment.pages) if attachment.pages else 0,
            }
            processed_files.append(file_info)

        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    error_msg = "; ".join(errors) if errors else None

    return UploadResponse(
        success=len(processed_files) > 0, files=processed_files, error=error_msg
    )


@app.post("/api/upload/base64")
async def upload_base64(request: Request, body: dict):
    """
    Upload un fichier encodé en base64.
    Utile pour les preview d'images côté frontend.
    """
    await require_auth(request)

    data = body.get("data", "")
    name = body.get("name", "upload")
    mime_type = body.get("mime_type", "")

    try:
        # Decoder base64
        content = base64.b64decode(data)

        if len(content) > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Fichier trop grand"},
            )

        # Traiter le fichier
        attachment = process_file(content, name, mime_type)

        if attachment is None:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Type non supporté"},
            )

        # Stocker
        async with attachments_lock:
            attachments_storage[attachment.id] = attachment

        return {
            "success": True,
            "file": {
                "id": attachment.id,
                "name": attachment.name,
                "type": attachment.file_type.value,
                "size": attachment.size,
            },
        }

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.delete("/api/attachments/{attachment_id}")
async def delete_attachment(request: Request, attachment_id: str):
    """Supprime un fichier uploadé."""
    await require_auth(request)

    async with attachments_lock:
        if attachment_id in attachments_storage:
            del attachments_storage[attachment_id]
            return {"success": True, "message": "Fichier supprimé"}

    return JSONResponse(
        status_code=404, content={"success": False, "error": "Fichier introuvable"}
    )


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Retourne le statut du serveur."""
    # Pour éviter fuite d'informations, exposer une version réduite publique.
    # Cette route reste publique mais retourne moins d'informations sensibles.
    return StatusResponse(
        success=True,
        status="online",
        port=config.PORT if config.DEBUG else 0,
        tools_count=len(tool_manager.tools) if (tool_manager and config.DEBUG) else 0,
        models_count=len(MODELS) if config.DEBUG else 0,
        timestamp=datetime.now().isoformat(),
    )


@app.get("/api/models")
async def get_models(request: Request):
    """Liste des modèles disponibles."""
    await require_auth(request)
    return {"success": True, "models": list(MODELS.values())}


@app.get("/api/tools")
async def get_tools(request: Request):
    """Liste des outils disponibles."""
    await require_auth(request)

    # Recharger les tools depuis le disque (pour les nouveaux skills)
    if tool_manager:
        tool_manager.discover_skills()

    tools_list = []
    if tool_manager:
        for tool_id, tool_info in tool_manager.tools.items():
            desc = inspect.getdoc(tool_info) or "Outil agentique"
            tools_list.append(
                {
                    "id": tool_id,
                    "name": tool_id,
                    "description": desc,
                    "dangerous": False,
                }
            )

    return {"success": True, "tools": tools_list}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequestIn):
    """Endpoint principal de chat avec boucle agentique et support multimodal."""
    await require_auth(request)

    # Validation du modèle
    if body.model not in MODELS:
        return ChatResponse(success=False, error=f"Modèle inconnu: {body.model}")

    model_config = MODELS[body.model]
    session_id = request.headers.get("X-Session-ID", "default")

    # Charger les attachments si présents
    content_blocks = []
    attachment_descriptions = []

    if body.attachments:
        async with attachments_lock:
            for att_id in body.attachments[:MAX_FILES]:
                if att_id in attachments_storage:
                    att = attachments_storage[att_id]
                    blocks = attachment_to_content_blocks(att)
                    content_blocks.extend(blocks)

                    # Description pour l'historique
                    if att.text_content:
                        attachment_descriptions.append(
                            f"[Document: {att.name}]\n{att.text_content[:500]}"
                        )
                    else:
                        attachment_descriptions.append(f"[Image: {att.name}]")

    # Construire le message avec les attachments
    if content_blocks:
        # Format multimodal avec content blocks
        user_message = {"role": "user", "content": []}
        user_message["content"].append({"type": "text", "text": body.message})
        user_message["content"].extend(content_blocks)
    else:
        # Format texte simple
        full_message = body.message
        if attachment_descriptions:
            full_message += "\n\n---Fichiers analysés:---\n" + "\n\n".join(
                attachment_descriptions
            )
        user_message = {"role": "user", "content": full_message}

    # Construction du payload
    is_mistral = "mistral" in body.model.lower()
    filtered_messages = []

    for m in chat_history.get_history(session_id):
        role = m.get("role")
        content = m.get("content")
        if role in ["system", "user", "assistant"] and content:
            filtered_messages.append({"role": role, "content": str(content).strip()})

    # Ajouter le system prompt si vide
    if not any(m.get("role") == "system" for m in filtered_messages):
        filtered_messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    # Ajouter le message utilisateur (multimodal ou texte)
    filtered_messages.append(user_message)

    headers = {
        "Authorization": f"Bearer {config.ALBERT_API_KEY}",
        "Content-Type": "application/json",
    }

    max_iterations = 5
    iterations = 0
    final_reply = ""

    async with httpx.AsyncClient(timeout=model_config["timeout"]) as client:
        while iterations < max_iterations:
            iterations += 1

            # Payload unifié : tous les modèles reçoivent les outils
            payload = {
                "model": body.model,
                "messages": filtered_messages,
                "max_tokens": model_config["max_tokens"],
                "temperature": 0.7,
                "tools": tool_manager.get_albert_tools_schema()
                if tool_manager
                else [],
            }

            try:
                response = await client.post(
                    f"{config.ALBERT_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            except httpx.TimeoutException:
                return ChatResponse(
                    success=False, error=f"Timeout API ({model_config['timeout']}s)"
                )
            except Exception as e:
                return ChatResponse(success=False, error=f"Erreur API: {str(e)}")

            message_obj = data["choices"][0]["message"]
            reply = message_obj.get("content") or ""

            # Détection des outils (natifs ou regex fallback)
            native_tool_calls = []
            regex_matches = []
            used_native = False

            if "tool_calls" in message_obj and message_obj["tool_calls"]:
                used_native = True
                # Ajouter le message assistant complet (avec tool_calls)
                filtered_messages.append(message_obj)
                if reply:
                    chat_history.add("assistant", reply, session_id)
                for tc in message_obj["tool_calls"]:
                    if tc.get("type") == "function":
                        native_tool_calls.append(
                            (tc["id"], tc["function"]["name"], tc["function"]["arguments"])
                        )
            else:
                # Pas de tool_calls natifs : ajouter la réponse texte
                if reply:
                    filtered_messages.append({"role": "assistant", "content": reply})
                    chat_history.add("assistant", reply, session_id)
                # Regex fallback pour les modèles qui ne supportent pas tool_calls
                tool_pattern = r"\[TOOL_CALLS\]([a-zA-Z0-9_]+)(\{.*?\})"
                for m in re.finditer(tool_pattern, reply, re.DOTALL):
                    regex_matches.append((m.group(1), m.group(2)))

            if not native_tool_calls and not regex_matches:
                final_reply = reply
                break

            # Exécution des outils (natifs)
            for tc_id, tool_name, json_args in native_tool_calls:
                if not tool_manager or tool_name not in tool_manager.tools:
                    obs = f"Outil '{tool_name}' introuvable"
                else:
                    try:
                        kwargs = (
                            json.loads(json_args)
                            if isinstance(json_args, str)
                            else json_args
                        )
                    except:
                        kwargs = {}
                    obs = tool_manager.execute_tool(tool_name, kwargs)

                # Rôle "tool" avec tool_call_id (format OpenAI/Mistral)
                filtered_messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "name": tool_name,
                    "content": str(obs),
                })

            # Exécution des outils (regex fallback — rôle user)
            for tool_name, json_args in regex_matches:
                if not tool_manager or tool_name not in tool_manager.tools:
                    obs = f"Outil '{tool_name}' introuvable"
                else:
                    try:
                        kwargs = (
                            json.loads(json_args)
                            if isinstance(json_args, str)
                            else json_args
                        )
                    except:
                        kwargs = {}
                    obs = tool_manager.execute_tool(tool_name, kwargs)

                tool_msg = f"OBSERVATION DE L'OUTIL '{tool_name}':\n{obs}"
                filtered_messages.append({"role": "user", "content": tool_msg})
                chat_history.add("user", tool_msg, session_id)

    if not final_reply:
        final_reply = "Erreur: Limite d'itérations atteinte."

    return ChatResponse(
        success=True, reply=final_reply, model=body.model, iterations=iterations
    )


@app.post("/api/chat/stream")
async def chat_stream(request: Request, body: ChatRequestIn):
    """Endpoint streaming pour le chat (SSE)."""
    await require_auth(request)

    async def event_generator():
        session_id = request.headers.get("X-Session-ID", "default")
        chat_history.add("user", body.message, session_id)

        yield f"data: {json.dumps({'type': 'start', 'model': body.model})}\n\n"

        # Logique simplifiée - streaming réel nécessite plus de config
        yield f"data: {json.dumps({'type': 'progress', 'content': 'Analyse en cours...'})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'content': 'Utilisez /api/chat pour les réponses complètes'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/api/history/clear")
async def clear_history(request: Request, session_id: str = "default"):
    """Efface l'historique de chat."""
    await require_auth(request)
    chat_history.clear(session_id)
    return {"success": True, "message": "Historique effacé"}


@app.get("/api/files")
async def list_files(request: Request, directory: str = "."):
    """Liste les fichiers dans le workspace."""
    await require_auth(request)
    validator = FilePathValidator(str(config.get_workspace_path()))
    target = validator.validate(directory)

    if not target:
        raise HTTPException(status_code=403, detail="Accès refusé")

    try:
        files = []
        for item in Path(target).iterdir():
            files.append(
                {
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(
                        item.stat().st_mtime
                    ).isoformat(),
                }
            )
        return {"success": True, "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WEBSOCKET ====================


class ConnectionManager:
    """Gestionnaire de connexions WebSocket."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour communication temps réel."""
    client_id = websocket.headers.get("X-Client-ID", str(id(websocket)))
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "chat":
                response = await process_chat(message_data)
                await manager.send_message(json.dumps(response), client_id)

            elif message_data.get("type") == "ping":
                await manager.send_message(json.dumps({"type": "pong"}), client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        await manager.send_message(
            json.dumps({"type": "error", "message": str(e)}), client_id
        )


async def process_chat(data: dict) -> dict:
    """Traitement asynchrone du chat via WebSocket."""
    message = data.get("message", "")
    model = data.get("model", "mistralai/Mistral-Small-3.2-24B-Instruct-2506")

    # Logique simplifiée
    return {"type": "response", "content": f"Echo: {message}", "model": model}


# ==================== LANCEMENT ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "albert_api:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info",
    )
