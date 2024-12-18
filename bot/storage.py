import json
import os

STORAGE_FILE = "tracked_tokens.json"

def load_tracked_tokens():
    """Load tracked tokens from a JSON file."""
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tracked_tokens(tracked_tokens):
    """Save tracked tokens to a JSON file."""
    with open(STORAGE_FILE, "w") as f:
        json.dump(tracked_tokens, f, indent=4)
