"use client";

import { useEffect, useState } from "react";

import { PageTitle } from "@/components/page-title";
import { PrintButton } from "@/components/print-button";
import { SectionCard } from "@/components/section-card";
import { fetchExecutionGuardrails } from "@/lib/api";
import { ExecutionGuardrails } from "@/lib/types";

export default function SettingsPage() {
  const [guardrails, setGuardrails] = useState<ExecutionGuardrails | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchExecutionGuardrails()
      .then((data) => {
        setGuardrails(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div>
      <PageTitle
        title="Settings"
        subtitle="Phase 1 local configuration settings."
        actions={<PrintButton />}
      />

      {error ? <p className="mb-4 rounded-lg bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p> : null}

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="Execution Guardrails">
          <ul className="space-y-2 text-sm text-muted">
            <li>Default mode: {guardrails?.default_mode || "isolated"}</li>
            <li>Shared adapter enabled: {guardrails?.shared_adapter_enabled ? "yes" : "no"}</li>
            <li>Legacy live-send reuse allowed: {guardrails?.allow_legacy_live_send_reuse ? "yes" : "no"}</li>
            <li>{guardrails?.policy_note || "Execution paths remain isolated by default."}</li>
          </ul>
        </SectionCard>

        <SectionCard title="Application Behavior">
          <ul className="space-y-2 text-sm text-muted">
            <li>Mode: Local-first only (CSV/XLSX file uploads, local SQLite persistence).</li>
            <li>Data source integrations: disabled in Phase 1 (no live QuickBooks API access).</li>
            <li>Duplicate handling: never auto-delete without reviewer action.</li>
            <li>Category handling: suggestive only unless reviewer applies rules.</li>
          </ul>
        </SectionCard>
      </div>
    </div>
  );
}
