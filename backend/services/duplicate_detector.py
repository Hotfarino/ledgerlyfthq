from __future__ import annotations

import uuid
from collections import defaultdict
from typing import List

from models.schemas import ConfidenceLevel, DuplicateGroup, TransactionRow
from services.normalizer import text_similarity


def detect_duplicates(job_id: str, rows: List[TransactionRow]) -> List[DuplicateGroup]:
    groups: List[DuplicateGroup] = []
    used_rows: set[int] = set()

    exact_map = defaultdict(list)
    for row in rows:
        date = row.cleaned_values.get("date", "")
        amount = row.cleaned_values.get("signed_amount", "")
        desc = row.cleaned_values.get("description", "")
        payee = row.cleaned_values.get("payee", "")
        key = (date, amount, desc.lower(), payee.lower())
        exact_map[key].append(row)

    for grouped_rows in exact_map.values():
        if len(grouped_rows) > 1:
            indices = [r.row_index for r in grouped_rows]
            groups.append(
                DuplicateGroup(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    row_indices=indices,
                    confidence=ConfidenceLevel.HIGH,
                    match_type="exact",
                    reason="Rows share date, amount, payee, and description.",
                )
            )
            used_rows.update(indices)

    candidate_rows = [r for r in rows if r.row_index not in used_rows]
    for idx, left in enumerate(candidate_rows):
        for right in candidate_rows[idx + 1 :]:
            if left.row_index in used_rows or right.row_index in used_rows:
                continue

            left_date = left.cleaned_values.get("date", "")
            right_date = right.cleaned_values.get("date", "")
            if not left_date or left_date != right_date:
                continue

            left_amount = left.cleaned_values.get("signed_amount")
            right_amount = right.cleaned_values.get("signed_amount")
            if left_amount == "" or right_amount == "":
                continue
            if abs(float(left_amount) - float(right_amount)) > 0.01:
                continue

            left_text = f"{left.cleaned_values.get('payee', '')} {left.cleaned_values.get('description', '')}".strip()
            right_text = f"{right.cleaned_values.get('payee', '')} {right.cleaned_values.get('description', '')}".strip()
            similarity = text_similarity(left_text, right_text)

            if similarity >= 0.9:
                confidence = ConfidenceLevel.HIGH
            elif similarity >= 0.75:
                confidence = ConfidenceLevel.MEDIUM
            elif similarity >= 0.6:
                confidence = ConfidenceLevel.LOW
            else:
                continue

            groups.append(
                DuplicateGroup(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    row_indices=[left.row_index, right.row_index],
                    confidence=confidence,
                    match_type="near",
                    reason=f"Near duplicate match on same day and amount (similarity={similarity:.2f}).",
                )
            )
            used_rows.update({left.row_index, right.row_index})

    return groups
