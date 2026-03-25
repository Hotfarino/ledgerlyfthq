"use client";

export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { JobPicker } from "@/components/job-picker";
import { PageTitle } from "@/components/page-title";
import { SectionCard } from "@/components/section-card";
import { fetchExceptions, markReviewed } from "@/lib/api";
import { ExceptionFlag } from "@/lib/types";
import { useActiveJobId } from "@/lib/use-active-job";

export default function ExceptionsPage() {
  const [jobId] = useActiveJobId();

  const [exceptions, setExceptions] = useState<ExceptionFlag[]>([]);
  const [severity, setSeverity] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchExceptions(jobId);
      setExceptions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load exceptions");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  const filtered = useMemo(
    () => (severity ? exceptions.filter((item) => item.severity === severity) : exceptions),
    [exceptions, severity]
  );

  async function markAllReviewed() {
    if (!jobId || filtered.length === 0) return;
    await markReviewed(jobId, "exceptions", filtered.map((item) => item.id));
    await load();
  }

  return (
    <div>
      <PageTitle
        title="Exceptions"
        subtitle="Rows requiring manual review due to missing or malformed values."
        actions={<JobPicker />}
      />

      <SectionCard title="Exception Filters">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm">
            Severity
            <select
              className="rounded-lg border border-line bg-white px-3 py-2"
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
            >
              <option value="">All severities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </label>
          <button
            type="button"
            className="rounded-lg border border-line bg-white px-4 py-2 text-sm font-semibold"
            onClick={load}
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
          <button
            type="button"
            className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            onClick={markAllReviewed}
            disabled={!jobId || filtered.length === 0}
          >
            Mark Visible Reviewed
          </button>
        </div>
      </SectionCard>

      <div className="mt-6">
        <SectionCard title="Flagged Rows">
          {error ? <p className="mb-3 text-sm text-bad">{error}</p> : null}
          {!jobId ? (
            <EmptyState text="Select a job to inspect exceptions." />
          ) : filtered.length === 0 ? (
            <EmptyState text="No exceptions for this selection." />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Severity</th>
                    <th>Flag</th>
                    <th>Source Row</th>
                    <th>Row ID</th>
                    <th>Message</th>
                    <th>Reviewed</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((item) => (
                    <tr key={item.id}>
                      <td>{item.severity}</td>
                      <td>{item.flag_type}</td>
                      <td>{item.source_row_index + 1}</td>
                      <td className="font-mono text-xs">{item.row_id}</td>
                      <td>{item.message}</td>
                      <td>{item.reviewed ? "yes" : "no"}</td>
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
