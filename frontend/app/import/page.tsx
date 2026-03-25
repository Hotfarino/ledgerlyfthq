"use client";

export const dynamic = "force-dynamic";

import { useMemo, useState } from "react";

import { JobPicker } from "@/components/job-picker";
import { PageTitle } from "@/components/page-title";
import { SectionCard } from "@/components/section-card";
import { applyCleanup, uploadFile } from "@/lib/api";
import { CANONICAL_COLUMNS } from "@/lib/constants";
import { UploadResponse } from "@/lib/types";
import { setActiveJobId } from "@/lib/use-active-job";

export default function ImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [uploading, setUploading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const headers = useMemo(() => {
    if (!uploadResult) return [];
    const used = Object.values(uploadResult.column_detection.mapping);
    return Array.from(new Set([...used, ...uploadResult.column_detection.unmapped_headers]));
  }, [uploadResult]);

  async function handleUpload() {
    if (!file) return;
    setError(null);
    setMessage(null);
    setUploading(true);
    try {
      const result = await uploadFile(file);
      setUploadResult(result);
      setColumnMapping(result.column_detection.mapping);
      setMessage(`Imported ${result.uploaded_file.row_count} rows. Job ID: ${result.job_id.slice(0, 12)}...`);
      setActiveJobId(result.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleApplyCleanup() {
    if (!uploadResult) return;
    setApplying(true);
    setError(null);
    try {
      await applyCleanup(uploadResult.job_id, columnMapping);
      setMessage("Cleanup pipeline rerun with updated mapping.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not apply cleanup");
    } finally {
      setApplying(false);
    }
  }

  return (
    <div>
      <PageTitle
        title="Import"
        subtitle="Upload CSV/XLSX files, detect bookkeeping columns, and adjust mapping before cleanup rerun."
        actions={<JobPicker />}
      />

      <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
        <SectionCard title="Upload File">
          <p className="mb-3 text-sm text-muted">
            Supported formats: CSV and XLSX. All files remain local to your machine in Phase 1.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <input
              type="file"
              accept=".csv,.xlsx,.xlsm,.xltx,.xltm"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
              className="rounded-lg border border-line bg-white px-3 py-2 text-sm"
            />
            <button
              type="button"
              className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              onClick={handleUpload}
              disabled={!file || uploading}
            >
              {uploading ? "Uploading..." : "Upload & Analyze"}
            </button>
          </div>

          {message ? <p className="mt-3 rounded bg-emerald-100 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}
          {error ? <p className="mt-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        </SectionCard>

        <SectionCard title="Import Notes">
          <ul className="space-y-2 text-sm text-muted">
            <li>Column detection is heuristic and should be reviewed before final export.</li>
            <li>Original raw values are always preserved for before/after auditability.</li>
            <li>Duplicates and category assignments are suggestions pending reviewer action.</li>
          </ul>
        </SectionCard>
      </div>

      {uploadResult ? (
        <SectionCard
          title="Column Mapping"
          right={
            <button
              type="button"
              className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              onClick={handleApplyCleanup}
              disabled={applying}
            >
              {applying ? "Applying..." : "Apply Mapping & Rerun Cleanup"}
            </button>
          }
        >
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {CANONICAL_COLUMNS.map((column) => (
              <label key={column} className="flex flex-col gap-1 text-sm">
                <span className="font-medium text-ink">{column}</span>
                <select
                  className="rounded-lg border border-line bg-white px-3 py-2"
                  value={columnMapping[column] || ""}
                  onChange={(event) =>
                    setColumnMapping((prev) => ({
                      ...prev,
                      [column]: event.target.value
                    }))
                  }
                >
                  <option value="">Unmapped</option>
                  {headers.map((header) => (
                    <option key={`${column}-${header}`} value={header}>
                      {header}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}
