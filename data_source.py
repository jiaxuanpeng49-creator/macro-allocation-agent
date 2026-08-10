import requests
import json
from pathlib import Path


DATA_FILE = Path(__file__).parent / "data" / "macro.json"


def load_macro_data():
    with DATA_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    return data

