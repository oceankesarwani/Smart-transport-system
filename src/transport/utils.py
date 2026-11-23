"""
Utility Functions and Configuration Helpers
"""
import os
from pathlib import Path
import yaml
from typing import Dict, Any

def get_project_root() -> Path:
    """Returns absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def load_config(config_path: str = None) -> Dict[str, Any]:
    """Loads config.yaml from project root."""
    if config_path is None:
        config_path = str(get_project_root() / "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_dir(dir_path: Path):
    """Ensures directory exists."""
    os.makedirs(dir_path, exist_ok=True)
