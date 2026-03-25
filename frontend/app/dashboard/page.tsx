"use client";

export const dynamic = "force-dynamic";

import { useEffect, useMemo, useState } from "react";

import { JobPicker } from "@/components/job-picker";
import { MetricGrid } from "@/components/metric-grid";
import { PageTitle } from "@/components/page-title";
import { SectionCard } from "@/components/section-card";
import { fetchDashboardMetrics, fetchJobs } from "@/lib/api";
import { DashboardMetrics, JobRecord } from "@/lib/types";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchDashboardMetrics(), fetchJobs()])
      .then(([metricsData, jobsData]) => {
        setMetrics(metricsData);
        setJobs(jobsData);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const metricItems = useMemo(
    () => [
      { label: "Files Imported", value: metrics?.files_imported ?? "-" },
      { label: "Rows Processed", value: metrics?.rows_processed ?? "-" },
      { label: "Duplicates Flagged", value: metrics?.duplicates_flagged ?? "-", accent: "warn" as const },
      { label: "Exceptions Flagged", value: metrics?.exceptions_flagged ?? "-", accent: "bad" as const },
      {
        label: "Uncategorized Transactions",
        value: metrics?.uncategorized_transactions ?? "-",
        accent: "warn" as const
      },
      {
        label: "Last Export",
        value: metrics?.last_export_time ? new Date(metrics.last_export_time).toLocaleString() : "Not exported"
      }
    ],
    [metrics]
  );

  return (
    <div>
      <PageTitle
        title="Dashboard"
        subtitle="Track current cleanup workload and output volume."
        actions={<JobPicker />}
      />

      {error ? <p className="mb-4 rounded-lg bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p> : null}

      <MetricGrid items={metricItems} />

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <SectionCard title="Recent Imports">
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Rows</th>
                  <th>Uploaded</th>
                  <th>Job ID</th>
                </tr>
              </thead>
              <tbody>
                {jobs.slice(0, 8).map((job) => (
                  <tr key={job.id}>
                    <td>{job.file_name}</td>
                    <td>{job.row_count}</td>
                    <td>{new Date(job.uploaded_at).toLocaleString()}</td>
                    <td className="font-mono text-xs">{job.id.slice(0, 12)}</td>
                  </tr>
                ))}
                {jobs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="text-muted">
                      No jobs yet.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <SectionCard title="Workflow Guardrails">
          <ul className="space-y-2 text-sm text-muted">
            <li>LedgerLift accelerates cleanup. It does not replace accounting judgment.</li>
            <li>Duplicates, exceptions, and category suggestions always require reviewer approval.</li>
            <li>Phase 1 is local-first with CSV/XLSX file upload and local export outputs.</li>
            <li>No live QuickBooks API connection is used in this phase.</li>
          </ul>
        </SectionCard>
      </div>
    </div>
  );
}
