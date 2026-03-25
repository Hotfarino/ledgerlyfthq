"use client";

export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { FlagChip } from "@/components/flag-chip";
import { JobPicker } from "@/components/job-picker";
import { PageTitle } from "@/components/page-title";
import { SectionCard } from "@/components/section-card";
import { fetchRows, markReviewed } from "@/lib/api";
import { TransactionRow } from "@/lib/types";
import { useActiveJobId } from "@/lib/use-active-job";

export default function ReviewPage() {
  const [jobId] = useActiveJobId();

  const [rows, setRows] = useState<TransactionRow[]>([]);
  const [search, setSearch] = useState("");
  const [flagFilter, setFlagFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Record<number, boolean>>({});

  async function loadRows() {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRows(jobId, {
        search: search || undefined,
        flag: flagFilter || undefined
      });
      setRows(data);
      setSelected({});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load rows");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  const flagOptions = useMemo(() => {
    const all = new Set<string>();
    rows.forEach((row) => row.flags.forEach((flag) => all.add(flag)));
    return Array.from(all).sort();
  }, [rows]);

  const selectedIds = Object.entries(selected)
    .filter(([, value]) => value)
    .map(([key]) => key);

  async function handleMarkReviewed() {
    if (!jobId || selectedIds.length === 0) return;
    await markReviewed(jobId, "rows", selectedIds);
    await loadRows();
  }

  return (
    <div>
      <PageTitle
        title="Review Cleaned Data"
        subtitle="Inspect cleaned rows with before/after values and review status before export."
        actions={<JobPicker />}
      />

      <SectionCard title="Filters and Actions">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex min-w-64 flex-col gap-1 text-sm">
            Search
            <input
              className="rounded-lg border border-line bg-white px-3 py-2"
              placeholder="payee, amount, date, category"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>

          <label className="flex min-w-64 flex-col gap-1 text-sm">
            Flag filter
            <select
              className="rounded-lg border border-line bg-white px-3 py-2"
              value={flagFilter}
              onChange={(event) => setFlagFilter(event.target.value)}
            >
              <option value="">All flags</option>
              {flagOptions.map((flag) => (
                <option key={flag} value={flag}>
                  {flag}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            className="rounded-lg border border-line bg-white px-4 py-2 text-sm font-semibold"
            onClick={loadRows}
            disabled={!jobId || loading}
          >
            {loading ? "Loading..." : "Run Filters"}
          </button>

          <button
            type="button"
            className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
            onClick={handleMarkReviewed}
            disabled={!jobId || selectedIds.length === 0}
          >
            Mark Selected Reviewed ({selectedIds.length})
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-bad">{error}</p> : null}
      </SectionCard>

      <div className="mt-6">
        <SectionCard title="Cleaned Rows">
          {!jobId ? (
            <EmptyState text="Select a job to review rows." />
          ) : rows.length === 0 ? (
            <EmptyState text="No rows returned for the current filters." />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th />
                    <th>Row</th>
                    <th>Date</th>
                    <th>Payee/Description</th>
                    <th>Amount</th>
                    <th>Category</th>
                    <th>Flags</th>
                    <th>Review</th>
                    <th>Before/After</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={`${row.row_index}-${row.transaction_id}`}>
                      <td>
                        <input
                          type="checkbox"
                          checked={Boolean(selected[row.row_index])}
                          onChange={(event) =>
                            setSelected((prev) => ({
                              ...prev,
                              [row.row_index]: event.target.checked
                            }))
                          }
                        />
                      </td>
                      <td>{row.row_index + 1}</td>
                      <td>{String(row.cleaned_values.date || "")}</td>
                      <td>
                        <div className="font-medium">{String(row.cleaned_values.payee || "")}</div>
                        <div className="text-xs text-muted">{String(row.cleaned_values.description || "")}</div>
                      </td>
                      <td className="font-mono">{String(row.cleaned_values.signed_amount || "")}</td>
                      <td>
                        <div>{String(row.cleaned_values.category || "") || "-"}</div>
                        {row.category_suggestion ? (
                          <div className="text-xs text-muted">
                            Suggestion: {row.category_suggestion} ({row.category_confidence})
                          </div>
                        ) : null}
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {row.flags.map((flag) => (
                            <FlagChip key={`${row.row_index}-${flag}`} value={flag} />
                          ))}
                        </div>
                      </td>
                      <td>{row.review_status}</td>
                      <td className="text-xs text-muted">
                        <div>Orig: {String(row.original_values["Description"] || row.original_values["Details"] || "")}</div>
                        <div>Clean: {String(row.cleaned_values.description || "")}</div>
                      </td>
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
