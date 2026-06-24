import Link from "next/link";
import { notFound } from "next/navigation";
import { AppShell } from "@/components/layout";
import {
  computePsiScore,
  formatCompact,
  formatNumber,
  formatRelativeTime,
  getTankBiomassKg,
  getTankDisplayId,
  getTankHealthStatusLabel,
  getTankHealthStatusStyle,
  getTankRiskLabel,
  getTankRiskLevel,
} from "@/lib";
import { cn } from "@/lib/utils";
import { getActiveAlerts } from "@/data/alerts";
import { getTankById } from "@/data/tanks";
import { getZoneById } from "@/data/zones";

interface TankDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function TankDetailPage({ params }: TankDetailPageProps) {
  const { id } = await params;
  const tank = getTankById(id);

  if (!tank) {
    notFound();
  }

  const zone = getZoneById(tank.zoneId);
  const activeAlerts = getActiveAlerts();
  const displayId = getTankDisplayId(tank);
  const biomass = getTankBiomassKg(tank);
  const psiScore = computePsiScore(tank);
  const riskLevel = getTankRiskLevel(tank);
  const { lastReading } = tank;

  return (
    <AppShell activePath="/tanks" title="Tank Management" alertCount={activeAlerts.length}>
      <div className="mb-6">
        <Link
          href="/tanks"
          className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:text-primary-bright"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
          Back to Tank Management
        </Link>
        <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-on-surface">{displayId}</h1>
            <p className="mt-1 text-sm text-on-surface-variant">{tank.name}</p>
            <p className="mt-0.5 text-xs text-on-surface-variant">
              {zone?.code} · {zone?.name} · {tank.species}
            </p>
          </div>
          <span
            className={cn(
              "rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-widest",
              getTankHealthStatusStyle(tank.status),
            )}
          >
            {getTankHealthStatusLabel(tank.status)}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="glass-panel-glow rounded-2xl p-6 lg:col-span-2">
          <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
            Production Metrics
          </h2>
          <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Population
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {tank.fishCount > 0 ? formatCompact(tank.fishCount) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Biomass
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {biomass > 0 ? `${formatCompact(biomass)} kg` : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Avg Weight
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {tank.avgWeightKg > 0 ? `${formatNumber(tank.avgWeightKg, 2)} kg` : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                FCR
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {tank.fcr > 0 ? formatNumber(tank.fcr, 2) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Mortality Rate
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {formatNumber(tank.mortalityRatePercent, 2)}%
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Days in Production
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {tank.daysInProduction > 0 ? tank.daysInProduction : "—"}
              </dd>
            </div>
          </dl>
        </div>

        <div className="glass-panel rounded-2xl p-6">
          <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
            Risk Assessment
          </h2>
          <dl className="mt-4 space-y-4">
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Health Score
              </dt>
              <dd className="mt-1 text-3xl font-bold text-on-surface">
                {tank.healthScore > 0 ? tank.healthScore : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                PSI Score
              </dt>
              <dd className="mt-1 text-2xl font-semibold text-primary">
                {psiScore > 0 ? formatNumber(psiScore, 1) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Risk Classification
              </dt>
              <dd className="mt-1 text-sm font-medium text-on-surface">
                {getTankRiskLabel(riskLevel)}
              </dd>
            </div>
          </dl>
        </div>

        <div className="glass-panel rounded-2xl p-6 lg:col-span-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
              Water Quality — Last Sensor Reading
            </h2>
            <span className="text-xs text-on-surface-variant">
              {formatRelativeTime(lastReading.timestamp)}
            </span>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Temperature
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.temperatureC, 1)}°C
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                pH
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.ph, 1)}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Dissolved Oxygen
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.dissolvedOxygenMgL, 1)} mg/L
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Salinity
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.salinityPpt, 1)} ppt
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Ammonia
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.ammoniaMgL, 3)} mg/L
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Turbidity
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.turbidityNtu, 1)} NTU
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </AppShell>
  );
}
