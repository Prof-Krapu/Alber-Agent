import os, json, sys
def list_all(directory='.'):
    try:
        entries = os.listdir(directory)
        # Return as JSON string for easy parsing
        return json.dumps(entries)
    except Exception as e:
        return json.dumps({'error': str(e)})
