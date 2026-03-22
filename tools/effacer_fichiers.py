import os
import fnmatch

def effacer_fichiers(path: str, recursive: bool = False, pattern: str = None, dry_run: bool = False) -> str:
    """
    Supprime les fichiers d'un répertoire avec support du filtrage par pattern et mode récursif.
    """
    if not os.path.exists(path):
        return f"Erreur: Le chemin '{path}' n'existe pas."

    deleted = []
    try:
        if recursive:
            for root, dirs, files in os.walk(path):
                for fname in files:
                    if pattern and not fnmatch.fnmatch(fname, pattern):
                        continue
                    full_path = os.path.join(root, fname)
                    if dry_run:
                        deleted.append(f"[DRY-RUN] {full_path}")
                    else:
                        os.remove(full_path)
                        deleted.append(full_path)
        else:
            if os.path.isdir(path):
                for fname in os.listdir(path):
                    full_path = os.path.join(path, fname)
                    if os.path.isfile(full_path):
                        if pattern and not fnmatch.fnmatch(fname, pattern):
                            continue
                        if dry_run:
                            deleted.append(f"[DRY-RUN] {full_path}")
                        else:
                            os.remove(full_path)
                            deleted.append(full_path)
            elif os.path.isfile(path):
                 if dry_run:
                    deleted.append(f"[DRY-RUN] {path}")
                 else:
                    os.remove(path)
                    deleted.append(path)
        
        if not deleted:
            return "Aucun fichier correspondant trouvé ou supprimé."
            
        res = f"Succès: {len(deleted)} fichiers traités.\n"
        res += "\n".join(deleted[:10])
        if len(deleted) > 10: res += f"\n... (+ {len(deleted)-10} autres)"
        return res
    except Exception as e:
        return f"Erreur lors de la suppression: {str(e)}"
