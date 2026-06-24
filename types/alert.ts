export type AlertSeverity = "info" | "warning" | "critical";

export type AlertStatus = "active" | "acknowledged" | "resolved";

export type AlertCategory =
  | "water_quality"
  | "mortality"
  | "equipment"
  | "biosecurity"
  | "feeding"
  | "environment";

export interface Alert {
  id: string;
  tankId: string | null;
  zoneId: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  status: AlertStatus;
  category: AlertCategory;
  metric: string | null;
  threshold: string | null;
  currentValue: string | null;
  triggeredAt: string;
  acknowledgedAt: string | null;
  resolvedAt: string | null;
}
