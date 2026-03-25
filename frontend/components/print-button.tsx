"use client";

export function PrintButton({ label = "Print View" }: { label?: string }) {
  return (
    <button
      type="button"
      className="no-print rounded-lg border border-line bg-white px-3 py-2 text-sm font-semibold text-ink"
      onClick={() => window.print()}
    >
      {label}
    </button>
  );
}
