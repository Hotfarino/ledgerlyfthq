import {
  AuditEntry,
  CategoryRule,
  DashboardMetrics,
  DuplicateGroup,
  ExceptionFlag,
  ExportSummary,
  JobPreview,
  JobRecord,
  TransactionRow,
  UploadResponse
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers || {})
    },
    cache: "no-store"
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const payload = await res.json();
      message = payload.detail || message;
    } catch {
      // no-op
    }
    throw new Error(message);
  }

  return res.json() as Promise<T>;
}

export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  return request<DashboardMetrics>("/dashboard/metrics");
}

export async function fetchJobs(): Promise<JobRecord[]> {
  const payload = await request<{ jobs: JobRecord[] }>("/jobs");
  return payload.jobs;
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return request<UploadResponse>("/upload", {
    method: "POST",
    body: formData
  });
}

export async function fetchJobPreview(jobId: string): Promise<JobPreview> {
  return request<JobPreview>(`/jobs/${jobId}/preview`);
}

export async function fetchSummary(jobId: string): Promise<ExportSummary> {
  return request<ExportSummary>(`/jobs/${jobId}/summary`);
}

export async function fetchRows(
  jobId: string,
  filters?: { search?: string; category?: string; flag?: string }
): Promise<TransactionRow[]> {
  const query = new URLSearchParams();
  if (filters?.search) query.set("search", filters.search);
  if (filters?.category) query.set("category", filters.category);
  if (filters?.flag) query.set("flag", filters.flag);

  const suffix = query.toString() ? `?${query.toString()}` : "";
  const payload = await request<{ job_id: string; rows: TransactionRow[] }>(`/jobs/${jobId}/rows${suffix}`);
  return payload.rows;
}

export async function fetchExceptions(jobId: string): Promise<ExceptionFlag[]> {
  const payload = await request<{ job_id: string; exceptions: ExceptionFlag[] }>(`/jobs/${jobId}/exceptions`);
  return payload.exceptions;
}

export async function fetchDuplicates(jobId: string): Promise<DuplicateGroup[]> {
  const payload = await request<{ job_id: string; duplicates: DuplicateGroup[] }>(`/jobs/${jobId}/duplicates`);
  return payload.duplicates;
}

export async function fetchSuggestions(jobId: string): Promise<TransactionRow[]> {
  const payload = await request<{ job_id: string; rows: TransactionRow[] }>(`/jobs/${jobId}/suggestions`);
  return payload.rows;
}

export async function fetchAuditLog(jobId: string): Promise<AuditEntry[]> {
  const payload = await request<{ job_id: string; entries: AuditEntry[] }>(`/jobs/${jobId}/audit-log`);
  return payload.entries;
}

export async function applyCleanup(jobId: string, columnMapping: Record<string, string>): Promise<ExportSummary> {
  const payload = await request<{ job_id: string; summary: ExportSummary }>(`/jobs/${jobId}/apply-cleanup`, {
    method: "POST",
    body: JSON.stringify({ column_mapping: columnMapping })
  });
  return payload.summary;
}

export async function applyCategoryRules(jobId: string, previewOnly = false): Promise<ExportSummary> {
  const payload = await request<{ job_id: string; summary: ExportSummary }>(`/jobs/${jobId}/apply-category-rules`, {
    method: "POST",
    body: JSON.stringify({ preview_only: previewOnly })
  });
  return payload.summary;
}

export async function markReviewed(
  jobId: string,
  target: "rows" | "exceptions" | "duplicates",
  ids: string[]
): Promise<{ updated: number }> {
  return request<{ updated: number }>(`/jobs/${jobId}/mark-reviewed`, {
    method: "POST",
    body: JSON.stringify({
      target,
      ids,
      review_status: "reviewed"
    })
  });
}

export async function fetchCategoryRules(): Promise<CategoryRule[]> {
  return request<CategoryRule[]>("/category-rules");
}

export async function createCategoryRule(payload: {
  name: string;
  target_field: string;
  contains_text: string;
  suggested_category: string;
  confidence: "high" | "medium" | "low";
  active: boolean;
}): Promise<CategoryRule> {
  return request<CategoryRule>("/category-rules", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getExportUrl(
  jobId: string,
  kind: "cleaned" | "exceptions" | "duplicates" | "summary",
  fileType?: "csv" | "xlsx"
): string {
  if (kind === "cleaned") {
    const query = fileType ? `?file_type=${fileType}` : "";
    return `${API_BASE}/jobs/${jobId}/export/cleaned${query}`;
  }
  return `${API_BASE}/jobs/${jobId}/export/${kind}`;
}
