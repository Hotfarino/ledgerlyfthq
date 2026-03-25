"use client";

export const dynamic = "force-dynamic";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { JobPicker } from "@/components/job-picker";
import { PageTitle } from "@/components/page-title";
import { SectionCard } from "@/components/section-card";
import { uploadFile } from "@/lib/api";
import { UploadResponse } from "@/lib/types";
import { setActiveJobId } from "@/lib/use-active-job";

export default function ImportPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload() {
    if (!file) return;
    setError(null);
    setMessage(null);
    setUploading(true);
    try {
      const result = await uploadFile(file);
      setUploadResult(result);
      setActiveJobId(result.job.job_id);
      setMessage(`Imported ${result.job.row_count} rows. Active job set to ${result.job.job_id.slice(0, 12)}...`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  const previewRows = uploadResult?.preview.preview_rows ?? [];
  const previewHeaders = uploadResult?.preview.source_headers ?? [];

  return (
    <div>
      <PageTitle
        title="Import"
        subtitle="Upload CSV/XLSX files, validate headers, and preview rows before column mapping."
        actions={<JobPicker />}
      />

      <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
        <SectionCard title="Upload File">
          <p className="mb-3 text-sm text-muted">Supported formats: CSV and XLSX. Files stay local in Version 1.</p>
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
              {uploading ? "Uploading..." : "Upload & Preview"}
            </button>
            <button
              type="button"
              className="rounded-lg border border-line bg-white px-4 py-2 text-sm font-semibold disabled:opacity-50"
              disabled={!uploadResult}
              onClick={() => router.push("/column-mapping")}
            >
              Go To Column Mapping
            </button>
          </div>

          {message ? <p className="mt-3 rounded bg-emerald-100 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}
          {error ? <p className="mt-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        </SectionCard>

        <SectionCard title="Import Summary">
          {uploadResult ? (
            <ul className="space-y-2 text-sm text-muted">
              <li>Rows imported: {uploadResult.job.row_count}</li>
              <li>Rows flagged: {uploadResult.summary.rows_flagged}</li>
              <li>Duplicates flagged: {uploadResult.summary.suspected_duplicates_count}</li>
              <li>Uncategorized: {uploadResult.summary.uncategorized_count}</li>
            </ul>
          ) : (
            <p className="text-sm text-muted">No file uploaded yet.</p>
          )}
        </SectionCard>
      </div>

      <div className="mt-6">
        <SectionCard title="Preview Rows (First 20)">
          {previewRows.length === 0 ? (
            <EmptyState text="Upload a file to preview the first rows." />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    {previewHeaders.map((header) => (
                      <th key={header}>{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {previewRows.map((row, index) => (
                    <tr key={`preview-${index}`}>
                      {previewHeaders.map((header) => (
                        <td key={`preview-${index}-${header}`}>{String(row[header] ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
