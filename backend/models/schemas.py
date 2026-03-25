from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExecutionMode(str, Enum):
    ISOLATED = "isolated"
    SHARED_ADAPTER = "shared_adapter"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class UploadJob(BaseModel):
    job_id: str
    file_name: str
    file_type: str
    file_path: str
    uploaded_at: datetime
    row_count: int
    source_headers: List[str] = Field(default_factory=list)
    column_mapping: Dict[str, str] = Field(default_factory=dict)


class TransactionRow(BaseModel):
    row_id: str
    job_id: str
    source_row_index: int
    date: Optional[str] = ""
    description: Optional[str] = ""
    payee: Optional[str] = ""
    amount: Optional[float] = None
    debit: Optional[float] = None
    credit: Optional[float] = None
    category: Optional[str] = ""
    account: Optional[str] = ""
    notes: Optional[str] = ""
    flags: List[str] = Field(default_factory=list)
    cleaned_values: Dict[str, Any] = Field(default_factory=dict)
    original_values: Dict[str, Any] = Field(default_factory=dict)
    review_status: ReviewStatus = ReviewStatus.PENDING
    category_suggestion: Optional[str] = None
    category_confidence: Optional[ConfidenceLevel] = None


class ExceptionFlag(BaseModel):
    id: str
    job_id: str
    row_id: str
    source_row_index: int
    flag_type: str
    severity: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    reviewed: bool = False


class DuplicateGroup(BaseModel):
    id: str
    job_id: str
    row_ids: List[str] = Field(default_factory=list)
    source_row_indexes: List[int] = Field(default_factory=list)
    confidence: ConfidenceLevel
    match_type: str
    reason: str
    reviewed: bool = False


class CategoryRule(BaseModel):
    id: str
    name: str
    target_field: str
    contains_text: str
    suggested_category: str
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    active: bool = True
    created_at: datetime
    updated_at: datetime


class AuditEntry(BaseModel):
    id: str
    job_id: str
    row_id: Optional[str] = None
    source_row_index: Optional[int] = None
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    action: str
    note: Optional[str] = None
    created_at: datetime


class ExportSummary(BaseModel):
    job_id: str
    total_rows_imported: int
    rows_cleaned: int
    rows_flagged: int
    suspected_duplicates_count: int
    uncategorized_count: int
    export_timestamp: Optional[datetime] = None
    last_updated: datetime


class JobPreview(BaseModel):
    job_id: str
    source_headers: List[str] = Field(default_factory=list)
    column_mapping: Dict[str, str] = Field(default_factory=dict)
    preview_rows: List[Dict[str, Any]] = Field(default_factory=list)


class UploadResponse(BaseModel):
    job: UploadJob
    summary: ExportSummary
    preview: JobPreview


class JobsResponse(BaseModel):
    jobs: List[Dict[str, Any]]


class ApplyCleanupRequest(BaseModel):
    column_mapping: Dict[str, str] = Field(default_factory=dict)
    execution_mode: ExecutionMode = ExecutionMode.ISOLATED


class ApplyCategoryRulesRequest(BaseModel):
    preview_only: bool = False
    execution_mode: ExecutionMode = ExecutionMode.ISOLATED


class MarkReviewedRequest(BaseModel):
    target: str
    ids: List[str] = Field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.REVIEWED


class CategoryRuleCreateRequest(BaseModel):
    name: str
    target_field: str = "payee"
    contains_text: str
    suggested_category: str
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    active: bool = True


class JobRowsResponse(BaseModel):
    job_id: str
    rows: List[TransactionRow]


class ExceptionsResponse(BaseModel):
    job_id: str
    exceptions: List[ExceptionFlag]


class DuplicatesResponse(BaseModel):
    job_id: str
    duplicates: List[DuplicateGroup]


class SuggestionsResponse(BaseModel):
    job_id: str
    rows: List[TransactionRow]


class AuditResponse(BaseModel):
    job_id: str
    entries: List[AuditEntry]


class ExecutionGuardrails(BaseModel):
    default_mode: ExecutionMode
    shared_adapter_enabled: bool
    allow_legacy_live_send_reuse: bool = False
    policy_note: str


class Phase0PainPoint(BaseModel):
    key: str
    label: str
    count: int
    percent_of_signals: float


class Phase0Report(BaseModel):
    lookback_days: int
    generated_at: datetime
    jobs_analyzed: int
    rows_analyzed: int
    signals_total: int
    top_pain_area: str
    pain_points: List[Phase0PainPoint] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
