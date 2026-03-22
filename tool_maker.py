import os
import ast
import json
import inspect
import importlib.util
import traceback
from pathlib import Path
from typing import get_type_hints, Any, Dict, Callable

# Chemin par défaut (pour compatibilité)
DEFAULT_SKILLS_DIR = Path("./skills").resolve()

class ToolMakerEngine:
    """
    Système Multi-Agents de Tool-Making.
    Permet à l'agent de coder, recharger et s'auto-exécuter des outils Python.
    """
    def __init__(self, skills_dir=None):
        self.tools: Dict[str, Callable] = {}
        # Liste des outils internes (hardcoded) qui ne doivent pas être supprimés lors du scan
        self.internal_tools: set = set()
        # Utiliser le répertoire spécifié ou le défaut
        self.skills_dir = Path(skills_dir).resolve() if skills_dir else DEFAULT_SKILLS_DIR
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        # L'outil d'amorçage est injecté par défaut
        self.register_tool(self.create_skill, internal=True)

    def register_tool(self, func: Callable, internal=False):
        name = func.__name__
        self.tools[name] = func
        if internal:
            self.internal_tools.add(name)

    def create_skill(self, nom_outil: str, code_python: str) -> str:
        """
        Crée ou met à jour un outil (skill) Python dynamiquement.
        ATTENTION: Le nom de la fonction Python DOIT correspondre exactement au `nom_outil` que tu veux créer.
        
        Args:
            nom_outil: Le nom du fichier Python sans l'extension ET le nom exact de la fonction principale (ex: 'mon_outil').
            code_python: Le code source Python complet de l'outil (ex: 'def mon_outil(): ...').
            
        Returns:
            str: Un message de confirmation ou l'erreur de compilation si la syntaxe est invalide.
        """
        # Sécurité : Restreindre l'écriture strictement au dossier des skills
        file_path = (self.skills_dir / f"{nom_outil}.py").resolve()
        if not str(file_path).startswith(str(self.skills_dir)):
            return "Erreur: Nom d'outil invalide (Tentative de Path Traversal)."

        # 1. Validation sémantique de la syntaxe Python
        try:
            ast.parse(code_python)
        except SyntaxError:
            # Capturer l'erreur de syntaxe avec sa trace complète pour le LLM
            return f"❌ Erreur de syntaxe fatale dans le code de l'outil:\n{traceback.format_exc()}\n\n-> Corrige la syntaxe et rappelle create_skill."
        
        # 2. Sauvegarde du fichier
        try:
            file_path.write_text(code_python, encoding="utf-8")
        except Exception:
            return f"❌ Erreur I/O lors de l'écriture du fichier:\n{traceback.format_exc()}"
            
        # 3. Hot-Reloading immédiat pour flusher la mémoire avec le nouvel outil
        reload_msg = self.discover_skills()
        return f"✅ Outil '{nom_outil}' compilé, sauvegardé et chargé avec succès.\n\nStatut du rechargement:\n{reload_msg}"

    def discover_skills(self) -> str:
        """
        Scanne le dossier des skills et charge/recharge dynamiquement les modules Python.
        Supprime les outils qui ne sont plus présents sur le disque (sauf outils internes).
        """
        loaded_tools = []
        errors = []
        
        # On ne garde que les outils internes avant de rescanner
        temp_tools = {name: self.tools[name] for name in self.internal_tools if name in self.tools}
        self.tools = temp_tools
        
        print(f"DEBUG: Scanning directory: {self.skills_dir}")
        for py_file in self.skills_dir.glob("*.py"):
            module_name = py_file.stem
            try:
                # Importation dynamique via importlib
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                # Exécution et chargement en mémoire
                spec.loader.exec_module(module)
                
                # Isolation des fonctions: on scrute uniquement les fonctions déclarées dans ce module
                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    # Ignorer les fonctions privées
                    if not name.startswith("_"):
                        try:
                            # On vérifie que la fonction appartient bien au module chargé (et pas un import)
                            if obj.__module__ == module_name:
                                self.register_tool(obj)
                                loaded_tools.append(name)
                        except Exception:
                            pass
            except Exception as e:
                errors.append(f"Erreur de chargement pour '{module_name}': {e}")
                
        msg = f"Rechargement terminé. Outils actifs: {', '.join(list(self.tools.keys()))}"
        if errors:
            msg += "\n" + "\n".join(errors)
        return msg

    def generate_schema(self, func: Callable) -> dict:
        """
        Extrait Type Hints et Docstrings pour construire automatiquement le schéma d'outil ALBERT/OpenAI.
        """
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        type_hints = get_type_hints(func)
        
        # Extraire la première ligne du docstring (description globale)
        doc_lines = doc.strip().split('\n')
        description = doc_lines[0] if doc_lines else f"Outil agentique: {func.__name__}"
        
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }

        # Conversion des paramètres de la signature en JSON Schema
        for name, param in sig.parameters.items():
            if name == "self":
                continue
                
            param_type = "string" # Fallback par défaut
            hint = type_hints.get(name, Any)
            
            # Formattage basique des types Python -> JSON Schema
            if hint == int:
                param_type = "integer"
            elif hint == float:
                param_type = "number"
            elif hint == bool:
                param_type = "boolean"
            elif hint == list or getattr(hint, '__origin__', None) == list:
                param_type = "array"
            elif hint == dict or getattr(hint, '__origin__', None) == dict:
                param_type = "object"
                
            # Recherche de la ligne correspondant au paramètre dans le docstring (Format Google/Sphinx)
            param_desc = ""
            for line in doc_lines:
                clean_line = line.strip()
                if clean_line.startswith(f"{name}:") or clean_line.startswith(f"{name} ("):
                    param_desc = clean_line.split(":", 1)[-1].strip()
                    break

            parameters["properties"][name] = {
                "type": param_type,
                "description": param_desc or f"Valeur pour {name}"
            }
            
            # Les attributs sans `= default` sont obligatoires
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(name)

        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": description,
                "parameters": parameters
            }
        }

    def get_albert_tools_schema(self) -> list:
        """
        Génère le payload JSON attendu par la clé `tools` de l'API Albert.
        """
        # On regénère les schémas à la volée pour s'assurer qu'ils matchent les outils en mémoire
        return [self.generate_schema(func) for func in self.tools.values()]

    def execute_tool(self, tool_name: str, kwargs: dict) -> str:
        """
        Routeur de Survie (Dispatcher).
        Intercepte, exécute et blinde la boucle principale contre tout crash du sous-processus de l'outil.
        """
        if tool_name not in self.tools:
            return f"❌ Erreur Execution: L'outil '{tool_name}' est introuvable. Avez-vous appelé create_skill ?"
            
        func = self.tools[tool_name]
        
        try:
            result = func(**kwargs)
            
            # Stringification intelligente pour assurer la longévité de l'agent
            if isinstance(result, (dict, list)):
                return json.dumps(result, ensure_ascii=False, indent=2)
            if result is None:
                return "Exécution terminée sans retour de valeur."
            return str(result)
            
        except Exception:
            # 🧨 CATCH ABSOLU : Le script utilisateur a planté !
            # Au lieu de faire crasher le chatbot, on lui remonte l'erreur complète pour qu'il la lise.
            error_trace = traceback.format_exc()
            alert = (
                f"⚠️ EXCEPTION TRACÉE (KILLED) LORS DE L'EXÉCUTION DE '{tool_name}':\n\n"
                f"```python-traceback\n{error_trace}\n```\n\n"
                f"==> Analyse attentivement cette trace d'erreur. Modifie le code source en conséquence et rappelle `create_skill` pour patcher ce comportement."
            )
            return alert

# =================================================================================
#               MODUS OPERANDI - INTÉGRATION BOUCLE D'INFÉRENCE
# =================================================================================
#
# from tool_maker import ToolMakerEngine
# import json
# import requests
# 
# engine = ToolMakerEngine()
# engine.discover_skills()  # Charge le cache persistant ./skills/ au boot
# 
# history = [{"role": "system", "content": "Tu es un Master Agent. Développe tes outils avec `create_skill`."}]
# 
# while True:
#     # ... Récupération input_utilisateur ...
#     # history.append({"role": "user", "content": input_utilisateur})
#     
#     # 1. Mise à disposition du schéma généré dynamiquement !
#     payload = {
#         "model": "mistralai/Ministral-3-8B-Instruct-2512",
#         "messages": history,
#         "tools": engine.get_albert_tools_schema()  # Extrait les skills dispo
#     }
#     
#     res = requests.post("https://albert.api...", json=payload, headers=headers).json()
#     message = res['choices'][0]['message']
#     history.append(message)
#     
#     if 'tool_calls' in message:
#         for tool_call in message['tool_calls']:
#             tool_name = tool_call['function']['name']
#             try:
#                 kwargs = json.loads(tool_call['function']['arguments'])
#             except Exception:
#                 kwargs = {}
#             
#             # 2. Exécution blindée et réception de la stacktrace le cas échéant
#             obs = engine.execute_tool(tool_name, kwargs)
#             
#             # 3. Réinjection de l'observation
#             history.append({
#                 "role": "tool",
#                 "tool_call_id": tool_call['id'],
#                 "name": tool_name,
#                 "content": obs
#             })
#         
#         # Retour au début pour que le LLM observe le résultat et agisse (ou se corrige !)
#         continue
#         
#     # ... Affiche la réponse finale ...
