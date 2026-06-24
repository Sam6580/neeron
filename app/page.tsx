import { AppShell } from "@/components/layout";
import { HealthScoreCard, MetricCard, SummaryStatCard, AlertCard } from "@/components/cards";
import { ZoneOverviewCard } from "@/components/tanks";
import { DashboardRecommendations, HistoricalCaseMatch } from "@/components/dashboard";
import {
  farmHealthOperational,
  getActiveAlerts,
  getEnvironmentalMetrics,
  getFarmHealthScore,
  getZoneOverviews,
  mortalityRisk,
  recommendations,
  riskTrend,
} from "@/data";
import { getZoneById } from "@/data/zones";

export default function FarmCommandCenterPage() {
  const { score, trendPercent } = getFarmHealthScore();
  const environmentalMetrics = getEnvironmentalMetrics();
  const zoneOverviews = getZoneOverviews();
  const activeAlerts = getActiveAlerts();
  const pendingRecommendations = recommendations.filter(
    (rec) => rec.status === "pending",
  );

  return (
    <AppShell title="Farm Command Center" alertCount={activeAlerts.length}>
      <div className="mb-2 hidden lg:block">
        <h1 className="text-lg font-semibold text-on-surface">Farm Command Center</h1>
        <p className="text-sm text-on-surface-variant">
          Real-time Atlantic Salmon operations across all active sites
        </p>
      </div>

      <div className="flex flex-col gap-6 xl:flex-row">
        {/* Main content */}
        <div className="min-w-0 flex-1 space-y-6">
          {/* Top summary row */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <HealthScoreCard
              score={score}
              trendPercent={trendPercent}
              operationalMeta={farmHealthOperational}
              variant="hero"
            />
            <SummaryStatCard
              label="Mortality Risk"
              value={`${mortalityRisk.value}${mortalityRisk.unit}`}
              subValue={
                <p className="text-xs font-semibold text-primary">
                  {mortalityRisk.classification}
                </p>
              }
            />
            <SummaryStatCard
              label="Risk Trend"
              value={riskTrend.label}
              valueClassName="text-error"
              trend="down"
              subValue={
                <p className="text-xs text-on-surface-variant">{riskTrend.description}</p>
              }
            />
          </div>

          {/* Environmental metrics */}
          <section>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 lg:gap-4">
              {environmentalMetrics.map((metric) => (
                <MetricCard
                  key={metric.id}
                  metric={metric}
                  sparkline={metric.sparkline}
                  variant="compact"
                />
              ))}
            </div>
          </section>

          {/* Active zones */}
          <section>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-on-surface">
                Active Zones
              </h2>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="rounded-full border border-white/10 px-3 py-1.5 text-xs font-medium text-on-surface-variant transition-colors hover:border-white/20 hover:text-on-surface"
                >
                  Filter
                </button>
                <button
                  type="button"
                  className="rounded-full border border-white/10 px-3 py-1.5 text-xs font-medium text-on-surface-variant transition-colors hover:border-white/20 hover:text-on-surface"
                >
                  View All
                </button>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {zoneOverviews.map((zone) => (
                <ZoneOverviewCard key={zone.id} zone={zone} />
              ))}
            </div>
          </section>
        </div>

        {/* Right AI panel */}
        <aside className="w-full shrink-0 space-y-6 xl:w-80 2xl:w-96">
          {/* AI Recommendations */}
          <section>
            <div className="mb-4 flex items-center gap-2">
              <svg className="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
              </svg>
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                AI Recommendations
              </h2>
            </div>
            <DashboardRecommendations recommendations={pendingRecommendations} />
          </section>

          {/* Historical case match */}
          <HistoricalCaseMatch />

          {/* Active alerts */}
          <section>
            <div className="mb-4 flex items-center gap-2">
              <svg className="h-4 w-4 text-warning" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
              </svg>
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                Active Alerts
              </h2>
            </div>
            <div className="space-y-2">
              {activeAlerts.slice(0, 4).map((alert) => (
                <AlertCard
                  key={alert.id}
                  alert={alert}
                  zoneCode={getZoneById(alert.zoneId)?.code}
                  variant="compact"
                />
              ))}
            </div>
          </section>
        </aside>
      </div>

      {/* Floating action button */}
      <button
        type="button"
        aria-label="Add new item"
        className="btn-primary-gradient fixed bottom-6 right-6 flex h-14 w-14 items-center justify-center rounded-full text-white shadow-[0_0_30px_rgba(0,210,255,0.4)] transition-all hover:scale-105"
      >
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </button>
    </AppShell>
  );
}
