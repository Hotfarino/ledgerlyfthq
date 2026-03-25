import clsx from "clsx";

export function FlagChip({ value }: { value: string }) {
  const severity =
    value.includes("missing") || value.includes("invalid") || value.includes("malformed")
      ? "bad"
      : value.includes("duplicate") || value.includes("inconsistent")
        ? "warn"
        : "ok";

  return (
    <span
      className={clsx(
        "inline-flex rounded-md px-2 py-1 text-xs font-medium",
        severity === "bad" ? "bg-red-100 text-red-700" : severity === "warn" ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"
      )}
    >
      {value}
    </span>
  );
}
