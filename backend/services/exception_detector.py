from __future__ import annotations

import uuid
from typing import Dict, List, Set

from models.schemas import ExceptionFlag, TransactionRow

FLAG_MESSAGES: Dict[str, tuple[str, str]] = {
    "missing_date": ("high", "Date is missing."),
    "missing_amount": ("high", "Amount is missing."),
    "invalid_date": ("high", "Date could not be parsed into a valid format."),
    "invalid_amount": ("high", "Amount value is invalid."),
    "blank_description_payee": ("medium", "Description and payee are both blank."),
    "malformed_row": ("high", "Row appears malformed or mostly empty."),
    "ambiguous_debit_credit": ("medium", "Debit and credit are both populated and ambiguous."),
    "inconsistent_sign": ("medium", "Amount sign appears inconsistent with debit/credit fields."),
    "possible_transfer_pair": ("low", "Potential transfer pair detected."),
    "amount_outlier": ("low", "Amount appears as an outlier in this file."),
    "uncategorized_transaction": ("low", "Category is blank."),
    "suspicious_duplicate": ("medium", "Suspicious duplicate transaction."),
}


def build_exceptions(job_id: str, rows: List[TransactionRow], duplicate_row_ids: Set[str]) -> List[ExceptionFlag]:
    result: List[ExceptionFlag] = []

    for row in rows:
        row_flags = set(row.flags)
        if row.row_id in duplicate_row_ids:
            row_flags.add("suspicious_duplicate")

        for flag in sorted(row_flags):
            severity, message = FLAG_MESSAGES.get(flag, ("low", flag.replace("_", " ").title()))
            result.append(
                ExceptionFlag(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    row_id=row.row_id,
                    source_row_index=row.source_row_index,
                    flag_type=flag,
                    severity=severity,
                    message=message,
                    details={"cleaned_values": row.cleaned_values},
                )
            )

    return result
