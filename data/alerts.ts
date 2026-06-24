import type { Alert } from "@/types";

export const alerts: Alert[] = [
  {
    id: "alert-001",
    tankId: "tank-ch-cage-05",
    zoneId: "zone-chiloé",
    title: "Dissolved oxygen below threshold",
    message:
      "DO reading of 6.4 mg/L is below the 7.0 mg/L critical threshold for harvest-size Atlantic Salmon at current biomass density.",
    severity: "critical",
    status: "active",
    category: "water_quality",
    metric: "Dissolved Oxygen",
    threshold: "≥ 7.0 mg/L",
    currentValue: "6.4 mg/L",
    triggeredAt: "2026-06-22T06:55:00Z",
    acknowledgedAt: null,
    resolvedAt: null,
  },
  {
    id: "alert-002",
    tankId: "tank-ld-cage-07",
    zoneId: "zone-loch-duich",
    title: "Elevated ammonia detected",
    message:
      "Ammonia levels at 0.028 mg/L exceed the warning threshold. May indicate reduced water exchange or overfeeding in the past 48 hours.",
    severity: "warning",
    status: "active",
    category: "water_quality",
    metric: "Total Ammonia",
    threshold: "≤ 0.025 mg/L",
    currentValue: "0.028 mg/L",
    triggeredAt: "2026-06-22T07:12:00Z",
    acknowledgedAt: null,
    resolvedAt: null,
  },
  {
    id: "alert-003",
    tankId: "tank-ch-cage-05",
    zoneId: "zone-chiloé",
    title: "Mortality rate spike detected",
    message:
      "7-day rolling mortality at 0.82% exceeds the 0.5% site threshold. Correlated with sea lice pressure and reduced feeding response.",
    severity: "critical",
    status: "acknowledged",
    category: "mortality",
    metric: "7-Day Mortality Rate",
    threshold: "≤ 0.5%",
    currentValue: "0.82%",
    triggeredAt: "2026-06-21T22:00:00Z",
    acknowledgedAt: "2026-06-22T01:15:00Z",
    resolvedAt: null,
  },
  {
    id: "alert-004",
    tankId: null,
    zoneId: "zone-hardanger",
    title: "Feed silo level low",
    message:
      "Primary feed silo at Hardanger site is at 12% capacity. Estimated 2.5 days remaining at current consumption rate.",
    severity: "warning",
    status: "active",
    category: "feeding",
    metric: "Silo Capacity",
    threshold: "≥ 20%",
    currentValue: "12%",
    triggeredAt: "2026-06-22T04:30:00Z",
    acknowledgedAt: null,
    resolvedAt: null,
  },
  {
    id: "alert-005",
    tankId: "tank-hf-cage-09",
    zoneId: "zone-hardanger",
    title: "Cage maintenance cycle complete",
    message:
      "Net cleaning and structural inspection completed. Cage ready for restocking with spring smolt batch.",
    severity: "info",
    status: "resolved",
    category: "equipment",
    metric: null,
    threshold: null,
    currentValue: null,
    triggeredAt: "2026-06-22T06:00:00Z",
    acknowledgedAt: "2026-06-22T06:15:00Z",
    resolvedAt: "2026-06-22T06:30:00Z",
  },
  {
    id: "alert-006",
    tankId: null,
    zoneId: "zone-chiloé",
    title: "Harmful algal bloom risk elevated",
    message:
      "Satellite chlorophyll data and local water sampling indicate rising HAB risk in the southern sector. Monitor cage sites CH-05 through CH-08 closely.",
    severity: "warning",
    status: "active",
    category: "environment",
    metric: "Chlorophyll-a Index",
    threshold: "≤ 3.0 μg/L",
    currentValue: "4.2 μg/L",
    triggeredAt: "2026-06-22T03:00:00Z",
    acknowledgedAt: null,
    resolvedAt: null,
  },
];

export function getAlertById(id: string): Alert | undefined {
  return alerts.find((alert) => alert.id === id);
}

export function getActiveAlerts(): Alert[] {
  return alerts.filter((alert) => alert.status === "active");
}

export function getCriticalAlerts(): Alert[] {
  return alerts.filter(
    (alert) => alert.severity === "critical" && alert.status !== "resolved",
  );
}
