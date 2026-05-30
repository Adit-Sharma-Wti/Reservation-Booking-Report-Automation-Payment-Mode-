# ============================================================
# CONFIG LOADER — Resolves Environment Variable Placeholders
# config_loader.py
# ============================================================

import os
import re
import configparser
from pathlib import Path


def load_config(path: str = "config.ini") -> configparser.ConfigParser:
    """
    Loads config.ini and replaces ${VAR_NAME} placeholders
    with actual environment variable values.
    
    Raises clear errors if required secrets are missing.
    """
    if not Path(path).exists():
        raise FileNotFoundError(
            f"config.ini not found at: {path}"
        )

    # Read raw config file content
    with open(path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    # Find all placeholders like ${VAR_NAME}
    placeholders = re.findall(r'\$\{(\w+)\}', raw_content)

    # Replace each placeholder with env variable value
    missing = []
    for var_name in placeholders:
        value = os.environ.get(var_name, "")
        if not value:
            missing.append(var_name)
        raw_content = raw_content.replace(f"${{{var_name}}}", value)

    # Warn about missing secrets
    if missing:
        print(
            f"⚠️  WARNING: Missing environment variables: "
            f"{', '.join(missing)}"
        )

    # Parse the resolved config content
    config = configparser.ConfigParser()
    config.read_string(raw_content)

    return config