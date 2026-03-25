export function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-line bg-white p-8 text-center text-sm text-muted">{text}</div>
  );
}
