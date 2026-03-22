from pathlib import Path
import os

def list_files(directory="."):
    try:
        # Convert the directory string to a Path object if it's not already
        path = Path(directory)
        if not path.is_dir():
            return []
        
        # List all files and directories in the given path
        contents = os.listdir(path)
        return contents
    except Exception as e:
        return str(e)