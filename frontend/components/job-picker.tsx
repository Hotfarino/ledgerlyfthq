"use client";

import { fetchJobs } from "@/lib/api";
import { JobRecord } from "@/lib/types";
import { useActiveJobId } from "@/lib/use-active-job";
import { useEffect, useState } from "react";

export function JobPicker() {
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useActiveJobId();

  useEffect(() => {
    let mounted = true;
    fetchJobs()
      .then((results) => {
        if (!mounted) return;
        setJobs(results);
      })
      .catch((err: Error) => {
        if (!mounted) return;
        setError(err.message);
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="no-print flex flex-col gap-1 text-sm">
      <label htmlFor="job-picker" className="text-xs font-semibold uppercase tracking-wide text-muted">
        Active Job
      </label>
      <select
        id="job-picker"
        className="rounded-lg border border-line bg-white px-3 py-2 text-sm"
        value={selected}
        onChange={(event) => setSelected(event.target.value)}
      >
        <option value="">Select a job</option>
        {jobs.map((job) => (
          <option key={job.job_id} value={job.job_id}>
            {job.file_name} ({job.job_id.slice(0, 8)})
          </option>
        ))}
      </select>
      {loading ? <span className="text-xs text-muted">Loading jobs...</span> : null}
      {error ? <span className="text-xs text-bad">{error}</span> : null}
    </div>
  );
}
