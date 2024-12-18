import json
from pathlib import Path

DATA_FILE = Path("tracked_tokens.json")


def save_token_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def load_token_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}
