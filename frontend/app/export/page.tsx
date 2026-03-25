"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/empty-state";
import { JobPicker } from "@/components/job-picker";
import { PageTitle } from "@/components/page-title";
import { SectionCard } from "@/components/section-card";
import { fetchSummary, getExportUrl } from "@/lib/api";
import { ExportJobSummary } from "@/lib/types";
import { useActiveJobId } from "@/lib/use-active-job";

export default function ExportPage() {
  const [jobId] = useActiveJobId();

  const [summary, setSummary] = useState<ExportJobSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setSummary(null);
      return;
    }
    fetchSummary(jobId)
      .then((data) => {
        setSummary(data);
        setError(null);
      })
      .catch((err: Error) => {
        setSummary(null);
        setError(err.message);
      });
  }, [jobId]);

  function download(kind: "cleaned" | "exceptions" | "duplicates" | "summary", fileType?: "csv" | "xlsx") {
    if (!jobId) return;
    window.open(getExportUrl(jobId, kind, fileType), "_blank");
  }

  return (
    <div>
      <PageTitle
        title="Export"
        subtitle="Download cleaned data, exception and duplicate review reports, plus summary metrics."
        actions={<JobPicker />}
      />

      {error ? <p className="mb-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p> : null}

      {!jobId ? (
        <EmptyState text="Select a job to export files." />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
          <SectionCard title="Export Actions">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <button
                type="button"
                className="rounded-lg border border-line bg-white px-4 py-3 text-left text-sm font-semibold"
                onClick={() => download("cleaned", "csv")}
              >
                Export Cleaned CSV
              </button>
              <button
                type="button"
                className="rounded-lg border border-line bg-white px-4 py-3 text-left text-sm font-semibold"
                onClick={() => download("cleaned", "xlsx")}
              >
                Export Cleaned XLSX
              </button>
              <button
                type="button"
                className="rounded-lg border border-line bg-white px-4 py-3 text-left text-sm font-semibold"
                onClick={() => download("exceptions")}
              >
                Export Exception Report CSV
              </button>
              <button
                type="button"
                className="rounded-lg border border-line bg-white px-4 py-3 text-left text-sm font-semibold"
                onClick={() => download("duplicates")}
              >
                Export Duplicate Review CSV
              </button>
              <button
                type="button"
                className="rounded-lg border border-line bg-white px-4 py-3 text-left text-sm font-semibold md:col-span-2"
                onClick={() => download("summary")}
              >
                Export Summary Report CSV
              </button>
            </div>
          </SectionCard>

          <SectionCard title="Summary Snapshot">
            {summary ? (
              <ul className="space-y-2 text-sm">
                <li>Total rows imported: {summary.total_rows_imported}</li>
                <li>Rows cleaned: {summary.rows_cleaned}</li>
                <li>Rows flagged: {summary.rows_flagged}</li>
                <li>Suspected duplicates: {summary.suspected_duplicates_count}</li>
                <li>Uncategorized count: {summary.uncategorized_count}</li>
                <li>
                  Last updated: {summary.last_updated ? new Date(summary.last_updated).toLocaleString() : "-"}
                </li>
              </ul>
            ) : (
              <p className="text-sm text-muted">Summary is not available.</p>
            )}
          </SectionCard>
        </div>
      )}
    </div>
  );
}
