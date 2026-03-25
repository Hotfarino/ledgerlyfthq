from __future__ import annotations

import uuid
from collections import defaultdict
from typing import List

from models.schemas import ConfidenceLevel, DuplicateGroup, TransactionRow
from services.normalizer import text_similarity


def detect_duplicates(job_id: str, rows: List[TransactionRow]) -> List[DuplicateGroup]:
    groups: List[DuplicateGroup] = []
    used_row_ids: set[str] = set()

    exact_map = defaultdict(list)
    for row in rows:
        key = (
            row.date or "",
            row.amount,
            (row.payee or "").lower(),
            (row.description or "").lower(),
        )
        exact_map[key].append(row)

    for candidate_rows in exact_map.values():
        if len(candidate_rows) <= 1:
            continue

        row_ids = [item.row_id for item in candidate_rows]
        source_indexes = [item.source_row_index for item in candidate_rows]
        groups.append(
            DuplicateGroup(
                id=str(uuid.uuid4()),
                job_id=job_id,
                row_ids=row_ids,
                source_row_indexes=source_indexes,
                confidence=ConfidenceLevel.HIGH,
                match_type="exact",
                reason="Rows share date, amount, payee, and description.",
            )
        )
        used_row_ids.update(row_ids)

    candidates = [row for row in rows if row.row_id not in used_row_ids]
    for index, left in enumerate(candidates):
        for right in candidates[index + 1 :]:
            if left.row_id in used_row_ids or right.row_id in used_row_ids:
                continue
            if not left.date or left.date != right.date:
                continue
            if left.amount is None or right.amount is None:
                continue
            if abs(left.amount - right.amount) > 0.01:
                continue

            left_text = f"{left.payee or ''} {left.description or ''}".strip()
            right_text = f"{right.payee or ''} {right.description or ''}".strip()
            similarity = text_similarity(left_text, right_text)

            if similarity >= 0.9:
                confidence = ConfidenceLevel.HIGH
            elif similarity >= 0.75:
                confidence = ConfidenceLevel.MEDIUM
            elif similarity >= 0.65:
                confidence = ConfidenceLevel.LOW
            else:
                continue

            groups.append(
                DuplicateGroup(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    row_ids=[left.row_id, right.row_id],
                    source_row_indexes=[left.source_row_index, right.source_row_index],
                    confidence=confidence,
                    match_type="likely",
                    reason=f"Likely duplicate on same date/amount (text similarity {similarity:.2f}).",
                )
            )
            used_row_ids.update({left.row_id, right.row_id})

    return groups
