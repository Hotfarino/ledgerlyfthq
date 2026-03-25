from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

from app.config import EXPORT_DIR
from services.repository import repository


class ExportService:
    def _rows_dataframe(self, job_id: str) -> pd.DataFrame:
        rows = repository.list_rows(job_id)
        records = []
        for row in sorted(rows, key=lambda item: item.source_row_index):
            records.append(
                {
                    "row_id": row.row_id,
                    "source_row_index": row.source_row_index,
                    "date": row.date,
                    "description": row.description,
                    "payee": row.payee,
                    "amount": row.amount,
                    "debit": row.debit,
                    "credit": row.credit,
                    "category": row.category,
                    "account": row.account,
                    "notes": row.notes,
                    "flags": ";".join(row.flags),
                    "review_status": row.review_status.value,
                    "category_suggestion": row.category_suggestion or "",
                    "category_confidence": row.category_confidence or "",
                    "cleaned_values_json": str(row.cleaned_values),
                    "original_values_json": str(row.original_values),
                }
            )
        return pd.DataFrame(records)

    def export_cleaned(self, job_id: str, file_type: Literal["csv", "xlsx"] = "csv") -> Path:
        df = self._rows_dataframe(job_id)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if file_type == "xlsx":
            output_path = EXPORT_DIR / f"{job_id}_cleaned_{timestamp}.xlsx"
            df.to_excel(output_path, index=False, engine="openpyxl")
        else:
            output_path = EXPORT_DIR / f"{job_id}_cleaned_{timestamp}.csv"
            df.to_csv(output_path, index=False)

        repository.set_last_export_time(job_id, datetime.utcnow())
        return output_path

    def export_exceptions(self, job_id: str) -> Path:
        exceptions = repository.list_exceptions(job_id)
        df = pd.DataFrame(
            [
                {
                    "id": item.id,
                    "job_id": item.job_id,
                    "row_id": item.row_id,
                    "source_row_index": item.source_row_index,
                    "flag_type": item.flag_type,
                    "severity": item.severity,
                    "message": item.message,
                    "reviewed": item.reviewed,
                }
                for item in exceptions
            ]
        )

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = EXPORT_DIR / f"{job_id}_exceptions_{timestamp}.csv"
        df.to_csv(output_path, index=False)
        repository.set_last_export_time(job_id, datetime.utcnow())
        return output_path

    def export_duplicates(self, job_id: str) -> Path:
        duplicates = repository.list_duplicates(job_id)
        df = pd.DataFrame(
            [
                {
                    "id": item.id,
                    "job_id": item.job_id,
                    "row_ids": ";".join(item.row_ids),
                    "source_row_indexes": ";".join(str(idx) for idx in item.source_row_indexes),
                    "confidence": item.confidence,
                    "match_type": item.match_type,
                    "reason": item.reason,
                    "reviewed": item.reviewed,
                }
                for item in duplicates
            ]
        )

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = EXPORT_DIR / f"{job_id}_duplicates_{timestamp}.csv"
        df.to_csv(output_path, index=False)
        repository.set_last_export_time(job_id, datetime.utcnow())
        return output_path

    def export_summary(self, job_id: str) -> Path:
        summary = repository.get_summary(job_id)
        if not summary:
            raise ValueError("Job summary not found")

        df = pd.DataFrame(
            [
                {
                    "job_id": summary.job_id,
                    "total_rows_imported": summary.total_rows_imported,
                    "rows_cleaned": summary.rows_cleaned,
                    "rows_flagged": summary.rows_flagged,
                    "suspected_duplicates_count": summary.suspected_duplicates_count,
                    "uncategorized_count": summary.uncategorized_count,
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "last_updated": summary.last_updated.isoformat()
                    if hasattr(summary.last_updated, "isoformat")
                    else summary.last_updated,
                }
            ]
        )

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = EXPORT_DIR / f"{job_id}_summary_{timestamp}.csv"
        df.to_csv(output_path, index=False)
        repository.set_last_export_time(job_id, datetime.utcnow())
        return output_path


export_service = ExportService()
