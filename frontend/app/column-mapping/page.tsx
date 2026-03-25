"use client";

export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { JobPicker } from "@/components/job-picker";
import { PageTitle } from "@/components/page-title";
import { SectionCard } from "@/components/section-card";
import { applyCleanup, fetchJobPreview } from "@/lib/api";
import { CANONICAL_COLUMNS } from "@/lib/constants";
import { JobPreview } from "@/lib/types";
import { useActiveJobId } from "@/lib/use-active-job";

function formatPreviewHeader(header: string): string {
  return header
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export default function ColumnMappingPage() {
  const router = useRouter();
  const [jobId] = useActiveJobId();

  const [preview, setPreview] = useState<JobPreview | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setPreview(null);
      setColumnMapping({});
      return;
    }

    setLoading(true);
    setError(null);
    fetchJobPreview(jobId)
      .then((payload) => {
        setPreview(payload);
        setColumnMapping(payload.column_mapping);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [jobId]);

  const headers = useMemo(() => preview?.source_headers ?? [], [preview]);

  async function handleApplyCleanup() {
    if (!jobId) return;

    setApplying(true);
    setMessage(null);
    setError(null);
    try {
      await applyCleanup(jobId, columnMapping);
      setMessage("Cleanup applied with latest column mapping.");
      router.push("/review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cleanup failed");
    } finally {
      setApplying(false);
    }
  }

  return (
    <div>
      <PageTitle
        title="Column Mapping"
        subtitle="Map imported headers to standard V1 row fields before cleaning and review."
        actions={<JobPicker />}
      />

      {error ? <p className="mb-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {message ? <p className="mb-3 rounded bg-emerald-100 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}

      {!jobId ? (
        <EmptyState text="Select a job first, or upload a file on the Import page." />
      ) : loading ? (
        <SectionCard title="Loading Mapping">
          <p className="text-sm text-muted">Loading source headers and mapping...</p>
        </SectionCard>
      ) : (
        <>
          <SectionCard
            title="Field Mapping"
            right={
              <button
                type="button"
                className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                onClick={handleApplyCleanup}
                disabled={applying}
              >
                {applying ? "Applying..." : "Apply Mapping & Clean"}
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

          <div className="mt-6">
            <SectionCard title="Source Preview Rows">
              {preview?.preview_rows.length ? (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        {headers.map((header) => (
                          <th key={header} title={header}>
                            {formatPreviewHeader(header)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {preview.preview_rows.map((row, index) => (
                        <tr key={`preview-${index}`}>
                          {headers.map((header) => (
                            <td key={`preview-${index}-${header}`}>{String(row[header] ?? "")}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState text="No preview rows available for this job." />
              )}
            </SectionCard>
          </div>
        </>
      )}
    </div>
  );
}
