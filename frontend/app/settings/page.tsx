import { PageTitle } from "@/components/page-title";
import { SectionCard } from "@/components/section-card";

export default function SettingsPage() {
  return (
    <div>
      <PageTitle
        title="Settings"
        subtitle="Phase 1 local configuration settings."
      />

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="Application Behavior">
          <ul className="space-y-2 text-sm text-muted">
            <li>Mode: Local-first only (CSV/XLSX file uploads, local SQLite persistence).</li>
            <li>Data source integrations: disabled in Phase 1 (no live QuickBooks API access).</li>
            <li>Duplicate handling: never auto-delete without reviewer action.</li>
            <li>Category handling: suggestive only unless reviewer applies rules.</li>
          </ul>
        </SectionCard>

        <SectionCard title="Future Flags (Planned)">
          <ul className="space-y-2 text-sm text-muted">
            <li>QuickBooks API connector</li>
            <li>Bank feed adapters</li>
            <li>Reconciliation assistant</li>
            <li>Recurring rules engine</li>
            <li>Multi-client workspaces and auth</li>
          </ul>
        </SectionCard>
      </div>
    </div>
  );
}
