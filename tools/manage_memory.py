"""
Outil de gestion de la mémoire à long terme (LTM) de l'agent.
Permet de sauvegarder de manière persistante des informations sur l'utilisateur ou le contexte.
"""

from pathlib import Path
import json
from datetime import datetime

# Chemin vers le fichier de mémoire caché dans le workspace
# Assumer qu'on s'exécute dans l'environnement de l'agent
MEMORY_FILE = Path("./workspace/.agent_memory.md")

def manage_memory(action: str, content: str = "") -> str:
    """
    Gère la mémoire à long terme de l'agent.
    Args:
        action (str): "read" pour lire la mémoire, "append" pour ajouter un souvenir, "clear" pour tout effacer.
        content (str): Le contenu du souvenir à ajouter (requis si action="append").
    """
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    if action == "append":
        if not content:
            return "Erreur: Le contenu est requis pour ajouter un souvenir."
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"- [{timestamp}] {content}\n"
        
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
            
        return "Souvenir enregistré avec succès dans la mémoire à long terme."
        
    elif action == "read":
        if not MEMORY_FILE.exists():
            return "La mémoire est actuellement vide."
            
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memory_content = f.read().strip()
            
        if not memory_content:
            return "La mémoire est actuellement vide."
            
        return f"=== CONTENU DE LA MÉMOIRE À LONG TERME ===\n{memory_content}"
        
    elif action == "clear":
        if MEMORY_FILE.exists():
            MEMORY_FILE.unlink()
        return "La mémoire a été entièrement effacée."
        
    else:
        return f"Erreur: Action '{action}' non reconnue. Utilisez 'read', 'append' ou 'clear'."
