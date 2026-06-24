import Link from "next/link";
import type { Tank } from "@/types";
import {
  computePsiScore,
  formatCompact,
  formatNumber,
  formatRelativeTime,
  getTankBiomassKg,
  getTankDisplayId,
  getTankHealthStatusLabel,
  getTankHealthStatusStyle,
  getPsiStatusStyle,
} from "@/lib";
import { cn } from "@/lib/utils";

interface TankCardProps {
  tank: Tank;
  zoneName?: string;
  zoneCode?: string;
  href?: string;
  className?: string;
}

export function TankCard({
  tank,
  zoneName,
  zoneCode,
  href,
  className,
}: TankCardProps) {
  const { lastReading } = tank;
  const displayId = getTankDisplayId(tank);
  const biomass = getTankBiomassKg(tank);
  const psiScore = computePsiScore(tank);
  const isActive = tank.status !== "maintenance" && tank.status !== "offline";
  const linkHref = href ?? `/tanks/${tank.id}`;

  const content = (
    <>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-on-surface">{displayId}</h3>
          <p className="mt-0.5 text-xs text-on-surface-variant">{tank.species}</p>
          <p className="mt-1 text-[11px] text-on-surface-variant/80">
            {tank.name}
            {zoneCode && ` · ${zoneCode}`}
          </p>
        </div>
        <span
          className={cn(
            "rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest",
            getTankHealthStatusStyle(tank.status),
          )}
        >
          {getTankHealthStatusLabel(tank.status)}
        </span>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3">
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
            Population
          </dt>
          <dd className="mt-1 text-base font-semibold text-on-surface">
            {tank.fishCount > 0 ? formatCompact(tank.fishCount) : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
            Biomass
          </dt>
          <dd className="mt-1 text-base font-semibold text-on-surface">
            {biomass > 0 ? `${formatCompact(biomass)} kg` : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
            Temperature
          </dt>
          <dd className="mt-1 text-sm font-medium text-on-surface">
            {formatNumber(lastReading.temperatureC, 1)}°C
          </dd>
        </div>
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
            pH
          </dt>
          <dd className="mt-1 text-sm font-medium text-on-surface">
            {formatNumber(lastReading.ph, 1)}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
            Dissolved Oxygen
          </dt>
          <dd className="mt-1 text-sm font-medium text-on-surface">
            {formatNumber(lastReading.dissolvedOxygenMgL, 1)} mg/L
          </dd>
        </div>
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
            PSI Score
          </dt>
          <dd
            className={cn(
              "mt-1 text-sm font-semibold",
              getPsiStatusStyle(psiScore),
            )}
          >
            {psiScore > 0 ? formatNumber(psiScore, 1) : "—"}
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
        <span className="text-xs text-on-surface-variant">
          {isActive
            ? `Updated ${formatRelativeTime(lastReading.timestamp)}`
            : zoneName ?? "No active cohort"}
        </span>
        <span className="inline-flex items-center gap-1 text-xs font-medium text-primary">
          Details
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
          </svg>
        </span>
      </div>
    </>
  );

  return (
    <Link
      href={linkHref}
      className={cn(
        "glass-panel group block rounded-2xl p-5 transition-all hover:border-primary/30 hover:shadow-[0_0_30px_rgba(71,214,255,0.08)]",
        className,
      )}
    >
      {content}
    </Link>
  );
}
