import { AppShell } from "@/components/layout";
import { TankManagementGrid } from "@/components/tanks/TankManagementGrid";
import { getActiveAlerts } from "@/data/alerts";
import { tanks } from "@/data/tanks";
import { getZoneById } from "@/data/zones";

export default function TankManagementPage() {
  const activeAlerts = getActiveAlerts();

  const tanksWithZones = tanks.map((tank) => {
    const zone = getZoneById(tank.zoneId);
    return {
      tank,
      zoneName: zone?.name ?? "Unknown Zone",
      zoneCode: zone?.code ?? "—",
    };
  });

  return (
    <AppShell activePath="/tanks" title="Tank Management" alertCount={activeAlerts.length}>
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-on-surface">Tank Management</h1>
        <p className="mt-1 text-sm text-on-surface-variant">
          Monitor all production units — sea cages, RAS systems, and smolt facilities
        </p>
      </div>

      <TankManagementGrid tanks={tanksWithZones} />
    </AppShell>
  );
}
