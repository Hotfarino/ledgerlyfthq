export type ConfidenceLevel = "high" | "medium" | "low";
export type ReviewStatus = "pending" | "reviewed" | "approved";

export interface UploadedFile {
  id: string;
  job_id: string;
  file_name: string;
  file_type: string;
  file_path: string;
  uploaded_at: string;
  row_count: number;
  column_mapping: Record<string, string>;
}

export interface TransactionRow {
  job_id: string;
  row_index: number;
  transaction_id?: string | null;
  original_values: Record<string, unknown>;
  cleaned_values: Record<string, unknown>;
  flags: string[];
  notes?: string | null;
  review_status: ReviewStatus;
  category_suggestion?: string | null;
  category_confidence?: ConfidenceLevel | null;
}

export interface ExceptionFlag {
  id: string;
  job_id: string;
  row_index: number;
  flag_type: string;
  severity: string;
  message: string;
  details: Record<string, unknown>;
  reviewed: boolean;
}

export interface DuplicateGroup {
  id: string;
  job_id: string;
  row_indices: number[];
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
  row_index?: number | null;
  field_name?: string | null;
  old_value?: string | null;
  new_value?: string | null;
  action: string;
  note?: string | null;
  created_at: string;
}

export interface ExportJobSummary {
  job_id: string;
  total_rows_imported: number;
  rows_cleaned: number;
  rows_flagged: number;
  suspected_duplicates_count: number;
  uncategorized_count: number;
  export_timestamp?: string | null;
  last_updated: string;
}

export interface UploadResponse {
  job_id: string;
  uploaded_file: UploadedFile;
  summary: ExportJobSummary;
  column_detection: {
    mapping: Record<string, string>;
    unmapped_headers: string[];
  };
}

export interface JobRecord {
  id: string;
  file_name: string;
  uploaded_at: string;
  row_count: number;
  summary: ExportJobSummary;
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
