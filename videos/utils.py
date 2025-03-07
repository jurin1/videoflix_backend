import re

def sanitize_filename(filename):
    """Bereinigt einen Dateinamen für die Verwendung als Ordnername."""
    filename = filename.replace(" ", "_")
    filename = re.sub(r'[^\w.-]', '', filename)
    return filename