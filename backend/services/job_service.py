from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from fastapi import UploadFile

from app.config import UPLOAD_DIR
from models.schemas import (
    AuditEntry,
    CategoryRule,
    ExportSummary,
    JobPreview,
    TransactionRow,
    UploadJob,
)
from parsers.file_parser import (
    build_preview_rows,
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

    def _build_summary(self, job_id: str, rows: List[TransactionRow], duplicate_count: int) -> ExportSummary:
        rows_flagged = sum(1 for row in rows if row.flags)
        uncategorized = sum(1 for row in rows if "uncategorized_transaction" in row.flags)
        return ExportSummary(
            job_id=job_id,
            total_rows_imported=len(rows),
            rows_cleaned=len(rows),
            rows_flagged=rows_flagged,
            suspected_duplicates_count=duplicate_count,
            uncategorized_count=uncategorized,
            last_updated=datetime.utcnow(),
        )

    async def handle_upload(self, file: UploadFile) -> tuple[UploadJob, ExportSummary, JobPreview]:
        job_id = str(uuid.uuid4())
        suffix = Path(file.filename or "upload.csv").suffix.lower() or ".csv"
        safe_file_name = f"{job_id}{suffix}"
        output_path = UPLOAD_DIR / safe_file_name

        content = await file.read()
        if not content:
            raise ValueError("Uploaded file is empty.")
        output_path.write_bytes(content)

        df = load_dataframe(output_path)
        mapping, _ = detect_column_mapping(df)
        preview_rows = build_preview_rows(df)
        source_headers = [str(column) for column in df.columns]

        upload_job = UploadJob(
            job_id=job_id,
            file_name=file.filename or safe_file_name,
            file_type=suffix,
            file_path=str(output_path),
            uploaded_at=datetime.utcnow(),
            row_count=len(df),
            source_headers=source_headers,
            column_mapping=mapping,
        )

        raw_df_json = dataframe_to_raw_json(df)
        rows, summary = self._run_processing(job_id=job_id, raw_df_json=raw_df_json, mapping=mapping)

        repository.create_job(upload_job=upload_job, preview_rows=preview_rows, raw_df_json=raw_df_json, summary=summary)
        repository.replace_rows(job_id=job_id, rows=rows)

        preview = JobPreview(
            job_id=job_id,
            source_headers=source_headers,
            column_mapping=mapping,
            preview_rows=preview_rows,
        )
        return upload_job, summary, preview

    def _run_processing(self, job_id: str, raw_df_json: str, mapping: Dict[str, str]) -> tuple[List[TransactionRow], ExportSummary]:
        df = dataframe_from_raw_json(raw_df_json)
        normalized = normalize_rows(job_id=job_id, df=df, mapping=mapping)

        rules = repository.list_category_rules()
        rows = apply_category_rules(normalized.rows, rules=rules, preview_only=True)

        duplicates = detect_duplicates(job_id=job_id, rows=rows)
        duplicate_row_ids = {row_id for group in duplicates for row_id in group.row_ids}
        exceptions = build_exceptions(job_id=job_id, rows=rows, duplicate_row_ids=duplicate_row_ids)
        summary = self._build_summary(job_id, rows, duplicate_count=len(duplicates))

        audit_entries: List[AuditEntry] = [
            AuditEntry(
                id=str(uuid.uuid4()),
                job_id=job_id,
                row_id=entry["row_id"],
                source_row_index=entry["source_row_index"],
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
                note="Normalization, exception scan, and duplicate detection completed.",
                created_at=datetime.utcnow(),
            )
        )

        repository.replace_duplicates(job_id, duplicates)
        repository.replace_exceptions(job_id, exceptions)
        repository.replace_audit_entries(job_id, audit_entries)
        repository.update_job(job_id=job_id, column_mapping=mapping, summary=summary)

        return rows, summary

    def rerun_cleanup(self, job_id: str, column_mapping: Dict[str, str]) -> ExportSummary:
        job = repository.get_job(job_id)
        if not job:
            raise ValueError("Job not found")

        mapping = column_mapping or job["column_mapping"]
        rows, summary = self._run_processing(job_id=job_id, raw_df_json=job["raw_df_json"], mapping=mapping)

        repository.replace_rows(job_id=job_id, rows=rows)
        repository.update_job(job_id=job_id, column_mapping=mapping, summary=summary)
        repository.add_audit_entries(
            [
                AuditEntry(
                    id=str(uuid.uuid4()),
                    job_id=job_id,
                    action="cleanup_rerun",
                    note="Cleanup re-run with updated column mapping.",
                    created_at=datetime.utcnow(),
                )
            ]
        )

        return summary

    def apply_category_rules(self, job_id: str, preview_only: bool = False) -> ExportSummary:
        rows = repository.list_rows(job_id)
        if not rows:
            raise ValueError("Job not found or no rows available")

        rules = repository.list_category_rules()
        updated_rows = apply_category_rules(rows=rows, rules=rules, preview_only=preview_only)
        repository.replace_rows(job_id=job_id, rows=updated_rows)

        duplicate_count = len(repository.list_duplicates(job_id))
        summary = self._build_summary(job_id, updated_rows, duplicate_count)
        job = repository.get_job(job_id)
        repository.update_job(job_id=job_id, column_mapping=job["column_mapping"], summary=summary)
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
