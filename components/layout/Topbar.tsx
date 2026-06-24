"use client";

import { cn } from "@/lib/utils";

interface TopbarProps {
  title?: string;
  alertCount?: number;
  className?: string;
}

const TABS = ["Global Metrics", "Network Status"] as const;

export function Topbar({
  title = "Farm Command Center",
  alertCount = 0,
  className,
}: TopbarProps) {
  return (
    <header
      className={cn(
        "flex h-16 shrink-0 items-center justify-between gap-4 border-b border-white/5 bg-surface-container/80 px-6 backdrop-blur-xl",
        className,
      )}
    >
      <div className="relative hidden min-w-0 flex-1 md:block md:max-w-xs lg:max-w-sm">
        <svg
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-on-surface-variant"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
        <input
          type="search"
          placeholder="Search parameters..."
          aria-label="Search parameters"
          className="h-9 w-full rounded-full border border-white/10 bg-white/5 pl-9 pr-4 text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>

      <div className="hidden items-center gap-6 lg:flex">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            type="button"
            className={cn(
              "relative pb-1 text-sm font-medium transition-colors",
              i === 0
                ? "text-primary"
                : "text-on-surface-variant hover:text-on-surface",
            )}
          >
            {tab}
            {i === 0 && (
              <span className="absolute -bottom-4 left-0 h-0.5 w-full bg-primary shadow-[0_0_8px_rgba(71,214,255,0.6)]" />
            )}
          </button>
        ))}
      </div>

      <h1 className="text-sm font-semibold text-on-surface lg:hidden">{title}</h1>

      <div className="flex items-center gap-3">
        <button
          type="button"
          className="hidden rounded-full border border-white/10 px-4 py-2 text-sm font-medium text-on-surface transition-colors hover:border-primary/30 hover:bg-white/5 sm:block"
        >
          Run AI Diagnostic
        </button>

        <button
          type="button"
          className="relative rounded-full p-2 text-on-surface-variant transition-colors hover:bg-white/5 hover:text-on-surface"
          aria-label={`Notifications${alertCount > 0 ? `, ${alertCount} active alerts` : ""}`}
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
          </svg>
          {alertCount > 0 && (
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-error shadow-[0_0_6px_rgba(255,180,171,0.8)]" />
          )}
        </button>
      </div>
    </header>
  );
}
