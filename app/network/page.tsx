"use client";

import { AppShell } from "@/components/layout";
import { SummaryStatCard, AlertCard } from "@/components/cards";
import { useAppData } from "@/lib/hooks/useAppData";
import { formatCompact, formatRelativeTime } from "@/lib";
import { cn } from "@/lib/utils";

const ZONE_STATUS_STYLE: Record<string, string> = {
  operational: "border-primary/30 bg-primary/10 text-primary",
  degraded: "border-warning/30 bg-warning/10 text-warning",
  restricted: "border-warning/30 bg-warning/10 text-warning",
  offline: "border-error/30 bg-error/10 text-error",
};

const INFRA_ALERT_CATEGORIES = ["equipment", "environment"];

function tankOnline(status: string): boolean {
  return status !== "offline" && status !== "maintenance";
}

export default function NetworkStatusPage() {
  const { zones, tanks, getActiveAlerts, getZoneById, source, loading } = useAppData();

  const activeAlerts = getActiveAlerts();
  const infraAlerts = activeAlerts.filter((a) => INFRA_ALERT_CATEGORIES.includes(a.category));

  const zonesOnline = zones.filter((z) => z.status === "operational").length;
  const tanksReporting = tanks.filter((t) => tankOnline(t.status)).length;
  const reportingPct = tanks.length > 0 ? Math.round((tanksReporting / tanks.length) * 100) : 0;

  // Telemetry freshness: most recent reading across tanks.
  const lastTimestamps = tanks
    .map((t) => t.lastReading?.timestamp)
    .filter((x): x is string => Boolean(x))
    .sort();
  const lastSeen = lastTimestamps.length > 0 ? lastTimestamps[lastTimestamps.length - 1] : null;

  const systemStatus = infraAlerts.some((a) => a.severity === "critical")
    ? { label: "Degraded", style: "text-error" }
    : infraAlerts.length > 0
      ? { label: "Warning", style: "text-warning" }
      : { label: "Operational", style: "text-primary" };

  return (
    <AppShell activePath="/network" title="Network Status" alertCount={activeAlerts.length}>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold text-on-surface">Network &amp; Device Status</h1>
          <p className="mt-1 text-sm text-on-surface-variant">
            Connectivity, telemetry throughput, and infrastructure health across all sites
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

      {/* System summary */}
      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryStatCard
          label="System Status"
          value={systemStatus.label}
          valueClassName={systemStatus.style}
          subValue={
            <p className="mt-1 text-xs text-on-surface-variant">
              {infraAlerts.length} infrastructure alert{infraAlerts.length === 1 ? "" : "s"}
            </p>
          }
        />
        <SummaryStatCard
          label="Sites Online"
          value={`${zonesOnline} / ${zones.length}`}
          subValue={<p className="mt-1 text-xs text-on-surface-variant">Operational zones</p>}
        />
        <SummaryStatCard
          label="Tanks Reporting"
          value={`${reportingPct}%`}
          subValue={
            <p className="mt-1 text-xs text-on-surface-variant">
              {tanksReporting} of {tanks.length} units streaming
            </p>
          }
        />
        <SummaryStatCard
          label="Last Telemetry"
          value={lastSeen ? formatRelativeTime(lastSeen) : "—"}
          subValue={<p className="mt-1 text-xs text-on-surface-variant">Most recent sensor reading</p>}
        />
      </div>

      {/* Zone connectivity */}
      <section className="mb-6">
        <h2 className="mb-3 text-sm font-semibold text-on-surface">Site Connectivity</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {zones.map((zone) => (
            <div key={zone.id} className="glass-panel rounded-2xl p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-on-surface">{zone.code}</h3>
                <span
                  className={cn(
                    "rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                    ZONE_STATUS_STYLE[zone.status] ?? "border-white/10 bg-white/5 text-on-surface-variant",
                  )}
                >
                  {zone.status}
                </span>
              </div>
              <p className="mt-1 text-xs text-on-surface-variant">{zone.name}</p>
              <div className="mt-3 flex items-center justify-between text-xs text-on-surface-variant">
                <span>{zone.tankCount} units</span>
                <span>{formatCompact(zone.totalBiomassKg)} kg</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Tank telemetry status */}
      <section className="mb-6">
        <h2 className="mb-3 text-sm font-semibold text-on-surface">Telemetry Streams</h2>
        <div className="overflow-hidden rounded-2xl border border-white/5">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-white/5 text-left text-xs uppercase tracking-wider text-on-surface-variant">
                <th className="px-4 py-2 font-medium">Unit</th>
                <th className="px-4 py-2 font-medium">Site</th>
                <th className="px-4 py-2 font-medium">Stream</th>
                <th className="px-4 py-2 text-right font-medium">Last Reading</th>
              </tr>
            </thead>
            <tbody>
              {tanks.map((tank) => {
                const online = tankOnline(tank.status);
                return (
                  <tr key={tank.id} className="border-t border-white/5 hover:bg-white/5">
                    <td className="px-4 py-2 font-medium text-on-surface">{tank.name}</td>
                    <td className="px-4 py-2 text-on-surface-variant">
                      {getZoneById(tank.zoneId)?.code ?? "—"}
                    </td>
                    <td className="px-4 py-2">
                      <span className="inline-flex items-center gap-1.5">
                        <span
                          className={cn(
                            "h-2 w-2 rounded-full",
                            online ? "bg-primary shadow-[0_0_6px_rgba(71,214,255,0.7)]" : "bg-error",
                          )}
                        />
                        <span className={online ? "text-on-surface" : "text-error"}>
                          {online ? "Online" : "Offline"}
                        </span>
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right text-on-surface-variant">
                      {tank.lastReading?.timestamp ? formatRelativeTime(tank.lastReading.timestamp) : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Infrastructure alerts */}
      <section>
        <h2 className="mb-3 text-sm font-semibold text-on-surface">
          Infrastructure Alerts ({infraAlerts.length})
        </h2>
        {infraAlerts.length === 0 ? (
          <p className="rounded-xl border border-white/5 bg-white/5 px-4 py-6 text-center text-xs text-on-surface-variant">
            No active equipment or environment alerts.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {infraAlerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} zoneCode={getZoneById(alert.zoneId)?.code} />
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}
