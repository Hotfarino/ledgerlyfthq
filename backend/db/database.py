from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.config import DB_PATH


class Database:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    column_mapping_json TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    raw_df_json TEXT NOT NULL,
                    last_export_at TEXT
                );

                CREATE TABLE IF NOT EXISTS rows (
                    job_id TEXT NOT NULL,
                    row_index INTEGER NOT NULL,
                    transaction_id TEXT,
                    original_json TEXT NOT NULL,
                    cleaned_json TEXT NOT NULL,
                    flags_json TEXT NOT NULL,
                    notes TEXT,
                    review_status TEXT NOT NULL,
                    category_suggestion TEXT,
                    category_confidence TEXT,
                    PRIMARY KEY(job_id, row_index)
                );

                CREATE TABLE IF NOT EXISTS exceptions (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    row_index INTEGER NOT NULL,
                    flag_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    reviewed INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS duplicates (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    row_indices_json TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    match_type TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    reviewed INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS category_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    target_field TEXT NOT NULL,
                    contains_text TEXT NOT NULL,
                    suggested_category TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    active INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_entries (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    row_index INTEGER,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    action TEXT NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def dumps(value: Any) -> str:
        return json.dumps(value, default=str)

    @staticmethod
    def loads(value: Optional[str], default: Any) -> Any:
        if not value:
            return default
        return json.loads(value)


db = Database()
