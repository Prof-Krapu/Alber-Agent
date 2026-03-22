import os
import shutil

def duplicate_file(source: str, destination: str) -> str:
    """Copie le fichier *source* vers *destination*.

    Retourne une chaîne de caractères décrivant le résultat.
    """
    # Vérifier l'existence du fichier source
    if not os.path.isfile(source):
        return f"Erreur: le fichier source '{source}' n'existe pas."
    # Créer le répertoire cible si nécessaire
    dest_dir = os.path.dirname(destination)
    if dest_dir and not os.path.isdir(dest_dir):
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except Exception as e:
            return f"Erreur lors de la création du répertoire destination '{dest_dir}': {e}"
    # Effectuer la copie
    try:
        shutil.copyfile(source, destination)
        return f"Succès: '{source}' a été dupliqué vers '{destination}'."
    except Exception as e:
        return f"Erreur lors de la duplication: {e}"