"use client";

import { useEffect, useState } from "react";

const ACTIVE_JOB_KEY = "ledgerlift.activeJobId";
const ACTIVE_JOB_EVENT = "ledgerlift:active-job-changed";

function readActiveJobId(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(ACTIVE_JOB_KEY) || "";
}

export function setActiveJobId(jobId: string) {
  if (typeof window === "undefined") return;
  if (jobId) {
    window.localStorage.setItem(ACTIVE_JOB_KEY, jobId);
  } else {
    window.localStorage.removeItem(ACTIVE_JOB_KEY);
  }
  window.dispatchEvent(new CustomEvent(ACTIVE_JOB_EVENT, { detail: { jobId } }));
}

export function useActiveJobId(): [string, (jobId: string) => void] {
  const [jobId, setJobIdState] = useState("");

  useEffect(() => {
    const initial = readActiveJobId();
    setJobIdState(initial);

    const onStorage = () => setJobIdState(readActiveJobId());
    const onActiveJobChange = (event: Event) => {
      const customEvent = event as CustomEvent<{ jobId?: string }>;
      setJobIdState(customEvent.detail?.jobId || readActiveJobId());
    };

    window.addEventListener("storage", onStorage);
    window.addEventListener(ACTIVE_JOB_EVENT, onActiveJobChange);

    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener(ACTIVE_JOB_EVENT, onActiveJobChange);
    };
  }, []);

  const setJobId = (nextJobId: string) => {
    setActiveJobId(nextJobId);
    setJobIdState(nextJobId);
  };

  return [jobId, setJobId];
}
