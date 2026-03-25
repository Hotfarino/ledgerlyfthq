from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

from app.config import EXPORT_DIR
from services.repository import repository


class ExportService:
    def _cleaned_dataframe(self, job_id: str) -> pd.DataFrame:
        rows = repository.list_rows(job_id)
        records = []
        for row in rows:
            record = {
                "row_index": row.row_index,
                "review_status": row.review_status.value,
                "flags": ";".join(row.flags),
                "notes": row.notes or "",
                "category_suggestion": row.category_suggestion or "",
                "category_confidence": row.category_confidence or "",
            }
            for key, value in row.cleaned_values.items():
                record[f"cleaned_{key}"] = value
            for key, value in row.original_values.items():
                record[f"original_{key}"] = value
            records.append(record)
        return pd.DataFrame(records)

    def export_cleaned(self, job_id: str, file_type: Literal["csv", "xlsx"] = "csv") -> Path:
        df = self._cleaned_dataframe(job_id)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        if file_type == "xlsx":
            output = EXPORT_DIR / f"{job_id}_cleaned_{timestamp}.xlsx"
            df.to_excel(output, index=False, engine="openpyxl")
        else:
            output = EXPORT_DIR / f"{job_id}_cleaned_{timestamp}.csv"
            df.to_csv(output, index=False)
        repository.set_last_export_time(job_id, datetime.utcnow())
        return output

    def export_exceptions(self, job_id: str) -> Path:
        exceptions = repository.list_exceptions(job_id)
        rows = [
            {
                "id": item.id,
                "job_id": item.job_id,
                "row_index": item.row_index,
                "flag_type": item.flag_type,
                "severity": item.severity,
                "message": item.message,
                "reviewed": item.reviewed,
            }
            for item in exceptions
        ]
        df = pd.DataFrame(rows)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output = EXPORT_DIR / f"{job_id}_exceptions_{timestamp}.csv"
        df.to_csv(output, index=False)
        repository.set_last_export_time(job_id, datetime.utcnow())
        return output

    def export_duplicates(self, job_id: str) -> Path:
        duplicates = repository.list_duplicates(job_id)
        rows = [
            {
                "id": item.id,
                "job_id": item.job_id,
                "row_indices": ";".join(str(r) for r in item.row_indices),
                "confidence": item.confidence,
                "match_type": item.match_type,
                "reason": item.reason,
                "reviewed": item.reviewed,
            }
            for item in duplicates
        ]
        df = pd.DataFrame(rows)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output = EXPORT_DIR / f"{job_id}_duplicates_{timestamp}.csv"
        df.to_csv(output, index=False)
        repository.set_last_export_time(job_id, datetime.utcnow())
        return output

    def export_summary(self, job_id: str) -> Path:
        summary = repository.get_summary(job_id)
        if not summary:
            raise ValueError("Job summary not found")
        row = {
            "job_id": summary.job_id,
            "total_rows_imported": summary.total_rows_imported,
            "rows_cleaned": summary.rows_cleaned,
            "rows_flagged": summary.rows_flagged,
            "suspected_duplicates_count": summary.suspected_duplicates_count,
            "uncategorized_count": summary.uncategorized_count,
            "export_timestamp": datetime.utcnow().isoformat(),
            "last_updated": summary.last_updated.isoformat() if hasattr(summary.last_updated, "isoformat") else summary.last_updated,
        }
        df = pd.DataFrame([row])
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output = EXPORT_DIR / f"{job_id}_summary_{timestamp}.csv"
        df.to_csv(output, index=False)
        repository.set_last_export_time(job_id, datetime.utcnow())
        return output


export_service = ExportService()
