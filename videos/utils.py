import re

def sanitize_filename(filename):
    """
    Sanitizes a filename to be used as a folder name.

    This function replaces spaces with underscores and removes any characters
    that are not alphanumeric, underscores, periods, or hyphens from the filename.
    This ensures that the filename is safe to be used as a directory name in
    most file systems.

    Args:
        filename (str): The filename to sanitize.

    Returns:
        str: The sanitized filename.
    """
    filename = filename.replace(" ", "_")
    filename = re.sub(r'[^\w.-]', '', filename)
    return filename