#!/usr/bin/env python3
"""
Albert IA Agentic - Serveur final simplifié
Backend + Frontend unifié
"""

import os
import sys
import json
import subprocess
import tempfile
import requests
import re
import importlib.util
import inspect
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from functools import wraps

# ==================== CONFIGURATION ====================
API_KEY = os.environ.get("ALBERT_API_KEY", "REDACTED_API_KEY")
BOT_ACCESS_TOKEN = os.environ.get("BOT_ACCESS_TOKEN", "default-secure-token-12345")
BASE_URL = "https://albert.api.etalab.gouv.fr/v1"
PORT = 8090

# Utiliser le répertoire courant du script comme racine du projet pour la portabilité
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
# Si on est dans le dossier du projet, la racine est le dossier courant
WORKSPACE_ROOT = CURRENT_DIR
TOOLS_DIR = os.path.join(WORKSPACE_ROOT, "tools")

# Créer les répertoires
os.makedirs(WORKSPACE_ROOT, exist_ok=True)
os.makedirs(TOOLS_DIR, exist_ok=True)

# Modèles disponibles
MODELS = {
    "mistralai/Ministral-3-8B-Instruct-2512": {
        "name": "Ministral 3 8B",
        "description": "Rapide et efficace",
        "emoji": "⚡",
        "timeout": 30,
        "max_tokens": 4000
    },
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506": {
        "name": "Mistral Small 24B",
        "description": "Équilibre puissance/vitesse",
        "emoji": "⚖️",
        "timeout": 45,
        "max_tokens": 8000
    },
    "openai/gpt-oss-120b": {
        "name": "GPT-OSS-120B",
        "description": "Très puissant",
        "emoji": "🚀",
        "timeout": 120,
        "max_tokens": 16000
    },
    "Qwen/Qwen3-Coder-30B-A3B-Instruct": {
        "name": "Qwen Coder 30B",
        "description": "Expert en code et outils",
        "emoji": "💻",
        "timeout": 60,
        "max_tokens": 8000
    }
}

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization') or request.headers.get('X-API-Key')
        if not token or token.replace('Bearer ', '') != BOT_ACCESS_TOKEN:
            return jsonify({'success': False, 'error': 'Unauthorized: Invalid or missing access token'}), 401
        return f(*args, **kwargs)
    return decorated

# REMPLACÉ: Ancien ToolManager retiré au profit du robuste ToolMakerEngine
from tool_maker import ToolMakerEngine
tool_manager = ToolMakerEngine(skills_dir=TOOLS_DIR)

# Migration des vieux "Outils Systèmes" dans le nouveau moteur
def register_legacy_tools(engine: ToolMakerEngine):
    class LegacyWrapper:
        def __init__(self):
            self.workspace = WORKSPACE_ROOT
        
        def execute_command(self, command: str) -> str:
            """Exécute une commande shell sur le système (CLI)."""
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True,
                    cwd=self.workspace, timeout=30
                )
                return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            except Exception as e:
                return f"Erreur: {str(e)}"

        def list_files(self, directory: str = ".") -> str:
            """Liste les fichiers dans un répertoire"""
            try:
                if ".." in directory: return "Accès refusé"
                target = (Path(self.workspace) / directory).resolve()
                if not target.exists(): return "Répertoire introuvable"
                files = []
                for item in target.iterdir():
                    size = item.stat().st_size if item.is_file() else 0
                    files.append({"name": item.name, "type": "dir" if item.is_dir() else "file", "size": size})
                return json.dumps(files, ensure_ascii=False)
            except Exception as e: return str(e)
            
        def read_file(self, filename: str) -> str:
            """Lit le contenu d'un fichier texte"""
            target = (Path(self.workspace) / filename).resolve()
            if not str(target).startswith(str(self.workspace)): return "Accès refusé"
            try: return target.read_text(encoding="utf-8")
            except Exception as e: return str(e)

        def write_file(self, filename: str, content: str) -> str:
            """Écrit du contenu dans un fichier"""
            target = (Path(self.workspace) / filename).resolve()
            if not str(target).startswith(str(self.workspace)): return "Accès refusé"
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                return f"Fichier {filename} écrit avec succès."
            except Exception as e: return str(e)
            
        def execute_python(self, code: str) -> str:
            """Exécute du code Python et retourne le résultat."""
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            redirected_output = sys.stdout = StringIO()
            try:
                exec(code)
                sys.stdout = old_stdout
                return redirected_output.getvalue()
            except Exception as e:
                sys.stdout = old_stdout
                return str(e)

        def compile_latex(self, latex_source: str) -> str:
            """Compile un document LaTeX (complet ou fragment) en PDF et archive la source."""
            try:
                import subprocess, tempfile, os
                from pathlib import Path
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                base_name = f"document_{timestamp}"
                
                output_dir = os.path.join(self.workspace, "output")
                os.makedirs(output_dir, exist_ok=True)
                
                # Détection : document complet ou fragment ?
                is_full_doc = "\\documentclass" in latex_source
                
                if is_full_doc:
                    # Injection automatique des packages scientifiques s'ils manquent
                    packages = [
                        (r"\\usepackage\{tikz\}", r"\\usepackage{tikz}\n\\usetikzlibrary{babel}"),
                        (r"\\usepackage\{circuitikz\}", r"\\usepackage[siunitx,european,cuteappendices]{circuitikz}"),
                        (r"\\usepackage\{mhchem\}", r"\\usepackage[version=4]{mhchem}"),
                        (r"\\usepackage\{chemfig\}", r"\\usepackage{chemfig}"),
                        (r"\\usepackage\{pgfplots\}", r"\\usepackage{pgfplots}\n\\pgfplotsset{compat=1.18}")
                    ]
                    
                    full_latex = latex_source
                    for pattern, pkg in packages:
                        if not re.search(pattern, full_latex):
                            # Insérer juste après \documentclass
                            full_latex = re.sub(r"(\\documentclass[^{]*\{[^}]*\})", f"\\1\n{pkg}", full_latex, count=1)
                        elif "circuitikz" in pattern:
                            # Forcer l'option european même si circuitikz est déjà présent
                            full_latex = re.sub(r"\\usepackage(\[[^\]]*\])?\{circuitikz\}", r"\\usepackage[siunitx,european,cuteappendices]{circuitikz}", full_latex)
                else:
                    # Wrapper standard avec support circuitikz et physique
                    full_latex = (
                        "\\documentclass[12pt,a4paper]{article}\n"
                        "\\usepackage[utf8]{inputenc}\n"
                        "\\usepackage[french]{babel}\n"
                        "\\usepackage{amsmath,amssymb,geometry}\n"
                        "\\usepackage{tikz}\n"
                        "\\usetikzlibrary{babel}\n"
                        "\\usepackage[siunitx,european,cuteappendices]{circuitikz}\n"
                        "\\usepackage[version=4]{mhchem}\n"
                        "\\usepackage{chemfig}\n"
                        "\\usepackage{pgfplots}\n"
                        "\\pgfplotsset{compat=1.18}\n"
                        "\\usepackage{tikz}\n"
                        "\\begin{document}\n"
                        f"{latex_source}\n"
                        "\\end{document}"
                    )
                
                # Sauvegarde de la source .tex
                tex_dest = os.path.join(output_dir, f"{base_name}.tex")
                Path(tex_dest).write_text(full_latex, encoding="utf-8")
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    tex_file = os.path.join(tmpdir, "temp.tex")
                    Path(tex_file).write_text(full_latex, encoding="utf-8")
                    
                    # Double compilation pour les références et tables
                    for _ in range(2):
                        subprocess.run(["pdflatex", "-interaction=nonstopmode", "temp.tex"], cwd=tmpdir, capture_output=True)
                    
                    pdf_path = os.path.join(tmpdir, "temp.pdf")
                    if os.path.exists(pdf_path):
                        pdf_dest = os.path.join(output_dir, f"{base_name}.pdf")
                        import shutil
                        shutil.copy(pdf_path, pdf_dest)
                        return f"Succès ! Fichiers générés : {base_name}.pdf et {base_name}.tex. Note : circuitikz, mhchem, chemfig et pgfplots sont supportés."
                    
                    # En cas d'échec, on renvoie une partie des logs LaTeX pour aider l'IA à corriger
                    log_file = os.path.join(tmpdir, "temp.log")
                    logs = ""
                    if os.path.exists(log_file):
                        logs = Path(log_file).read_text(errors='ignore')[-1000:]
                    return f"Échec compilation. Logs récents :\n{logs}\nLa source est archivée dans {base_name}.tex."
            except Exception as e: return f"Erreur critique LaTeX : {str(e)}"

        def fetch_url(self, url: str) -> str:
            """Récupère le contenu d'une URL"""
            try:
                return requests.get(url, timeout=10).text[:5000]
            except Exception as e: return str(e)

        def effacer_fichiers(self, pattern: str) -> str:
            """
            Supprime des fichiers correspondant à un motif (glob). 
            ATTENTION: Ne supprime que dans le workspace.
            """
            try:
                import glob
                files = glob.glob(os.path.join(self.workspace, pattern))
                count = 0
                for f in files:
                    if os.path.isfile(f) and str(f).startswith(str(self.workspace)):
                        os.remove(f)
                        count += 1
                # Si on supprime un tool, on force le reload
                if "tools/" in pattern or "skills/" in pattern:
                    tool_manager.discover_skills()
                return f"{count} fichiers supprimés."
            except Exception as e: return str(e)

    legacy = LegacyWrapper()
    engine.register_tool(legacy.execute_command, internal=True)
    engine.register_tool(legacy.list_files, internal=True)
    engine.register_tool(legacy.read_file, internal=True)
    engine.register_tool(legacy.write_file, internal=True)
    engine.register_tool(legacy.compile_latex, internal=True)
    engine.register_tool(legacy.execute_python, internal=True)
    engine.register_tool(legacy.fetch_url, internal=True)
    engine.register_tool(legacy.effacer_fichiers, internal=True)

register_legacy_tools(tool_manager)
print(f"DEBUG: Discovery Result: {tool_manager.discover_skills()}")
print(f"DEBUG: Final Tool IDs: {list(tool_manager.tools.keys())}")


# ==================== GESTION DE MÉMOIRE (SIMPLIFIÉE) ====================
global_chat_history = [
    {
        "role": "system", 
        "content": (
            "Tu es Albert IA Agentic, un assistant conversationnel expert. Tu dois TOUJOURS répondre en Markdown clair et rédigé (langage naturel), JAMAIS sous forme de bloc JSON brut.\n\n"
            "# GESTION DES DOCUMENTS ET ARCHIVES (CRITIQUE)\n"
            "1. **AUCUNE ÉCRITURE À LA RACINE** : Il est strictement interdit de créer ou d'écrire des fichiers directement à la racine du projet.\n"
            "2. **DOSSIER OUTPUT** : Tous les fichiers persistants doivent être créés exclusivement dans le dossier `output/`.\n"
            "3. **COMPILATION LATEX** : Utilise l'outil `compile_latex`. Les packages `circuitikz` (style européen forcé), `mhchem`, `chemfig` et `pgfplots` sont injectés automatiquement.\n"
            "4. **SCIENCES (IMPORTANT)** :\n"
            "   - **Électricité** : Utilise TOUALWAYS `circuitikz` en style EUROPEAN (résistances rectangulaires). Ne dessine JAMAIS de circuits avec de simples lignes TikZ `--`. Exemple : `\\begin{circuitikz} \\draw (0,0) to[R=$R$] (2,0) to[C=$C$] (2,-2) -- (0,-2) -- (0,0); \\end{circuitikz}`. Si tu utilises `babel[french]`, n'oublie pas `\\usetikzlibrary{babel}` si tu fournis un document complet.\n"
            "   - **Chimie** : Utilise `\\ce{...}` (mhchem) et `\\chemfig{...}`.\n"
            "   - **Graphiques** : Utilise `pgfplots` (axis).\n"
            "5. **AUTO-CORRECTION** : Si la compilation échoue, lis les logs renvoyés, analyse ton `.tex` archivé et corrige-toi.\n\n"
            "# RÈGLE DE FORMATAGE LATEX CRITIQUE\n"
            "Tu génères du contenu scientifique. Pour que l'interface puisse rendre les symboles, tu dois IMPÉRATIVEMENT :\n"
            "1. **Toujours utiliser des délimiteurs :** TOUT symbole mathématique, même une seule lettre grecque (ex: \\mu_0), doit être encadré par des dollars `$`. \n"
            "   - *Incorrect* : La perméabilité \\mu_0 est...\n"
            "   - *Correct* : La perméabilité $\\mu_0$ est...\n"
            "2. **Syntaxe Standard :** Utilise un SEUL antislash (ex: \\\\nabla, \\\\alpha, \\\\frac{1}{2}). Ne double JAMAIS les antislashs.\n"
            "3. **Équations isolées :** Utilise `$$...$$` pour les blocs d'équations centrés."
        )
    }
]

# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """Page d'accueil"""
    return send_from_directory('.', 'albert-agentic-complete.html')

@app.route('/api/models')
@require_auth
def get_models():
    """Liste des modèles"""
    return jsonify({'success': True, 'models': MODELS})

@app.route('/api/tools')
@require_auth
def get_tools():
    """Liste des outils (Actualisé en temps réel)"""
    tool_manager.discover_skills() # Forcer le scan du dossier
    tools_list = []
    for tool_id, tool_info in tool_manager.tools.items():
        tools_list.append({
            "id": tool_id,
            "name": tool_id,
            "description": inspect.getdoc(tool_info) or "Outil agentique",
            "dangerous": False
        })
    return jsonify({'success': True, 'tools': tools_list})

import re

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    """Endpoint de chat (BOUCLE AGENTIQUE AUTOMATISÉE)"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        model = data.get('model', 'mistralai/Ministral-3-8B-Instruct-2512')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message vide'})
        
        if model not in MODELS:
            return jsonify({'success': False, 'error': f'Modèle inconnu: {model}'})
            
        # Garder une compatibilité descendante : si l'utilisateur insiste sur "/tool", on l'encapsule dans du langage naturel
        if message.startswith('/tool '):
            message = f"Exécute manuellement ton outil: {message[6:]}"
            
        # 1. Ajout de la question à l'historique
        global_chat_history.append({"role": "user", "content": message})
        
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
            # 2. La boucle d'autonomie (Max 5 itérations d'outils par tour pour éviter boucle infinie)
        max_iterations = 5
        iterations = 0
        final_reply = ""
        
        while iterations < max_iterations:
            iterations += 1
            
            # Détermination si le modèle supporte les outils (Agentic)
            # Mistral est configuré en "chat only" (pas de paramètre 'tools')
            is_mistral = "mistral" in model.lower()
            
            # Construction du payload avec filtrage spécifique selon le modèle
            if is_mistral:
                # 1. Filtrage DEEP de l'historique pour Mistral (très sensible aux rôles et contenus null)
                filtered_messages = []
                for m in global_chat_history:
                    role = m.get('role')
                    content = m.get('content')
                    
                    if role not in ['system', 'user', 'assistant']:
                        continue
                        
                    # On ignore les messages sans contenu textuel (ex: appels d'outils seuls)
                    if content is None or (isinstance(content, str) and not content.strip()):
                        continue
                    
                    # Reconstruction d'un message minimaliste (rôle + texte uniquement)
                    filtered_messages.append({
                        "role": role,
                        "content": str(content).strip()
                    })
                
                payload = {
                    'model': model,
                    'messages': filtered_messages,
                    'max_tokens': MODELS[model]['max_tokens'],
                    'temperature': 0.7
                }
            else:
                # Modèles agentiques (ex: GPT-OSS): on envoie l'historique complet + outils
                payload = {
                    'model': model,
                    'messages': global_chat_history,
                    'max_tokens': MODELS[model]['max_tokens'],
                    'temperature': 0.7,
                    'tools': tool_manager.get_albert_tools_schema()
                }
            
            # Log de débogage pour inspection des payloads envoyés
            print(f"DEBUG: Outgoing Payload for {model}: {json.dumps(payload, indent=2, ensure_ascii=False)}", flush=True)

            response = requests.post(
                f'{BASE_URL}/chat/completions',
                headers=headers,
                json=payload,
                timeout=MODELS[model]['timeout']
            )
            response.raise_for_status()
            
            data = response.json()
            message_obj = data['choices'][0]['message']
            reply = message_obj.get('content') or ""
            
            print(f"=== ITERATION {iterations} ===", flush=True)
            print("REPLY FROM MODEL:", reply, flush=True)
            
            # On logge toujours la réponse textuelle de l'agent si elle existe
            if reply:
                global_chat_history.append({"role": "assistant", "content": reply})
            
            # === DÉTECTION DES OUTILS (NATIVE OPENAI + FALLBACK ETALAB) ===
            matches = []
            
            # 1. Standard OpenAI 'tool_calls' support
            if 'tool_calls' in message_obj and message_obj['tool_calls']:
                # On ajoute aussi l'appel JSON dans l'historique pour ne pas casser le fil
                global_chat_history.append(message_obj)
                for tc in message_obj['tool_calls']:
                    if tc.get('type') == 'function':
                        func_name = tc['function']['name']
                        func_args = tc['function']['arguments']
                        matches.append((func_name, func_args))
            else:
                # 2. Regex fallback pour cibler [TOOL_CALLS]tool_name{"kwargs": "..."}
                tool_calls_pattern = r'\[TOOL_CALLS\]([a-zA-Z0-9_]+)(\{.*?\})'
                for m in re.finditer(tool_calls_pattern, reply, re.DOTALL):
                    matches.append((m.group(1), m.group(2)))
                
                # 3. Fallback pour XML-style (<tool_call> ou naked <function=>)
                # On supporte les deux formats identifiés par jbousquie/llm-proxy
                xml_patterns = [
                    r'<tool_call>\s*<function=([^>]+)>\s*(.*?)\s*</function>\s*</tool_call>',
                    r'<function=([^>]+)>\s*(.*?)\s*</function>'
                ]
                
                for pattern in xml_patterns:
                    for m in re.finditer(pattern, reply, re.DOTALL):
                        func_name = m.group(1).strip()
                        params_raw = m.group(2).strip()
                        
                        # Extraction des paramètres <parameter=name>value</parameter>
                        kwargs = {}
                        param_matches = re.finditer(r'<parameter=([^>]+)>(.*?)</parameter>', params_raw, re.DOTALL)
                        for pm in param_matches:
                            p_name = pm.group(1).strip()
                            p_value = pm.group(2).strip()
                            try:
                                kwargs[p_name] = json.loads(p_value)
                            except:
                                kwargs[p_name] = p_value
                        
                        matches.append((func_name, json.dumps(kwargs)))
                    if matches: break # Priorité au premier pattern trouvé
            
            if not matches:
                # Si aucun outil n'est demandé, c'est la réponse finale !
                final_reply = reply
                break
                
            # Mode "Agent Exécution"
            for match in matches:
                tool_name, json_args_str = match
                
                print(f"-> EXECUTING TOOL: {tool_name} with args {json_args_str}", flush=True)
                
                # Parsing des arguments JSON
                try:
                    kwargs = json.loads(json_args_str)
                except Exception as e:
                    kwargs = {}
                
                # Exécution SÉCURISÉE via notre Routeur Tolérant aux Pannes
                obs = tool_manager.execute_tool(tool_name, kwargs)
                
                print(f"-> OBSERVATION: {obs}", flush=True)
                
                # Injection de l'observation
                tool_observation = f"OBSERVATION DE L'OUTIL '{tool_name}' :\n{obs}"
                global_chat_history.append({"role": "user", "content": tool_observation})
            
            # Si on a exécuté des outils, la boucle 'while' recommence naturellement pour envoyer 
            # l'observation au LLM et obtenir la suite de son analyse !
            
        if not final_reply:
            final_reply = "Erreur: Limite d'itérations d'outils atteinte."

        return jsonify({
            'success': True,
            'type': 'chat',
            'reply': final_reply,
            'model': model
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'Erreur API HTTP: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def status():
    """Statut du serveur"""
    return jsonify({
        'success': True,
        'status': 'online',
        'port': PORT,
        'tools': len(tool_manager.tools),
        'models': len(MODELS),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/albert-agentic.js')
def serve_js():
    """Serve le fichier JavaScript"""
    return send_from_directory('.', 'albert-agentic.js')

# ==================== LANCEMENT ====================

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 ALBERT IA AGENTIC")
    print("=" * 50)
    print(f"Port: {PORT}")
    print(f"Workspace: {WORKSPACE_ROOT}")
    print(f"Modèles: {len(MODELS)}")
    print(f"Outils: {len(tool_manager.tools)}")
    print(f"Local: http://localhost:{PORT}")
    print(f"Réseau: http://100.100.128.63:{PORT}")
    print("=" * 50)
    
    # Créer répertoires
    os.makedirs(os.path.join(WORKSPACE_ROOT, "output"), exist_ok=True)
    
    # Démarrer
    app.run(host='0.0.0.0', port=PORT, debug=False)