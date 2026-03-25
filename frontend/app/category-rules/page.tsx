"use client";

export const dynamic = "force-dynamic";

import { FormEvent, useEffect, useState } from "react";
import { EmptyState } from "@/components/empty-state";
import { JobPicker } from "@/components/job-picker";
import { PageTitle } from "@/components/page-title";
import { SectionCard } from "@/components/section-card";
import { applyCategoryRules, createCategoryRule, fetchCategoryRules, fetchSuggestions } from "@/lib/api";
import { CategoryRule, TransactionRow } from "@/lib/types";
import { useActiveJobId } from "@/lib/use-active-job";

const initialForm = {
  name: "",
  target_field: "payee",
  contains_text: "",
  suggested_category: "",
  confidence: "medium" as "high" | "medium" | "low",
  active: true
};

export default function CategoryRulesPage() {
  const [jobId] = useActiveJobId();

  const [rules, setRules] = useState<CategoryRule[]>([]);
  const [suggestions, setSuggestions] = useState<TransactionRow[]>([]);
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [ruleData, suggestionData] = await Promise.all([
        fetchCategoryRules(),
        jobId ? fetchSuggestions(jobId) : Promise.resolve([])
      ]);
      setRules(ruleData);
      setSuggestions(suggestionData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load category rules");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  async function handleCreateRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);

    try {
      await createCategoryRule(form);
      setForm(initialForm);
      setMessage("Category rule created.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create rule");
    }
  }

  async function runRules(previewOnly: boolean) {
    if (!jobId) {
      setError("Select a job first.");
      return;
    }
    setError(null);
    setMessage(null);
    try {
      await applyCategoryRules(jobId, previewOnly);
      setMessage(previewOnly ? "Category suggestions preview refreshed." : "Category rules applied to uncategorized rows.");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not run category rules");
    }
  }

  return (
    <div>
      <PageTitle
        title="Category Rules"
        subtitle="Define and apply deterministic category suggestions. Suggestions remain reviewable."
        actions={<JobPicker />}
      />

      {error ? <p className="mb-3 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p> : null}
      {message ? <p className="mb-3 rounded bg-emerald-100 px-3 py-2 text-sm text-emerald-700">{message}</p> : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_2fr]">
        <SectionCard title="Create Rule">
          <form className="space-y-3" onSubmit={handleCreateRule}>
            <label className="flex flex-col gap-1 text-sm">
              Rule name
              <input
                className="rounded-lg border border-line bg-white px-3 py-2"
                value={form.name}
                onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                required
              />
            </label>

            <label className="flex flex-col gap-1 text-sm">
              Target field
              <select
                className="rounded-lg border border-line bg-white px-3 py-2"
                value={form.target_field}
                onChange={(event) => setForm((prev) => ({ ...prev, target_field: event.target.value }))}
              >
                <option value="payee">Payee</option>
                <option value="description">Description</option>
                <option value="memo">Memo</option>
                <option value="vendor">Vendor</option>
              </select>
            </label>

            <label className="flex flex-col gap-1 text-sm">
              Contains text
              <input
                className="rounded-lg border border-line bg-white px-3 py-2"
                value={form.contains_text}
                onChange={(event) => setForm((prev) => ({ ...prev, contains_text: event.target.value }))}
                placeholder="e.g., shell"
                required
              />
            </label>

            <label className="flex flex-col gap-1 text-sm">
              Suggested category
              <input
                className="rounded-lg border border-line bg-white px-3 py-2"
                value={form.suggested_category}
                onChange={(event) => setForm((prev) => ({ ...prev, suggested_category: event.target.value }))}
                placeholder="e.g., Fuel"
                required
              />
            </label>

            <label className="flex flex-col gap-1 text-sm">
              Confidence
              <select
                className="rounded-lg border border-line bg-white px-3 py-2"
                value={form.confidence}
                onChange={(event) =>
                  setForm((prev) => ({
                    ...prev,
                    confidence: event.target.value as "high" | "medium" | "low"
                  }))
                }
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </label>

            <button type="submit" className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white">
              Add Rule
            </button>
          </form>
        </SectionCard>

        <SectionCard
          title="Existing Rules"
          right={
            <div className="flex gap-2">
              <button
                type="button"
                className="rounded-lg border border-line bg-white px-3 py-2 text-xs font-semibold"
                onClick={() => runRules(true)}
                disabled={loading}
              >
                Preview Suggestions
              </button>
              <button
                type="button"
                className="rounded-lg bg-accent px-3 py-2 text-xs font-semibold text-white"
                onClick={() => runRules(false)}
                disabled={loading}
              >
                Apply to Job
              </button>
            </div>
          }
        >
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Field</th>
                  <th>Contains</th>
                  <th>Category</th>
                  <th>Confidence</th>
                  <th>Active</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => (
                  <tr key={rule.id}>
                    <td>{rule.name}</td>
                    <td>{rule.target_field}</td>
                    <td>{rule.contains_text}</td>
                    <td>{rule.suggested_category}</td>
                    <td>{rule.confidence}</td>
                    <td>{rule.active ? "yes" : "no"}</td>
                  </tr>
                ))}
                {rules.length === 0 ? (
                  <tr>
                    <td colSpan={6}>No rules configured.</td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>

      <div className="mt-6">
        <SectionCard title="Current Category Suggestions">
          {!jobId ? (
            <EmptyState text="Select a job to review category suggestions." />
          ) : suggestions.length === 0 ? (
            <EmptyState text="No suggestions available for this job yet." />
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Row</th>
                    <th>Payee/Description</th>
                    <th>Current Category</th>
                    <th>Suggested Category</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {suggestions.map((row) => (
                    <tr key={`${row.row_index}-${row.transaction_id}`}>
                      <td>{row.row_index + 1}</td>
                      <td>
                        <div>{String(row.cleaned_values.payee || "")}</div>
                        <div className="text-xs text-muted">{String(row.cleaned_values.description || "")}</div>
                      </td>
                      <td>{String(row.cleaned_values.category || "") || "-"}</td>
                      <td>{row.category_suggestion || "-"}</td>
                      <td>{row.category_confidence || "-"}</td>
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
