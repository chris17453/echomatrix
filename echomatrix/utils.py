import os

def cleanup_temp_file(path):
    try:
        os.remove(path)
    except Exception:
        pass
