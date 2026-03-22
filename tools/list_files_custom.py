import os

def list_files_custom(directory: str = ".") -> str:
    """
    Spécialisation de list_files pour Albert.
    """
    import json
    from pathlib import Path
    try:
        workspace = os.getcwd() # Ou passer via une globale
        target = (Path(workspace) / directory).resolve()
        files = []
        for item in target.iterdir():
            files.append({"name": item.name, "type": "dir" if item.is_dir() else "file", "size": item.stat().st_size if item.is_file() else 0})
        return json.dumps(files, ensure_ascii=False)
    except Exception as e:
        return str(e)
