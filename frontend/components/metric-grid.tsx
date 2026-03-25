export function MetricGrid({
  items
}: {
  items: Array<{ label: string; value: string | number; accent?: "ok" | "warn" | "bad" | "default" }>;
}) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map((item) => (
        <article key={item.label} className="rounded-2xl border border-line bg-panel p-4 shadow-panel">
          <p className="text-xs uppercase tracking-wide text-muted">{item.label}</p>
          <p
            className={`mt-2 text-2xl font-semibold ${
              item.accent === "ok"
                ? "text-ok"
                : item.accent === "warn"
                  ? "text-warn"
                  : item.accent === "bad"
                    ? "text-bad"
                    : "text-ink"
            }`}
          >
            {item.value}
          </p>
        </article>
      ))}
    </div>
  );
}
