import type { ZoneOverview } from "@/data/dashboard";
import { SPECIES } from "@/lib/constants";
import { formatCompact, formatNumber } from "@/lib";
import { cn } from "@/lib/utils";

interface ZoneOverviewCardProps {
  zone: ZoneOverview;
  className?: string;
}

const statusStyles: Record<ZoneOverview["displayStatus"], string> = {
  optimal: "badge-optimal",
  warning: "badge-warning",
  critical: "badge-critical",
};

const statusLabels: Record<ZoneOverview["displayStatus"], string> = {
  optimal: "Optimal",
  warning: "Warning",
  critical: "Critical",
};

export function ZoneOverviewCard({ zone, className }: ZoneOverviewCardProps) {
  return (
    <article
      className={cn(
        "glass-panel group rounded-2xl p-5 transition-all hover:border-primary/20",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-on-surface">{zone.code}</h3>
          <p className="mt-0.5 text-xs text-on-surface-variant">{SPECIES}</p>
        </div>
        <span
          className={cn(
            "rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest",
            statusStyles[zone.displayStatus],
          )}
        >
          {statusLabels[zone.displayStatus]}
        </span>
      </div>

      <p className="mt-2 text-xs text-on-surface-variant">{zone.name}</p>

      <dl className="mt-4 grid grid-cols-2 gap-4">
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
            Population
          </dt>
          <dd className="mt-1 text-lg font-semibold text-on-surface">
            {formatCompact(zone.population)}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
            Health Score
          </dt>
          <dd className="mt-1 text-lg font-semibold text-on-surface">
            {formatNumber(zone.avgHealthScore, 1)}
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
        <span className="text-xs text-on-surface-variant">
          Updated {zone.updatedMinutesAgo}m ago
        </span>
        <button
          type="button"
          className="inline-flex items-center gap-1 text-xs font-medium text-primary transition-colors hover:text-primary-bright"
        >
          Details
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
          </svg>
        </button>
      </div>
    </article>
  );
}
