from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class UploadedFile(BaseModel):
    id: str
    job_id: str
    file_name: str
    file_type: str
    file_path: str
    uploaded_at: datetime
    row_count: int
    column_mapping: Dict[str, str] = Field(default_factory=dict)


class TransactionRow(BaseModel):
    job_id: str
    row_index: int
    transaction_id: Optional[str] = None
    original_values: Dict[str, Any] = Field(default_factory=dict)
    cleaned_values: Dict[str, Any] = Field(default_factory=dict)
    flags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.PENDING
    category_suggestion: Optional[str] = None
    category_confidence: Optional[ConfidenceLevel] = None


class ExceptionFlag(BaseModel):
    id: str
    job_id: str
    row_index: int
    flag_type: str
    severity: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    reviewed: bool = False


class DuplicateGroup(BaseModel):
    id: str
    job_id: str
    row_indices: List[int] = Field(default_factory=list)
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
    row_index: Optional[int] = None
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    action: str
    note: Optional[str] = None
    created_at: datetime


class ExportJobSummary(BaseModel):
    job_id: str
    total_rows_imported: int
    rows_cleaned: int
    rows_flagged: int
    suspected_duplicates_count: int
    uncategorized_count: int
    export_timestamp: Optional[datetime] = None
    last_updated: datetime


class ColumnDetectionResult(BaseModel):
    mapping: Dict[str, str] = Field(default_factory=dict)
    unmapped_headers: List[str] = Field(default_factory=list)


class UploadResponse(BaseModel):
    job_id: str
    uploaded_file: UploadedFile
    summary: ExportJobSummary
    column_detection: ColumnDetectionResult


class ApplyCleanupRequest(BaseModel):
    column_mapping: Dict[str, str] = Field(default_factory=dict)


class ApplyCategoryRulesRequest(BaseModel):
    preview_only: bool = False


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
