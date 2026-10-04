#!/usr/bin/env python3
"""
Configuration loader for environment variables
"""

import os
from pathlib import Path
from typing import Optional


def load_env_file(env_file: str = ".env") -> None:
    """Load environment variables from .env file"""
    if Path(env_file).exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get configuration value from environment or default"""
    return os.getenv(key, default)


def get_required_config(key: str) -> str:
    """Get required configuration value, raise error if not found"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required configuration missing: {key}")
    return value


def get_ado_config() -> dict:
    """Get Azure DevOps configuration"""
    load_env_file()
    return {
        "org_url": get_required_config("AZURE_ORG_URL"),
        "project_name": get_required_config("AZURE_PROJECT_NAME"),
        "pat": get_required_config("AZURE_PAT"),
    }


def get_import_config() -> dict:
    """Get import configuration"""
    load_env_file()
    return {
        "excel_file": get_required_config("EXCEL_FILE_PATH"),
        "mapping_file": get_config("MAPPING_FILE_PATH", "ado_traceability_map.json"),
        "report_format": get_config("REPORT_FORMAT", "csv"),
    }
