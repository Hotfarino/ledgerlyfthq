"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/import", label: "Import" },
  { href: "/review", label: "Review Cleaned Data" },
  { href: "/exceptions", label: "Exceptions" },
  { href: "/duplicates", label: "Duplicate Review" },
  { href: "/category-rules", label: "Category Rules" },
  { href: "/export", label: "Export" },
  { href: "/audit-log", label: "Audit Log" },
  { href: "/settings", label: "Settings" }
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-line bg-panel px-4 py-6">
      <div className="mb-8 rounded-xl bg-accentSoft p-4">
        <h1 className="text-xl font-semibold text-ink">LedgerLift</h1>
        <p className="mt-2 text-xs text-muted">
          Bookkeeping data cleanup accelerator. Accounting judgment stays with the reviewer.
        </p>
      </div>

      <nav className="space-y-1">
        {links.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "block rounded-lg px-3 py-2 text-sm transition",
                active ? "bg-accent text-white" : "text-ink hover:bg-accentSoft"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
