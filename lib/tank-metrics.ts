import type { Tank, TankStatus } from "@/types";
import { getZoneById } from "@/data/zones";

export type TankRiskLevel = "low" | "moderate" | "high" | "critical" | "offline";

export function getTankDisplayId(tank: Tank): string {
  const zone = getZoneById(tank.zoneId);
  const zoneCode = zone?.code.split("-")[0] ?? "TK";
  const suffix = tank.id.split("-").pop()?.toUpperCase() ?? tank.id.slice(-3).toUpperCase();
  const typePrefix =
    tank.type === "ras" ? "R" : tank.type === "smolt" ? "S" : "C";
  return `${zoneCode}-${typePrefix}${suffix.replace(/\D/g, "").padStart(2, "0") || suffix}`;
}

export function getTankBiomassKg(tank: Tank): number {
  return Math.round(tank.fishCount * tank.avgWeightKg);
}

export function computePsiScore(tank: Tank): number {
  if (tank.status === "maintenance" || tank.status === "offline" || tank.fishCount === 0) {
    return 0;
  }

  const { lastReading } = tank;
  const doStress = Math.max(0, (8.0 - lastReading.dissolvedOxygenMgL) / 2.5);
  const ammoniaStress = lastReading.ammoniaMgL / 0.03;
  const mortalityStress = tank.mortalityRatePercent / 0.5;
  const healthStress = (100 - tank.healthScore) / 100;

  const raw =
    doStress * 0.35 +
    ammoniaStress * 0.2 +
    mortalityStress * 0.25 +
    healthStress * 0.2;

  return Math.round(Math.min(5, Math.max(1, 1 + raw * 2.8)) * 10) / 10;
}

export function getTankRiskLevel(tank: Tank): TankRiskLevel {
  if (tank.status === "offline" || tank.status === "maintenance") return "offline";
  if (tank.status === "critical" || tank.healthScore < 60) return "critical";
  if (tank.status === "warning" || tank.healthScore < 75) return "high";
  if (tank.healthScore < 85 || computePsiScore(tank) > 2.5) return "moderate";
  return "low";
}

export function getTankRiskLabel(risk: TankRiskLevel): string {
  const labels: Record<TankRiskLevel, string> = {
    low: "Low Risk",
    moderate: "Moderate Risk",
    high: "High Risk",
    critical: "Critical Risk",
    offline: "Offline",
  };
  return labels[risk];
}

export function getTankHealthStatusLabel(status: TankStatus): string {
  const labels: Record<TankStatus, string> = {
    healthy: "Optimal",
    warning: "Warning",
    critical: "Critical",
    offline: "Offline",
    maintenance: "Maintenance",
  };
  return labels[status];
}

export function getTankHealthStatusStyle(status: TankStatus): string {
  const styles: Record<TankStatus, string> = {
    healthy: "badge-optimal",
    warning: "badge-warning",
    critical: "badge-critical",
    offline: "text-on-surface-variant bg-white/5 border border-white/10",
    maintenance: "text-secondary bg-secondary/10 border border-secondary/20",
  };
  return styles[status];
}

export function getPsiStatusStyle(psi: number): string {
  if (psi === 0) return "text-on-surface-variant";
  if (psi <= 2.0) return "text-primary";
  if (psi <= 3.0) return "text-warning";
  return "text-error";
}
