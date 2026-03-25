from __future__ import annotations

import uuid
from typing import Dict, List

from models.schemas import ExceptionFlag, TransactionRow

FLAG_MESSAGES: Dict[str, tuple[str, str]] = {
    "missing_date": ("high", "Date is missing."),
    "missing_amount": ("high", "Amount is missing."),
    "invalid_numeric_amount": ("high", "Amount could not be normalized to a numeric value."),
    "ambiguous_debit_credit": ("medium", "Debit and credit values are ambiguous."),
    "inconsistent_sign": ("medium", "Amount sign appears inconsistent with debit/credit columns."),
    "blank_description_payee": ("medium", "Description and payee are both blank."),
    "likely_malformed_row": ("high", "Row appears malformed or mostly blank."),
    "uncategorized_transaction": ("low", "Category is missing."),
    "possible_transfer_pair": ("low", "Possible transfer pair found with opposite signed amount."),
    "amount_outlier": ("low", "Amount is an outlier compared to the rest of the dataset."),
    "suspicious_duplicate": ("medium", "Suspicious duplicate transaction."),
    "invalid_date": ("high", "Date value could not be parsed."),
}


def build_exceptions(job_id: str, rows: List[TransactionRow], duplicate_row_indices: set[int]) -> List[ExceptionFlag]:
    results: List[ExceptionFlag] = []

    for row in rows:
        flags = set(row.flags)
        if row.row_index in duplicate_row_indices:
            flags.add("suspicious_duplicate")

        for flag in sorted(flags):
            severity, message = FLAG_MESSAGES.get(flag, ("low", flag.replace("_", " ").title()))
            results.append(
                ExceptionFlag(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    row_index=row.row_index,
                    flag_type=flag,
                    severity=severity,
                    message=message,
                    details={"cleaned": row.cleaned_values},
                )
            )

    return results
