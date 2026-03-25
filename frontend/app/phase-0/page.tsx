"use client";

export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { PageTitle } from "@/components/page-title";
import { PrintButton } from "@/components/print-button";
import { SectionCard } from "@/components/section-card";
import { fetchPhase0Report } from "@/lib/api";
import { Phase0Report } from "@/lib/types";

export default function Phase0Page() {
  const [report, setReport] = useState<Phase0Report | null>(null);
  const [days, setDays] = useState(60);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadReport(lookbackDays: number) {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPhase0Report(lookbackDays);
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load diagnostics report");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport(days);
  }, [days]);

  const topSignals = useMemo(() => {
    if (!report) return [];
    return [...report.pain_points].sort((a, b) => b.count - a.count);
  }, [report]);

  return (
    <div>
      <PageTitle
        title="Phase 0 Diagnostics"
        subtitle="Run this first on actual last-60-day history to locate primary operational pain."
        actions={
          <div className="flex items-center gap-2">
            <PrintButton label="Print Diagnostics" />
          </div>
        }
      />

      <SectionCard title="Lookback Window">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm">
            Days
            <select
              className="rounded-lg border border-line bg-white px-3 py-2"
              value={days}
              onChange={(event) => setDays(Number(event.target.value))}
            >
              <option value={30}>30</option>
              <option value={60}>60</option>
              <option value={90}>90</option>
              <option value={180}>180</option>
            </select>
          </label>
          <button
            type="button"
            className="no-print rounded-lg border border-line bg-white px-4 py-2 text-sm font-semibold"
            onClick={() => loadReport(days)}
          >
            {loading ? "Running..." : "Re-run"}
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-bad">{error}</p> : null}
      </SectionCard>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <SectionCard title="Pain Signal Breakdown">
          {!report ? (
            <EmptyState text="No Phase 0 data yet." />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Pain Area</th>
                    <th className="num-cell">Signals</th>
                    <th className="num-cell">% of Signals</th>
                  </tr>
                </thead>
                <tbody>
                  {topSignals.map((item) => (
                    <tr key={item.key}>
                      <td>{item.label}</td>
                      <td className="num-cell">{item.count}</td>
                      <td className="num-cell">{item.percent_of_signals.toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>

        <SectionCard title="Phase 0 Summary">
          {!report ? (
            <p className="text-sm text-muted">Loading diagnostics summary...</p>
          ) : (
            <ul className="space-y-2 text-sm">
              <li>Top pain area: {report.top_pain_area}</li>
              <li>Jobs analyzed: {report.jobs_analyzed}</li>
              <li>Rows analyzed: {report.rows_analyzed}</li>
              <li>Total signals: {report.signals_total}</li>
              <li>Generated: {new Date(report.generated_at).toLocaleString()}</li>
            </ul>
          )}

          {report?.notes?.length ? (
            <div className="mt-4 rounded-lg border border-line bg-slate-50 px-3 py-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted">Notes</p>
              <ul className="mt-2 space-y-1 text-sm text-muted">
                {report.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </SectionCard>
      </div>
    </div>
  );
}
