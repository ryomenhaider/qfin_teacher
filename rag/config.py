import json
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".config" / "qfin-rag"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

def get_api_key() -> str:
    config = load_config()
    return config.get("api_key", "")

def set_api_key(key: str):
    config = load_config()
    config["api_key"] = key
    save_config(config)

def get_docs_dir() -> Path:
    config = load_config()
    docs_path = config.get("docs_dir", "")
    if docs_path:
        return Path(docs_path)
    return Path(__file__).parent.parent / "docs"

def set_docs_dir(path: str):
    config = load_config()
    config["docs_dir"] = path
    save_config(config)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
VECTOR_STORE = DATA_DIR / "vector_store"
VECTOR_STORE.mkdir(exist_ok=True)