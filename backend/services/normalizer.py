from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.config import DATE_OUTPUT_FORMAT
from models.constants import REQUIRED_FIELDS
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


def _normalize_date(raw: Any) -> str:
    text = _clean_text(raw)
    if not text:
        return ""
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.strftime(DATE_OUTPUT_FORMAT)


def _normalize_amount(amount: Any, debit: Any, credit: Any) -> tuple[Optional[float], List[str], bool]:
    flags: List[str] = []
    ambiguous = False

    amount_float = _to_float(amount)
    debit_float = _to_float(debit)
    credit_float = _to_float(credit)

    if amount_float is not None:
        if debit_float is not None and credit_float is not None:
            flags.append("ambiguous_debit_credit")
            ambiguous = True
        return amount_float, flags, ambiguous

    if debit_float is not None and credit_float is not None:
        flags.append("ambiguous_debit_credit")
        ambiguous = True
        if abs(debit_float) > 0 and abs(credit_float) > 0:
            return None, flags, ambiguous

    if debit_float is not None:
        return -abs(debit_float), flags, ambiguous
    if credit_float is not None:
        return abs(credit_float), flags, ambiguous

    flags.append("missing_amount")
    return None, flags, ambiguous


def _detect_malformed_row(cleaned: Dict[str, Any]) -> bool:
    populated = [k for k, v in cleaned.items() if str(v).strip()]
    return len(populated) <= 1


def _build_cleaned_values(original: Dict[str, Any], mapping: Dict[str, str]) -> tuple[Dict[str, Any], List[str], Dict[str, Any]]:
    flags: List[str] = []
    audit_changes: Dict[str, Any] = {}

    cleaned: Dict[str, Any] = {}
    for canonical, source in mapping.items():
        raw = original.get(source, "")
        if canonical in {"payee", "vendor", "description", "memo", "category", "account"}:
            title_case = canonical in {"payee", "vendor"}
            normalized = _clean_text(raw, title_case=title_case)
        elif canonical == "date":
            normalized = _normalize_date(raw)
            if _clean_text(raw) and not normalized:
                flags.append("invalid_date")
        else:
            normalized = _clean_text(raw)
        cleaned[canonical] = normalized
        if str(raw) != str(normalized):
            audit_changes[canonical] = {"old": raw, "new": normalized}

    amount, amount_flags, _ = _normalize_amount(
        cleaned.get("amount", ""), cleaned.get("debit", ""), cleaned.get("credit", "")
    )
    flags.extend(amount_flags)
    if amount is None:
        cleaned["signed_amount"] = ""
    else:
        cleaned["signed_amount"] = float(np.round(amount, 2))

    if not cleaned.get("date"):
        flags.append("missing_date")
    if cleaned.get("signed_amount") == "":
        flags.append("invalid_numeric_amount")
    if not cleaned.get("description") and not cleaned.get("payee"):
        flags.append("blank_description_payee")

    category = cleaned.get("category", "")
    if not category:
        flags.append("uncategorized_transaction")

    if _detect_malformed_row(cleaned):
        flags.append("likely_malformed_row")

    return cleaned, sorted(set(flags)), audit_changes


def _mark_sign_inconsistencies(rows: List[TransactionRow]) -> None:
    for row in rows:
        cleaned = row.cleaned_values
        amount = cleaned.get("signed_amount")
        if amount == "":
            continue
        debit = _to_float(cleaned.get("debit", ""))
        credit = _to_float(cleaned.get("credit", ""))
        if debit is not None and amount > 0:
            row.flags.append("inconsistent_sign")
        if credit is not None and amount < 0:
            row.flags.append("inconsistent_sign")
        row.flags = sorted(set(row.flags))


def _mark_outliers(rows: List[TransactionRow]) -> None:
    amounts = [abs(float(r.cleaned_values["signed_amount"])) for r in rows if r.cleaned_values.get("signed_amount") != ""]
    if len(amounts) < 5:
        return
    series = pd.Series(amounts)
    threshold = series.mean() + (2.5 * series.std())
    for row in rows:
        amount = row.cleaned_values.get("signed_amount")
        if amount == "":
            continue
        if abs(float(amount)) > threshold:
            row.flags.append("amount_outlier")
            row.flags = sorted(set(row.flags))


def _mark_possible_transfer_pairs(rows: List[TransactionRow]) -> None:
    by_date_amount: Dict[tuple[str, float], List[TransactionRow]] = {}
    for row in rows:
        date = row.cleaned_values.get("date", "")
        amount = row.cleaned_values.get("signed_amount", "")
        if not date or amount == "":
            continue
        key = (date, round(abs(float(amount)), 2))
        by_date_amount.setdefault(key, []).append(row)

    for _, grouped in by_date_amount.items():
        positives = [r for r in grouped if r.cleaned_values.get("signed_amount", 0) > 0]
        negatives = [r for r in grouped if r.cleaned_values.get("signed_amount", 0) < 0]
        if positives and negatives:
            for row in positives + negatives:
                row.flags.append("possible_transfer_pair")
                row.flags = sorted(set(row.flags))


def normalize_rows(job_id: str, df: pd.DataFrame, mapping: Dict[str, str]) -> NormalizationResult:
    rows: List[TransactionRow] = []
    audit_entries: List[Dict[str, Any]] = []

    for idx, record in enumerate(df.to_dict(orient="records")):
        cleaned, flags, changes = _build_cleaned_values(record, mapping)
        transaction_id = cleaned.get("transaction_id") or f"row-{idx + 1}"
        row = TransactionRow(
            job_id=job_id,
            row_index=idx,
            transaction_id=transaction_id,
            original_values={str(k): v for k, v in record.items()},
            cleaned_values=cleaned,
            flags=flags,
        )
        rows.append(row)

        for field_name, diff in changes.items():
            audit_entries.append(
                {
                    "row_index": idx,
                    "field_name": field_name,
                    "old_value": str(diff["old"]),
                    "new_value": str(diff["new"]),
                    "action": "normalize_field",
                    "note": "Normalized imported value.",
                }
            )

    _mark_sign_inconsistencies(rows)
    _mark_possible_transfer_pairs(rows)
    _mark_outliers(rows)

    return NormalizationResult(rows=rows, audit_entries=audit_entries)


def text_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()
