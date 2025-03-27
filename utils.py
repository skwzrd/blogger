import os
import re

def make_path(*file_path):
    """Make a file path as though this file's directory is a root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), *file_path))

def quote_path(text):
    text = re.sub(r'[^a-zA-Z0-9_ ]', '', text).lower()
    text = re.sub(r' +|_+', '_', text)
    return text
