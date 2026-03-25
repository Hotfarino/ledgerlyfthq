from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR.parent / "data"
SAMPLE_DATA_DIR = BASE_DIR.parent / "sample_data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
DB_PATH = BASE_DIR / "db" / "ledgerlyfthq_v1.db"
DATE_OUTPUT_FORMAT = "%Y-%m-%d"
DEFAULT_EXECUTION_MODE = "isolated"
ENABLE_SHARED_ADAPTER = os.getenv("LEDGERLYFTHQ_ENABLE_SHARED_ADAPTER", "false").lower() == "true"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
