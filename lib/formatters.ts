import type { TankStatus, AlertSeverity, MetricStatus } from "@/types";

export function getTankStatusLabel(status: TankStatus): string {
  const labels: Record<TankStatus, string> = {
    healthy: "Healthy",
    warning: "Warning",
    critical: "Critical",
    offline: "Offline",
    maintenance: "Maintenance",
  };
  return labels[status];
}

export function getAlertSeverityLabel(severity: AlertSeverity): string {
  const labels: Record<AlertSeverity, string> = {
    info: "Info",
    warning: "Warning",
    critical: "Critical",
  };
  return labels[severity];
}

export function getMetricStatusLabel(status: MetricStatus): string {
  const labels: Record<MetricStatus, string> = {
    good: "On Target",
    warning: "Attention",
    critical: "Critical",
    neutral: "Stable",
  };
  return labels[status];
}

export function getHealthScoreStatus(score: number): MetricStatus {
  if (score >= 80) return "good";
  if (score >= 60) return "warning";
  return "critical";
}

export function getTankStatusColor(status: TankStatus): string {
  const colors: Record<TankStatus, string> = {
    healthy: "text-emerald-600 bg-emerald-50 border-emerald-200",
    warning: "text-amber-600 bg-amber-50 border-amber-200",
    critical: "text-red-600 bg-red-50 border-red-200",
    offline: "text-slate-500 bg-slate-50 border-slate-200",
    maintenance: "text-blue-600 bg-blue-50 border-blue-200",
  };
  return colors[status];
}

export function getAlertSeverityColor(severity: AlertSeverity): string {
  const colors: Record<AlertSeverity, string> = {
    info: "text-sky-600 bg-sky-50 border-sky-200",
    warning: "text-amber-600 bg-amber-50 border-amber-200",
    critical: "text-red-600 bg-red-50 border-red-200",
  };
  return colors[severity];
}

export function getMetricStatusColor(status: MetricStatus): string {
  const colors: Record<MetricStatus, string> = {
    good: "text-emerald-600",
    warning: "text-amber-600",
    critical: "text-red-600",
    neutral: "text-slate-500",
  };
  return colors[status];
}

export function getTrendColor(trend: "up" | "down" | "stable", invert = false): string {
  if (trend === "stable") return "text-on-surface-variant";

  const isPositive = trend === "up";
  const positiveIsGood = !invert;

  if (isPositive === positiveIsGood) return "text-primary";
  return "text-error";
}
