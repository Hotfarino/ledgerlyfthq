"use client";

export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/empty-state";
import { JobPicker } from "@/components/job-picker";
import { PageTitle } from "@/components/page-title";
import { SectionCard } from "@/components/section-card";
import { fetchAuditLog } from "@/lib/api";
import { AuditEntry } from "@/lib/types";
import { useActiveJobId } from "@/lib/use-active-job";

export default function AuditLogPage() {
  const [jobId] = useActiveJobId();

  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      setEntries([]);
      return;
    }
    setLoading(true);
    fetchAuditLog(jobId)
      .then((results) => {
        setEntries(results);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [jobId]);

  return (
    <div>
      <PageTitle
        title="Audit Log"
        subtitle="Row-level change history and workflow events for traceability."
        actions={<JobPicker />}
      />

      <SectionCard title="Audit Entries">
        {error ? <p className="mb-3 text-sm text-bad">{error}</p> : null}
        {!jobId ? (
          <EmptyState text="Select a job to view its audit trail." />
        ) : loading ? (
          <p className="text-sm text-muted">Loading audit entries...</p>
        ) : entries.length === 0 ? (
          <EmptyState text="No audit entries found for this job." />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Action</th>
                  <th>Row</th>
                  <th>Field</th>
                  <th>Change</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>{new Date(entry.created_at).toLocaleString()}</td>
                    <td>{entry.action}</td>
                    <td>{entry.row_index !== null && entry.row_index !== undefined ? entry.row_index + 1 : "-"}</td>
                    <td>{entry.field_name || "-"}</td>
                    <td className="text-xs">
                      {entry.old_value !== null && entry.old_value !== undefined ? `"${entry.old_value}" -> "${entry.new_value || ""}"` : "-"}
                    </td>
                    <td>{entry.note || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
