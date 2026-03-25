from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import UploadFile

from app.config import UPLOAD_DIR
from models.schemas import (
    AuditEntry,
    CategoryRule,
    ExportJobSummary,
    TransactionRow,
    UploadedFile,
)
from parsers.file_parser import (
    dataframe_from_raw_json,
    dataframe_to_raw_json,
    detect_column_mapping,
    load_dataframe,
)
from services.category_assist import apply_category_rules
from services.duplicate_detector import detect_duplicates
from services.exception_detector import build_exceptions
from services.normalizer import normalize_rows
from services.repository import repository


class JobService:
    def __init__(self) -> None:
        repository.ensure_default_rules()

    def _build_summary(self, job_id: str, rows: List[TransactionRow], duplicate_count: int) -> ExportJobSummary:
        rows_flagged = sum(1 for row in rows if row.flags)
        uncategorized = sum(1 for row in rows if "uncategorized_transaction" in row.flags)
        return ExportJobSummary(
            job_id=job_id,
            total_rows_imported=len(rows),
            rows_cleaned=len(rows),
            rows_flagged=rows_flagged,
            suspected_duplicates_count=duplicate_count,
            uncategorized_count=uncategorized,
            last_updated=datetime.utcnow(),
        )

    async def handle_upload(self, file: UploadFile) -> tuple[str, UploadedFile, ExportJobSummary, dict[str, str], list[str]]:
        job_id = str(uuid.uuid4())
        suffix = Path(file.filename or "upload.csv").suffix.lower()
        safe_name = f"{job_id}{suffix if suffix else '.csv'}"
        output_path = UPLOAD_DIR / safe_name
        output_path.write_bytes(await file.read())

        df = load_dataframe(output_path)
        mapping, unmapped = detect_column_mapping(df)

        uploaded = UploadedFile(
            id=job_id,
            job_id=job_id,
            file_name=file.filename or safe_name,
            file_type=suffix or "csv",
            file_path=str(output_path),
            uploaded_at=datetime.utcnow(),
            row_count=len(df),
            column_mapping=mapping,
        )

        rows, summary = self._run_processing(job_id=job_id, df_json=dataframe_to_raw_json(df), mapping=mapping)

        repository.create_job(uploaded_file=uploaded, raw_df_json=dataframe_to_raw_json(df), summary=summary)
        repository.replace_rows(job_id, rows)

        return job_id, uploaded, summary, mapping, unmapped

    def _run_processing(self, job_id: str, df_json: str, mapping: Dict[str, str]) -> tuple[List[TransactionRow], ExportJobSummary]:
        df = dataframe_from_raw_json(df_json)
        normalized = normalize_rows(job_id=job_id, df=df, mapping=mapping)

        rules = repository.list_category_rules()
        rows = apply_category_rules(normalized.rows, rules=rules, preview_only=True)

        duplicates = detect_duplicates(job_id=job_id, rows=rows)
        duplicate_indices = {idx for group in duplicates for idx in group.row_indices}
        exceptions = build_exceptions(job_id=job_id, rows=rows, duplicate_row_indices=duplicate_indices)
        summary = self._build_summary(job_id, rows, duplicate_count=len(duplicates))

        audit_entries: List[AuditEntry] = [
            AuditEntry(
                id=str(uuid.uuid4()),
                job_id=job_id,
                row_index=entry["row_index"],
                field_name=entry["field_name"],
                old_value=entry["old_value"],
                new_value=entry["new_value"],
                action=entry["action"],
                note=entry["note"],
                created_at=datetime.utcnow(),
            )
            for entry in normalized.audit_entries
        ]

        audit_entries.append(
            AuditEntry(
                id=str(uuid.uuid4()),
                job_id=job_id,
                action="pipeline_run",
                note="Normalization, duplicate detection, and exception scan completed.",
                created_at=datetime.utcnow(),
            )
        )

        repository.replace_duplicates(job_id, duplicates)
        repository.replace_exceptions(job_id, exceptions)
        repository.replace_audit_entries(job_id, audit_entries)
        repository.update_job(job_id=job_id, column_mapping=mapping, summary=summary)

        return rows, summary

    def rerun_cleanup(self, job_id: str, column_mapping: Dict[str, str]) -> ExportJobSummary:
        job = repository.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        mapping = column_mapping or job["column_mapping"]
        rows, summary = self._run_processing(job_id=job_id, df_json=job["raw_df_json"], mapping=mapping)
        repository.replace_rows(job_id, rows)
        repository.update_job(job_id=job_id, column_mapping=mapping, summary=summary)

        repository.add_audit_entries(
            [
                AuditEntry(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    action="cleanup_rerun",
                    note="Cleanup rerun with updated column mapping.",
                    created_at=datetime.utcnow(),
                )
            ]
        )
        return summary

    def apply_category_rules(self, job_id: str, preview_only: bool = False) -> ExportJobSummary:
        rows = repository.list_rows(job_id)
        if not rows:
            raise ValueError("Job not found or no rows available")

        rules = repository.list_category_rules()
        updated_rows = apply_category_rules(rows, rules, preview_only=preview_only)
        repository.replace_rows(job_id, updated_rows)

        duplicates = repository.list_duplicates(job_id)
        summary = self._build_summary(job_id, updated_rows, duplicate_count=len(duplicates))
        repository.update_job(job_id=job_id, column_mapping=repository.get_job(job_id)["column_mapping"], summary=summary)

        repository.add_audit_entries(
            [
                AuditEntry(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    action="apply_category_rules",
                    note=f"Category rules {'previewed' if preview_only else 'applied'}.",
                    created_at=datetime.utcnow(),
                )
            ]
        )
        return summary

    def create_category_rule(
        self,
        name: str,
        target_field: str,
        contains_text: str,
        suggested_category: str,
        confidence: str,
        active: bool,
    ) -> CategoryRule:
        now = datetime.utcnow()
        rule = CategoryRule(
            id=str(uuid.uuid4()),
            name=name,
            target_field=target_field,
            contains_text=contains_text,
            suggested_category=suggested_category,
            confidence=confidence,
            active=active,
            created_at=now,
            updated_at=now,
        )
        repository.create_category_rule(rule)
        return rule


job_service = JobService()
