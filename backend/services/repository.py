from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from db.database import db
from models.schemas import (
    AuditEntry,
    CategoryRule,
    DuplicateGroup,
    ExceptionFlag,
    ExportSummary,
    JobPreview,
    ReviewStatus,
    TransactionRow,
    UploadJob,
)
from rules.default_rules import get_default_rules


class Repository:
    def list_jobs(self) -> List[dict[str, Any]]:
        with db.connection() as conn:
            rows = conn.execute(
                "SELECT id, file_name, uploaded_at, row_count, summary_json, last_export_at FROM jobs ORDER BY uploaded_at DESC"
            ).fetchall()
        return [
            {
                "job_id": row["id"],
                "file_name": row["file_name"],
                "uploaded_at": row["uploaded_at"],
                "row_count": row["row_count"],
                "summary": db.loads(row["summary_json"], {}),
                "last_export_at": row["last_export_at"],
            }
            for row in rows
        ]

    def create_job(
        self,
        upload_job: UploadJob,
        preview_rows: List[dict],
        raw_df_json: str,
        summary: ExportSummary,
    ) -> None:
        with db.connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    id, file_name, file_type, file_path, uploaded_at, row_count,
                    source_headers_json, column_mapping_json, preview_rows_json, summary_json, raw_df_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    upload_job.job_id,
                    upload_job.file_name,
                    upload_job.file_type,
                    upload_job.file_path,
                    upload_job.uploaded_at.isoformat(),
                    upload_job.row_count,
                    db.dumps(upload_job.source_headers),
                    db.dumps(upload_job.column_mapping),
                    db.dumps(preview_rows),
                    db.dumps(summary.model_dump(mode="json")),
                    raw_df_json,
                ),
            )

    def update_job(
        self,
        job_id: str,
        column_mapping: Dict[str, str],
        summary: ExportSummary,
        preview_rows: Optional[List[dict]] = None,
        source_headers: Optional[List[str]] = None,
    ) -> None:
        with db.connection() as conn:
            if preview_rows is None and source_headers is None:
                conn.execute(
                    "UPDATE jobs SET column_mapping_json = ?, summary_json = ? WHERE id = ?",
                    (db.dumps(column_mapping), db.dumps(summary.model_dump(mode="json")), job_id),
                )
                return

            row = conn.execute("SELECT source_headers_json, preview_rows_json FROM jobs WHERE id = ?", (job_id,)).fetchone()
            current_headers = db.loads(row["source_headers_json"], []) if row else []
            current_preview = db.loads(row["preview_rows_json"], []) if row else []
            conn.execute(
                """
                UPDATE jobs
                SET column_mapping_json = ?, summary_json = ?, source_headers_json = ?, preview_rows_json = ?
                WHERE id = ?
                """,
                (
                    db.dumps(column_mapping),
                    db.dumps(summary.model_dump(mode="json")),
                    db.dumps(source_headers if source_headers is not None else current_headers),
                    db.dumps(preview_rows if preview_rows is not None else current_preview),
                    job_id,
                ),
            )

    def get_job(self, job_id: str) -> Optional[dict[str, Any]]:
        with db.connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None

        return {
            "job_id": row["id"],
            "file_name": row["file_name"],
            "file_type": row["file_type"],
            "file_path": row["file_path"],
            "uploaded_at": row["uploaded_at"],
            "row_count": row["row_count"],
            "source_headers": db.loads(row["source_headers_json"], []),
            "column_mapping": db.loads(row["column_mapping_json"], {}),
            "preview_rows": db.loads(row["preview_rows_json"], []),
            "summary": db.loads(row["summary_json"], {}),
            "raw_df_json": row["raw_df_json"],
            "last_export_at": row["last_export_at"],
        }

    def get_upload_job(self, job_id: str) -> Optional[UploadJob]:
        payload = self.get_job(job_id)
        if not payload:
            return None
        return UploadJob(
            job_id=payload["job_id"],
            file_name=payload["file_name"],
            file_type=payload["file_type"],
            file_path=payload["file_path"],
            uploaded_at=datetime.fromisoformat(payload["uploaded_at"]),
            row_count=payload["row_count"],
            source_headers=payload["source_headers"],
            column_mapping=payload["column_mapping"],
        )

    def get_preview(self, job_id: str) -> Optional[JobPreview]:
        payload = self.get_job(job_id)
        if not payload:
            return None
        return JobPreview(
            job_id=job_id,
            source_headers=payload["source_headers"],
            column_mapping=payload["column_mapping"],
            preview_rows=payload["preview_rows"],
        )

    def get_summary(self, job_id: str) -> Optional[ExportSummary]:
        payload = self.get_job(job_id)
        if not payload:
            return None
        return ExportSummary(**payload["summary"])

    def set_last_export_time(self, job_id: str, exported_at: datetime) -> None:
        with db.connection() as conn:
            conn.execute("UPDATE jobs SET last_export_at = ? WHERE id = ?", (exported_at.isoformat(), job_id))
            row = conn.execute("SELECT summary_json FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return
            summary = db.loads(row["summary_json"], {})
            summary["export_timestamp"] = exported_at.isoformat()
            summary["last_updated"] = exported_at.isoformat()
            conn.execute("UPDATE jobs SET summary_json = ? WHERE id = ?", (db.dumps(summary), job_id))

    def replace_rows(self, job_id: str, rows: List[TransactionRow]) -> None:
        with db.connection() as conn:
            conn.execute("DELETE FROM rows WHERE job_id = ?", (job_id,))
            conn.executemany(
                """
                INSERT INTO rows (
                    job_id, row_id, source_row_index, date, description, payee,
                    amount, debit, credit, category, account, notes, flags_json,
                    cleaned_json, original_json, review_status, category_suggestion, category_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.job_id,
                        row.row_id,
                        row.source_row_index,
                        row.date,
                        row.description,
                        row.payee,
                        row.amount,
                        row.debit,
                        row.credit,
                        row.category,
                        row.account,
                        row.notes,
                        db.dumps(row.flags),
                        db.dumps(row.cleaned_values),
                        db.dumps(row.original_values),
                        row.review_status.value,
                        row.category_suggestion,
                        row.category_confidence.value if row.category_confidence else None,
                    )
                    for row in rows
                ],
            )

    def list_rows(self, job_id: str) -> List[TransactionRow]:
        with db.connection() as conn:
            rows = conn.execute("SELECT * FROM rows WHERE job_id = ? ORDER BY source_row_index ASC", (job_id,)).fetchall()

        output: List[TransactionRow] = []
        for row in rows:
            status = row["review_status"] if row["review_status"] in {"pending", "reviewed", "approved"} else "pending"
            output.append(
                TransactionRow(
                    row_id=row["row_id"],
                    job_id=row["job_id"],
                    source_row_index=row["source_row_index"],
                    date=row["date"] or "",
                    description=row["description"] or "",
                    payee=row["payee"] or "",
                    amount=row["amount"],
                    debit=row["debit"],
                    credit=row["credit"],
                    category=row["category"] or "",
                    account=row["account"] or "",
                    notes=row["notes"] or "",
                    flags=db.loads(row["flags_json"], []),
                    cleaned_values=db.loads(row["cleaned_json"], {}),
                    original_values=db.loads(row["original_json"], {}),
                    review_status=ReviewStatus(status),
                    category_suggestion=row["category_suggestion"],
                    category_confidence=row["category_confidence"],
                )
            )
        return output

    def replace_exceptions(self, job_id: str, exceptions: List[ExceptionFlag]) -> None:
        with db.connection() as conn:
            conn.execute("DELETE FROM exceptions WHERE job_id = ?", (job_id,))
            conn.executemany(
                """
                INSERT INTO exceptions (id, job_id, row_id, source_row_index, flag_type, severity, message, details_json, reviewed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.id,
                        item.job_id,
                        item.row_id,
                        item.source_row_index,
                        item.flag_type,
                        item.severity,
                        item.message,
                        db.dumps(item.details),
                        1 if item.reviewed else 0,
                    )
                    for item in exceptions
                ],
            )

    def list_exceptions(self, job_id: str) -> List[ExceptionFlag]:
        with db.connection() as conn:
            rows = conn.execute("SELECT * FROM exceptions WHERE job_id = ? ORDER BY source_row_index ASC", (job_id,)).fetchall()

        return [
            ExceptionFlag(
                id=row["id"],
                job_id=row["job_id"],
                row_id=row["row_id"],
                source_row_index=row["source_row_index"],
                flag_type=row["flag_type"],
                severity=row["severity"],
                message=row["message"],
                details=db.loads(row["details_json"], {}),
                reviewed=bool(row["reviewed"]),
            )
            for row in rows
        ]

    def replace_duplicates(self, job_id: str, duplicates: List[DuplicateGroup]) -> None:
        with db.connection() as conn:
            conn.execute("DELETE FROM duplicates WHERE job_id = ?", (job_id,))
            conn.executemany(
                """
                INSERT INTO duplicates (id, job_id, row_ids_json, source_row_indexes_json, confidence, match_type, reason, reviewed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.id,
                        item.job_id,
                        db.dumps(item.row_ids),
                        db.dumps(item.source_row_indexes),
                        item.confidence.value,
                        item.match_type,
                        item.reason,
                        1 if item.reviewed else 0,
                    )
                    for item in duplicates
                ],
            )

    def list_duplicates(self, job_id: str) -> List[DuplicateGroup]:
        with db.connection() as conn:
            rows = conn.execute("SELECT * FROM duplicates WHERE job_id = ? ORDER BY id ASC", (job_id,)).fetchall()

        return [
            DuplicateGroup(
                id=row["id"],
                job_id=row["job_id"],
                row_ids=db.loads(row["row_ids_json"], []),
                source_row_indexes=db.loads(row["source_row_indexes_json"], []),
                confidence=row["confidence"],
                match_type=row["match_type"],
                reason=row["reason"],
                reviewed=bool(row["reviewed"]),
            )
            for row in rows
        ]

    def replace_audit_entries(self, job_id: str, entries: List[AuditEntry]) -> None:
        with db.connection() as conn:
            conn.execute("DELETE FROM audit_entries WHERE job_id = ?", (job_id,))
            conn.executemany(
                """
                INSERT INTO audit_entries (id, job_id, row_id, source_row_index, field_name, old_value, new_value, action, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        entry.id,
                        entry.job_id,
                        entry.row_id,
                        entry.source_row_index,
                        entry.field_name,
                        entry.old_value,
                        entry.new_value,
                        entry.action,
                        entry.note,
                        entry.created_at.isoformat(),
                    )
                    for entry in entries
                ],
            )

    def add_audit_entries(self, entries: List[AuditEntry]) -> None:
        if not entries:
            return
        with db.connection() as conn:
            conn.executemany(
                """
                INSERT INTO audit_entries (id, job_id, row_id, source_row_index, field_name, old_value, new_value, action, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        entry.id,
                        entry.job_id,
                        entry.row_id,
                        entry.source_row_index,
                        entry.field_name,
                        entry.old_value,
                        entry.new_value,
                        entry.action,
                        entry.note,
                        entry.created_at.isoformat(),
                    )
                    for entry in entries
                ],
            )

    def list_audit_entries(self, job_id: str) -> List[AuditEntry]:
        with db.connection() as conn:
            rows = conn.execute("SELECT * FROM audit_entries WHERE job_id = ? ORDER BY created_at DESC", (job_id,)).fetchall()

        return [
            AuditEntry(
                id=row["id"],
                job_id=row["job_id"],
                row_id=row["row_id"],
                source_row_index=row["source_row_index"],
                field_name=row["field_name"],
                old_value=row["old_value"],
                new_value=row["new_value"],
                action=row["action"],
                note=row["note"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def mark_reviewed(self, job_id: str, target: str, ids: List[str], status: ReviewStatus) -> int:
        with db.connection() as conn:
            if target == "rows":
                if not ids:
                    cursor = conn.execute("UPDATE rows SET review_status = ? WHERE job_id = ?", (status.value, job_id))
                else:
                    placeholders = ",".join("?" for _ in ids)
                    cursor = conn.execute(
                        f"UPDATE rows SET review_status = ? WHERE job_id = ? AND row_id IN ({placeholders})",
                        [status.value, job_id, *ids],
                    )
                return cursor.rowcount

            table = "exceptions" if target == "exceptions" else "duplicates"
            if not ids:
                cursor = conn.execute(f"UPDATE {table} SET reviewed = 1 WHERE job_id = ?", (job_id,))
                return cursor.rowcount

            placeholders = ",".join("?" for _ in ids)
            cursor = conn.execute(
                f"UPDATE {table} SET reviewed = 1 WHERE job_id = ? AND id IN ({placeholders})",
                [job_id, *ids],
            )
            return cursor.rowcount

    def ensure_default_rules(self) -> None:
        with db.connection() as conn:
            count = conn.execute("SELECT COUNT(*) as c FROM category_rules").fetchone()["c"]
            if count > 0:
                return
            defaults = get_default_rules()
            conn.executemany(
                """
                INSERT INTO category_rules (id, name, target_field, contains_text, suggested_category, confidence, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        rule.id,
                        rule.name,
                        rule.target_field,
                        rule.contains_text,
                        rule.suggested_category,
                        rule.confidence.value,
                        1 if rule.active else 0,
                        rule.created_at.isoformat(),
                        rule.updated_at.isoformat(),
                    )
                    for rule in defaults
                ],
            )

    def list_category_rules(self) -> List[CategoryRule]:
        with db.connection() as conn:
            rows = conn.execute("SELECT * FROM category_rules ORDER BY created_at ASC").fetchall()
        return [
            CategoryRule(
                id=row["id"],
                name=row["name"],
                target_field=row["target_field"],
                contains_text=row["contains_text"],
                suggested_category=row["suggested_category"],
                confidence=row["confidence"],
                active=bool(row["active"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    def create_category_rule(self, rule: CategoryRule) -> None:
        with db.connection() as conn:
            conn.execute(
                """
                INSERT INTO category_rules (id, name, target_field, contains_text, suggested_category, confidence, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule.id,
                    rule.name,
                    rule.target_field,
                    rule.contains_text,
                    rule.suggested_category,
                    rule.confidence.value,
                    1 if rule.active else 0,
                    rule.created_at.isoformat(),
                    rule.updated_at.isoformat(),
                ),
            )


repository = Repository()
