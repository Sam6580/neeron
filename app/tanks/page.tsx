"use client";

import { AppShell } from "@/components/layout";
import { TankManagementGrid } from "@/components/tanks/TankManagementGrid";
import { useAppData } from "@/lib/hooks/useAppData";

export default function TankManagementPage() {
  const { tanks, getActiveAlerts, getZoneById, source, loading } = useAppData();
  const activeAlerts = getActiveAlerts();

  const tanksWithZones = tanks.map((tank) => {
    const zone = getZoneById(tank.zoneId);
    return {
      tank,
      zoneName: zone?.name ?? "Production Site",
      zoneCode: zone?.code ?? "—",
    };
  });

  return (
    <AppShell activePath="/tanks" title="Tank Management" alertCount={activeAlerts.length}>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold text-on-surface">Tank Management</h1>
          <p className="mt-1 text-sm text-on-surface-variant">
            Monitor all production units — sea cages, RAS systems, and smolt facilities
          </p>
        </div>
        <span
          className={
            "shrink-0 rounded-full border px-3 py-1 text-xs font-medium " +
            (source === "live"
              ? "border-primary/30 bg-primary/10 text-primary"
              : "border-white/10 bg-white/5 text-on-surface-variant")
          }
        >
          {loading ? "Loading…" : source === "live" ? "Live data" : "Demo data"}
        </span>
      </div>

      <TankManagementGrid tanks={tanksWithZones} />
    </AppShell>
  );
}
