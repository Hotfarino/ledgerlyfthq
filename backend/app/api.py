from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.config import DEFAULT_EXECUTION_MODE, ENABLE_SHARED_ADAPTER
from exporters.export_service import export_service
from models.schemas import (
    ApplyCategoryRulesRequest,
    ApplyCleanupRequest,
    AuditResponse,
    CategoryRule,
    CategoryRuleCreateRequest,
    DuplicatesResponse,
    ExecutionMode,
    ExecutionGuardrails,
    ExceptionsResponse,
    JobRowsResponse,
    JobsResponse,
    MarkReviewedRequest,
    SuggestionsResponse,
    UploadResponse,
)
from services.job_service import job_service
from services.repository import repository

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ledgerlyftHQ API"}


@router.get("/jobs", response_model=JobsResponse)
def list_jobs() -> JobsResponse:
    return JobsResponse(jobs=repository.list_jobs())


@router.get("/execution/guardrails", response_model=ExecutionGuardrails)
def execution_guardrails() -> ExecutionGuardrails:
    return ExecutionGuardrails(
        default_mode=ExecutionMode(DEFAULT_EXECUTION_MODE),
        shared_adapter_enabled=ENABLE_SHARED_ADAPTER,
        allow_legacy_live_send_reuse=False,
        policy_note=(
            "New execution paths stay isolated by default. "
            "Shared adapter use must be explicitly selected and mode-guarded."
        ),
    )


@router.get("/dashboard/metrics")
def dashboard_metrics() -> dict[str, int | str | None]:
    jobs = repository.list_jobs()

    files_imported = len(jobs)
    rows_processed = sum(int(job.get("row_count", 0)) for job in jobs)
    duplicates = 0
    exceptions = 0
    uncategorized = 0
    last_export_time = None

    for job in jobs:
        summary = job.get("summary", {})
        duplicates += int(summary.get("suspected_duplicates_count", 0))
        exceptions += int(summary.get("rows_flagged", 0))
        uncategorized += int(summary.get("uncategorized_count", 0))
        if job.get("last_export_at") and (not last_export_time or job["last_export_at"] > last_export_time):
            last_export_time = job["last_export_at"]

    return {
        "files_imported": files_imported,
        "rows_processed": rows_processed,
        "duplicates_flagged": duplicates,
        "exceptions_flagged": exceptions,
        "uncategorized_transactions": uncategorized,
        "last_export_time": last_export_time,
    }


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xlsm", ".xltx", ".xltm"}:
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported in V1")

    try:
        upload_job, summary, preview = await job_service.handle_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {exc}") from exc

    return UploadResponse(job=upload_job, summary=summary, preview=preview)


@router.get("/jobs/{job_id}/preview")
def get_preview(job_id: str):
    preview = repository.get_preview(job_id)
    if not preview:
        raise HTTPException(status_code=404, detail="Job not found")
    return preview


@router.get("/jobs/{job_id}/summary")
def get_summary(job_id: str):
    summary = repository.get_summary(job_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Job not found")
    return summary


@router.get("/jobs/{job_id}/rows", response_model=JobRowsResponse)
def get_rows(
    job_id: str,
    search: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    flag: Optional[str] = Query(default=None),
):
    rows = repository.list_rows(job_id)
    if not rows and not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    filtered = rows
    if search:
        needle = search.lower()
        filtered = [
            row
            for row in filtered
            if needle in (row.payee or "").lower()
            or needle in (row.description or "").lower()
            or needle in (row.date or "").lower()
            or needle in (row.category or "").lower()
            or needle in str(row.amount or "")
        ]
    if category:
        filtered = [row for row in filtered if (row.category or "").lower() == category.lower()]
    if flag:
        filtered = [row for row in filtered if flag in row.flags]

    return JobRowsResponse(job_id=job_id, rows=filtered)


@router.get("/jobs/{job_id}/exceptions", response_model=ExceptionsResponse)
def get_exceptions(job_id: str) -> ExceptionsResponse:
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return ExceptionsResponse(job_id=job_id, exceptions=repository.list_exceptions(job_id))


@router.get("/jobs/{job_id}/duplicates", response_model=DuplicatesResponse)
def get_duplicates(job_id: str) -> DuplicatesResponse:
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return DuplicatesResponse(job_id=job_id, duplicates=repository.list_duplicates(job_id))


@router.get("/jobs/{job_id}/suggestions", response_model=SuggestionsResponse)
def get_suggestions(job_id: str) -> SuggestionsResponse:
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    rows = [row for row in repository.list_rows(job_id) if row.category_suggestion]
    return SuggestionsResponse(job_id=job_id, rows=rows)


@router.post("/jobs/{job_id}/apply-cleanup")
def apply_cleanup(job_id: str, payload: ApplyCleanupRequest):
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        summary = job_service.rerun_cleanup(
            job_id,
            payload.column_mapping,
            execution_mode=payload.execution_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"job_id": job_id, "summary": summary}


@router.post("/jobs/{job_id}/apply-category-rules")
def apply_category_rules(job_id: str, payload: ApplyCategoryRulesRequest):
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        summary = job_service.apply_category_rules(
            job_id,
            preview_only=payload.preview_only,
            execution_mode=payload.execution_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"job_id": job_id, "summary": summary}


@router.post("/jobs/{job_id}/mark-reviewed")
def mark_reviewed(job_id: str, payload: MarkReviewedRequest):
    if payload.target not in {"rows", "exceptions", "duplicates"}:
        raise HTTPException(status_code=400, detail="target must be one of rows, exceptions, duplicates")
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    updated = repository.mark_reviewed(job_id, payload.target, payload.ids, payload.review_status)
    return {"job_id": job_id, "target": payload.target, "updated": updated}


@router.get("/jobs/{job_id}/audit-log", response_model=AuditResponse)
def get_audit_log(job_id: str) -> AuditResponse:
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return AuditResponse(job_id=job_id, entries=repository.list_audit_entries(job_id))


@router.get("/jobs/{job_id}/export/cleaned")
def export_cleaned(job_id: str, file_type: str = Query(default="csv")):
    if file_type not in {"csv", "xlsx"}:
        raise HTTPException(status_code=400, detail="file_type must be csv or xlsx")
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    path = export_service.export_cleaned(job_id, file_type=file_type)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if file_type == "xlsx" else "text/csv"
    return FileResponse(path=path, filename=path.name, media_type=media_type)


@router.get("/jobs/{job_id}/export/exceptions")
def export_exceptions(job_id: str):
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    path = export_service.export_exceptions(job_id)
    return FileResponse(path=path, filename=path.name, media_type="text/csv")


@router.get("/jobs/{job_id}/export/duplicates")
def export_duplicates(job_id: str):
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    path = export_service.export_duplicates(job_id)
    return FileResponse(path=path, filename=path.name, media_type="text/csv")


@router.get("/jobs/{job_id}/export/summary")
def export_summary(job_id: str):
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    path = export_service.export_summary(job_id)
    return FileResponse(path=path, filename=path.name, media_type="text/csv")


@router.get("/jobs/{job_id}/export/audit-log")
def export_audit_log(job_id: str):
    if not repository.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    path = export_service.export_audit_log(job_id)
    return FileResponse(path=path, filename=path.name, media_type="text/csv")


@router.get("/category-rules", response_model=list[CategoryRule])
def list_category_rules():
    return repository.list_category_rules()


@router.post("/category-rules", response_model=CategoryRule)
def create_category_rule(payload: CategoryRuleCreateRequest):
    return job_service.create_category_rule(
        name=payload.name,
        target_field=payload.target_field,
        contains_text=payload.contains_text,
        suggested_category=payload.suggested_category,
        confidence=payload.confidence,
        active=payload.active,
    )
