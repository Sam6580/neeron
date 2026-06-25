"use client";

import { AppShell } from "@/components/layout";
import { HealthScoreCard, MetricCard, SummaryStatCard, AlertCard } from "@/components/cards";
import { DashboardRecommendations } from "@/components/dashboard";
import { useAppData } from "@/lib/hooks/useAppData";
import {
  getTankHealthStatusLabel,
  getTankHealthStatusStyle,
  getTankRiskLabel,
  getTankRiskLevel,
  formatPercent,
} from "@/lib";
import { cn } from "@/lib/utils";

const HEALTH_ALERT_CATEGORIES = ["mortality", "health", "water_quality", "biosecurity"];

export default function HealthPage() {
  const { tanks, dashboard, recommendations, getActiveAlerts, getZoneById, source, loading } =
    useAppData();

  const activeAlerts = getActiveAlerts();
  const healthAlerts = activeAlerts.filter((a) => HEALTH_ALERT_CATEGORIES.includes(a.category));

  const healthRecs = recommendations.filter(
    (r) => (r.category === "health" || r.category === "biosecurity") && r.status === "pending",
  );

  // Worst-health tanks first.
  const tanksByHealth = [...tanks].sort((a, b) => a.healthScore - b.healthScore);

  const avgMortality =
    tanks.length > 0
      ? tanks.reduce((sum, t) => sum + t.mortalityRatePercent, 0) / tanks.length
      : 0;
  const atRiskCount = tanks.filter((t) => t.status === "warning" || t.status === "critical").length;

  return (
    <AppShell activePath="/health" title="Health" alertCount={activeAlerts.length}>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold text-on-surface">Health Monitoring</h1>
          <p className="mt-1 text-sm text-on-surface-variant">
            Population health, mortality risk, and water-quality status across all cohorts
          </p>
        </div>
        <span
          className={cn(
            "shrink-0 rounded-full border px-3 py-1 text-xs font-medium",
            source === "live"
              ? "border-primary/30 bg-primary/10 text-primary"
              : "border-white/10 bg-white/5 text-on-surface-variant",
          )}
        >
          {loading ? "Loading…" : source === "live" ? "Live data" : "Demo data"}
        </span>
      </div>

      <div className="flex flex-col gap-6 xl:flex-row">
        <div className="min-w-0 flex-1 space-y-6">
          {/* Top summary */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <HealthScoreCard
                score={dashboard.farmHealthScore.score}
                trendPercent={dashboard.farmHealthScore.trendPercent}
                operationalMeta={dashboard.farmHealthOperational}
                variant="hero"
              />
            </div>
            <div className="flex flex-col gap-4">
              <SummaryStatCard
                label="Mortality Risk"
                value={`${dashboard.mortalityRisk.value}${dashboard.mortalityRisk.unit}`}
                valueClassName="text-warning"
                subValue={
                  <p className="mt-1 text-xs text-on-surface-variant">
                    {dashboard.mortalityRisk.classification} — {dashboard.mortalityRisk.description}
                  </p>
                }
              />
              <SummaryStatCard
                label="PSI Average"
                value={String(dashboard.psiAverage.value)}
                subValue={
                  <p className="mt-1 text-xs text-on-surface-variant">
                    {dashboard.psiAverage.description}
                  </p>
                }
              />
            </div>
          </div>

          {/* Water-quality / health metrics */}
          <section>
            <h2 className="mb-3 text-sm font-semibold text-on-surface">Water Quality & Environment</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 lg:gap-4">
              {dashboard.environmentalMetrics.map((metric) => (
                <MetricCard key={metric.id} metric={metric} sparkline={metric.sparkline} variant="compact" />
              ))}
            </div>
          </section>

          {/* Tank health breakdown */}
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-on-surface">Tank Health</h2>
              <span className="text-xs text-on-surface-variant">
                {atRiskCount} at risk · avg mortality {formatPercent(avgMortality)}
              </span>
            </div>
            <div className="overflow-hidden rounded-2xl border border-white/5">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-white/5 text-left text-xs uppercase tracking-wider text-on-surface-variant">
                    <th className="px-4 py-2 font-medium">Tank</th>
                    <th className="px-4 py-2 font-medium">Zone</th>
                    <th className="px-4 py-2 font-medium">Health</th>
                    <th className="px-4 py-2 font-medium">Status</th>
                    <th className="px-4 py-2 text-right font-medium">Mortality</th>
                    <th className="px-4 py-2 text-right font-medium">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {tanksByHealth.map((tank) => {
                    const zone = getZoneById(tank.zoneId);
                    const risk = getTankRiskLevel(tank);
                    return (
                      <tr key={tank.id} className="border-t border-white/5 hover:bg-white/5">
                        <td className="px-4 py-2 font-medium text-on-surface">{tank.name}</td>
                        <td className="px-4 py-2 text-on-surface-variant">{zone?.name ?? "—"}</td>
                        <td className="px-4 py-2">
                          <div className="flex items-center gap-2">
                            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/10">
                              <div
                                className={cn(
                                  "h-full rounded-full",
                                  tank.healthScore >= 80
                                    ? "bg-primary"
                                    : tank.healthScore >= 60
                                      ? "bg-warning"
                                      : "bg-error",
                                )}
                                style={{ width: `${Math.max(0, Math.min(100, tank.healthScore))}%` }}
                              />
                            </div>
                            <span className="tabular-nums text-on-surface">{Math.round(tank.healthScore)}</span>
                          </div>
                        </td>
                        <td className="px-4 py-2">
                          <span
                            className={cn(
                              "rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                              getTankHealthStatusStyle(tank.status),
                            )}
                          >
                            {getTankHealthStatusLabel(tank.status)}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right tabular-nums text-on-surface-variant">
                          {formatPercent(tank.mortalityRatePercent)}
                        </td>
                        <td className="px-4 py-2 text-right text-on-surface-variant">
                          {getTankRiskLabel(risk)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {/* Right column */}
        <aside className="w-full shrink-0 space-y-6 xl:w-80 2xl:w-96">
          <section>
            <h2 className="mb-4 text-xs font-bold uppercase tracking-widest text-on-surface-variant">
              Health Recommendations
            </h2>
            <DashboardRecommendations recommendations={healthRecs} />
          </section>

          <section>
            <h2 className="mb-4 text-xs font-bold uppercase tracking-widest text-on-surface-variant">
              Health Alerts ({healthAlerts.length})
            </h2>
            <div className="space-y-2">
              {healthAlerts.length === 0 ? (
                <p className="rounded-xl border border-white/5 bg-white/5 px-4 py-6 text-center text-xs text-on-surface-variant">
                  No active health alerts.
                </p>
              ) : (
                healthAlerts.slice(0, 6).map((alert) => (
                  <AlertCard
                    key={alert.id}
                    alert={alert}
                    zoneCode={getZoneById(alert.zoneId)?.code}
                    variant="compact"
                  />
                ))
              )}
            </div>
          </section>
        </aside>
      </div>
    </AppShell>
  );
}
