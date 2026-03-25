from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.config import DATE_OUTPUT_FORMAT
from models.schemas import TransactionRow


@dataclass
class NormalizationResult:
    rows: List[TransactionRow]
    audit_entries: List[Dict[str, Any]]


def _clean_text(value: Any, title_case: bool = False) -> str:
    text = "" if value is None else str(value)
    cleaned = " ".join(text.strip().split())
    if title_case and cleaned:
        return cleaned.title()
    return cleaned


def _to_float(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None

    normalized = re.sub(r"[^0-9\-().]", "", text)
    if normalized.startswith("(") and normalized.endswith(")"):
        normalized = f"-{normalized[1:-1]}"
    normalized = normalized.replace(",", "")

    try:
        return float(normalized)
    except ValueError:
        return None


def _normalize_date(raw: Any) -> tuple[str, bool]:
    text = _clean_text(raw)
    if not text:
        return "", False

    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return "", True

    return parsed.strftime(DATE_OUTPUT_FORMAT), False


def _normalize_amount(amount: Any, debit: Any, credit: Any) -> tuple[Optional[float], List[str], Optional[float], Optional[float]]:
    flags: List[str] = []

    amount_float = _to_float(amount)
    debit_float = _to_float(debit)
    credit_float = _to_float(credit)

    if amount_float is not None:
        return float(np.round(amount_float, 2)), flags, debit_float, credit_float

    if debit_float is not None and credit_float is not None and abs(debit_float) > 0 and abs(credit_float) > 0:
        flags.append("ambiguous_debit_credit")
        return None, flags, debit_float, credit_float

    if debit_float is not None:
        return float(np.round(-abs(debit_float), 2)), flags, debit_float, credit_float

    if credit_float is not None:
        return float(np.round(abs(credit_float), 2)), flags, debit_float, credit_float

    return None, flags, debit_float, credit_float


def _detect_malformed_row(cleaned: Dict[str, Any]) -> bool:
    populated = []
    for key, value in cleaned.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        populated.append(key)
    return len(populated) <= 1


def _build_cleaned_values(original: Dict[str, Any], mapping: Dict[str, str]) -> tuple[Dict[str, Any], List[str], Dict[str, Dict[str, Any]]]:
    cleaned: Dict[str, Any] = {
        "date": "",
        "description": "",
        "payee": "",
        "amount": "",
        "debit": "",
        "credit": "",
        "category": "",
        "account": "",
        "notes": "",
    }
    flags: List[str] = []
    audit_changes: Dict[str, Dict[str, Any]] = {}

    for canonical, source_column in mapping.items():
        raw = original.get(source_column, "")

        if canonical in {"payee", "vendor"}:
            normalized = _clean_text(raw, title_case=True)
        elif canonical in {"description", "notes", "category", "account"}:
            normalized = _clean_text(raw)
        elif canonical == "date":
            normalized, invalid_date = _normalize_date(raw)
            if invalid_date:
                flags.append("invalid_date")
        else:
            normalized = _clean_text(raw)

        if canonical == "vendor" and not cleaned.get("payee"):
            cleaned["payee"] = normalized
        else:
            cleaned[canonical] = normalized

        if str(raw) != str(normalized):
            audit_changes[canonical] = {"old": raw, "new": normalized}

    normalized_amount, amount_flags, normalized_debit, normalized_credit = _normalize_amount(
        cleaned.get("amount", ""),
        cleaned.get("debit", ""),
        cleaned.get("credit", ""),
    )
    flags.extend(amount_flags)

    if normalized_amount is None:
        raw_amount_provided = _clean_text(cleaned.get("amount", "")) or _clean_text(cleaned.get("debit", "")) or _clean_text(cleaned.get("credit", ""))
        flags.append("missing_amount" if not raw_amount_provided else "invalid_amount")
    cleaned["amount"] = normalized_amount
    cleaned["debit"] = normalized_debit
    cleaned["credit"] = normalized_credit

    if not cleaned.get("date"):
        flags.append("missing_date")

    if not cleaned.get("description") and not cleaned.get("payee"):
        flags.append("blank_description_payee")

    if _detect_malformed_row(cleaned):
        flags.append("malformed_row")

    if not cleaned.get("category"):
        flags.append("uncategorized_transaction")

    return cleaned, sorted(set(flags)), audit_changes


def _mark_sign_inconsistency(rows: List[TransactionRow]) -> None:
    for row in rows:
        if row.amount is None:
            continue
        if row.debit is not None and row.amount > 0:
            row.flags.append("inconsistent_sign")
        if row.credit is not None and row.amount < 0:
            row.flags.append("inconsistent_sign")
        row.flags = sorted(set(row.flags))


def _mark_outliers(rows: List[TransactionRow]) -> None:
    amounts = [abs(row.amount) for row in rows if row.amount is not None]
    if len(amounts) < 5:
        return

    series = pd.Series(amounts)
    threshold = float(series.mean() + (2.5 * series.std()))
    for row in rows:
        if row.amount is None:
            continue
        if abs(row.amount) > threshold:
            row.flags.append("amount_outlier")
            row.flags = sorted(set(row.flags))


def _mark_possible_transfer_pairs(rows: List[TransactionRow]) -> None:
    grouped: Dict[tuple[str, float], List[TransactionRow]] = {}
    for row in rows:
        if not row.date or row.amount is None:
            continue
        key = (row.date, round(abs(row.amount), 2))
        grouped.setdefault(key, []).append(row)

    for candidates in grouped.values():
        positives = [row for row in candidates if row.amount is not None and row.amount > 0]
        negatives = [row for row in candidates if row.amount is not None and row.amount < 0]
        if positives and negatives:
            for row in positives + negatives:
                row.flags.append("possible_transfer_pair")
                row.flags = sorted(set(row.flags))


def normalize_rows(job_id: str, df: pd.DataFrame, mapping: Dict[str, str]) -> NormalizationResult:
    rows: List[TransactionRow] = []
    audit_entries: List[Dict[str, Any]] = []

    for source_row_index, record in enumerate(df.to_dict(orient="records")):
        cleaned, flags, changes = _build_cleaned_values(record, mapping)

        row_id = f"row-{source_row_index + 1:06d}"
        row = TransactionRow(
            row_id=row_id,
            job_id=job_id,
            source_row_index=source_row_index,
            date=cleaned.get("date", ""),
            description=cleaned.get("description", ""),
            payee=cleaned.get("payee", ""),
            amount=cleaned.get("amount") if isinstance(cleaned.get("amount"), float) else None,
            debit=cleaned.get("debit") if isinstance(cleaned.get("debit"), float) else None,
            credit=cleaned.get("credit") if isinstance(cleaned.get("credit"), float) else None,
            category=cleaned.get("category", ""),
            account=cleaned.get("account", ""),
            notes=cleaned.get("notes", ""),
            flags=flags,
            cleaned_values=cleaned,
            original_values={str(k): v for k, v in record.items()},
        )
        rows.append(row)

        for field_name, diff in changes.items():
            audit_entries.append(
                {
                    "row_id": row_id,
                    "source_row_index": source_row_index,
                    "field_name": field_name,
                    "old_value": str(diff["old"]),
                    "new_value": str(diff["new"]),
                    "action": "normalize_field",
                    "note": "Normalized imported value.",
                }
            )

    _mark_sign_inconsistency(rows)
    _mark_possible_transfer_pairs(rows)
    _mark_outliers(rows)

    return NormalizationResult(rows=rows, audit_entries=audit_entries)


def text_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()
