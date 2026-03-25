export type ConfidenceLevel = "high" | "medium" | "low";
export type ReviewStatus = "pending" | "reviewed" | "approved";
export type ExecutionMode = "isolated" | "shared_adapter";

export interface UploadJob {
  job_id: string;
  file_name: string;
  file_type: string;
  file_path: string;
  uploaded_at: string;
  row_count: number;
  source_headers: string[];
  column_mapping: Record<string, string>;
}

export interface TransactionRow {
  row_id: string;
  job_id: string;
  source_row_index: number;
  date?: string;
  description?: string;
  payee?: string;
  amount?: number | null;
  debit?: number | null;
  credit?: number | null;
  category?: string;
  account?: string;
  notes?: string;
  flags: string[];
  cleaned_values: Record<string, unknown>;
  original_values: Record<string, unknown>;
  review_status: ReviewStatus;
  category_suggestion?: string | null;
  category_confidence?: ConfidenceLevel | null;
}

export interface ExceptionFlag {
  id: string;
  job_id: string;
  row_id: string;
  source_row_index: number;
  flag_type: string;
  severity: string;
  message: string;
  details: Record<string, unknown>;
  reviewed: boolean;
}

export interface DuplicateGroup {
  id: string;
  job_id: string;
  row_ids: string[];
  source_row_indexes: number[];
  confidence: ConfidenceLevel;
  match_type: string;
  reason: string;
  reviewed: boolean;
}

export interface CategoryRule {
  id: string;
  name: string;
  target_field: string;
  contains_text: string;
  suggested_category: string;
  confidence: ConfidenceLevel;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuditEntry {
  id: string;
  job_id: string;
  row_id?: string | null;
  source_row_index?: number | null;
  field_name?: string | null;
  old_value?: string | null;
  new_value?: string | null;
  action: string;
  note?: string | null;
  created_at: string;
}

export interface ExportSummary {
  job_id: string;
  total_rows_imported: number;
  rows_cleaned: number;
  rows_flagged: number;
  suspected_duplicates_count: number;
  uncategorized_count: number;
  export_timestamp?: string | null;
  last_updated: string;
}

export interface JobPreview {
  job_id: string;
  source_headers: string[];
  column_mapping: Record<string, string>;
  preview_rows: Record<string, unknown>[];
}

export interface UploadResponse {
  job: UploadJob;
  summary: ExportSummary;
  preview: JobPreview;
}

export interface JobRecord {
  job_id: string;
  file_name: string;
  uploaded_at: string;
  row_count: number;
  summary: ExportSummary;
  last_export_at?: string | null;
}

export interface DashboardMetrics {
  files_imported: number;
  rows_processed: number;
  duplicates_flagged: number;
  exceptions_flagged: number;
  uncategorized_transactions: number;
  last_export_time: string | null;
}

export interface ExecutionGuardrails {
  default_mode: ExecutionMode;
  shared_adapter_enabled: boolean;
  allow_legacy_live_send_reuse: boolean;
  policy_note: string;
}
