from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from models.constants import CANONICAL_COLUMNS, COLUMN_ALIASES


def load_dataframe(file_path: Path) -> pd.DataFrame:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path, dtype=str, keep_default_na=False)
    if suffix in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return pd.read_excel(file_path, dtype=str, engine="openpyxl").fillna("")
    raise ValueError(f"Unsupported file type: {suffix}")


def _normalize_header(header: str) -> str:
    return " ".join(str(header).strip().lower().replace("_", " ").split())


def detect_column_mapping(df: pd.DataFrame) -> Tuple[Dict[str, str], list[str]]:
    mapping: Dict[str, str] = {}
    normalized_headers = {_normalize_header(c): c for c in df.columns}

    for canonical in CANONICAL_COLUMNS:
        aliases = COLUMN_ALIASES.get(canonical, [])
        for alias in aliases:
            key = _normalize_header(alias)
            if key in normalized_headers:
                mapping[canonical] = normalized_headers[key]
                break

    unmapped = [h for h in df.columns if h not in mapping.values()]
    return mapping, unmapped


def dataframe_to_raw_json(df: pd.DataFrame) -> str:
    return df.to_json(orient="records")


def dataframe_from_raw_json(raw_json: str) -> pd.DataFrame:
    return pd.read_json(raw_json, orient="records", dtype=False).fillna("")
