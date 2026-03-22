import os
import shutil

def effacer_fichiers(path: str, recursive: bool = False, pattern: str = None, dry_run: bool = False) -> dict:
    """Supprime les fichiers d'un répertoire.

    Args:
        path (str): Chemin du répertoire cible.
        recursive (bool): Si True, parcourir les sous‑dossiers.
        pattern (str, optional): Pattern glob (ex: "*.tmp") pour ne supprimer que les fichiers correspondants.
        dry_run (bool): Si True, aucune suppression n’est réellement effectuée ; les fichiers qui seraient supprimés sont listés.

    Returns:
        dict: Résultat contenant le nombre de fichiers supprimés (ou listés en dry‑run) et les chemins concernés.
    """
    if not os.path.isdir(path):
        return {"error": f"Le chemin fourni n'est pas un répertoire valide: {path}"}

    import fnmatch
    deleted = []
    # Choisir la fonction de traversée
    if recursive:
        walker = os.walk(path)
        for root, dirs, files in walker:
            for fname in files:
                if pattern and not fnmatch.fnmatch(fname, pattern):
                    continue
                full_path = os.path.join(root, fname)
                if dry_run:
                    deleted.append(full_path)
                else:
                    try:
                        os.remove(full_path)
                        deleted.append(full_path)
                    except Exception as e:
                        # On continue malgré l'erreur mais on le note
                        deleted.append({"file": full_path, "error": str(e)})
    else:
        for fname in os.listdir(path):
            full_path = os.path.join(path, fname)
            if os.path.isfile(full_path):
                if pattern and not fnmatch.fnmatch(fname, pattern):
                    continue
                if dry_run:
                    deleted.append(full_path)
                else:
                    try:
                        os.remove(full_path)
                        deleted.append(full_path)
                    except Exception as e:
                        deleted.append({"file": full_path, "error": str(e)})
    return {"dry_run": dry_run, "count": len(deleted), "files": deleted}
