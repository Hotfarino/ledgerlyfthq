"use client";

export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { JobPicker } from "@/components/job-picker";
import { PageTitle } from "@/components/page-title";
import { PrintButton } from "@/components/print-button";
import { SectionCard } from "@/components/section-card";
import { fetchDuplicates, markReviewed } from "@/lib/api";
import { DuplicateGroup } from "@/lib/types";
import { useActiveJobId } from "@/lib/use-active-job";

export default function DuplicatesPage() {
  const [jobId] = useActiveJobId();

  const [duplicates, setDuplicates] = useState<DuplicateGroup[]>([]);
  const [confidence, setConfidence] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDuplicates(jobId);
      setDuplicates(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load duplicates");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  const filtered = useMemo(
    () => (confidence ? duplicates.filter((item) => item.confidence === confidence) : duplicates),
    [confidence, duplicates]
  );

  async function markVisibleReviewed() {
    if (!jobId || filtered.length === 0) return;
    await markReviewed(jobId, "duplicates", filtered.map((item) => item.id));
    await load();
  }

  return (
    <div>
      <PageTitle
        title="Duplicate Review"
        subtitle="Exact and likely duplicates are grouped for manual review."
        actions={
          <div className="flex items-center gap-2">
            <PrintButton />
            <JobPicker />
          </div>
        }
      />

      <SectionCard title="Duplicate Filters">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm">
            Confidence
            <select
              className="rounded-lg border border-line bg-white px-3 py-2"
              value={confidence}
              onChange={(event) => setConfidence(event.target.value)}
            >
              <option value="">All confidence levels</option>
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
            onClick={markVisibleReviewed}
            disabled={!jobId || filtered.length === 0}
          >
            Mark Visible Reviewed
          </button>
        </div>
      </SectionCard>

      <div className="mt-6">
        <SectionCard title="Duplicate Candidates">
          {error ? <p className="mb-3 text-sm text-bad">{error}</p> : null}
          {!jobId ? (
            <EmptyState text="Select a job to inspect duplicate candidates." />
          ) : filtered.length === 0 ? (
            <EmptyState text="No duplicate candidates for this selection." />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Confidence</th>
                    <th>Match Type</th>
                    <th>Source Rows</th>
                    <th>Row IDs</th>
                    <th>Reason</th>
                    <th>Reviewed</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((item) => (
                    <tr key={item.id}>
                      <td>{item.confidence}</td>
                      <td>{item.match_type}</td>
                      <td className="num-cell">{item.source_row_indexes.map((index) => index + 1).join(", ")}</td>
                      <td className="mono-cell">{item.row_ids.join(", ")}</td>
                      <td>{item.reason}</td>
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
