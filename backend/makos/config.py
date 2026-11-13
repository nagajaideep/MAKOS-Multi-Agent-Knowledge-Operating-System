"""Settings read from environment variables (see .env.example)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def database_url() -> str:
    return os.environ.get(
        "MAKOS_DATABASE_URL", "postgresql+psycopg://makos:makos@localhost:5432/makos"
    )
