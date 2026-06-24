export type MetricTrend = "up" | "down" | "stable";

export type MetricStatus = "good" | "warning" | "critical" | "neutral";

export type MetricCategory =
  | "production"
  | "water_quality"
  | "health"
  | "feed"
  | "mortality"
  | "environment";

export interface AnalyticsMetric {
  id: string;
  label: string;
  value: number;
  unit: string;
  category: MetricCategory;
  trend: MetricTrend;
  trendPercent: number;
  status: MetricStatus;
  target: number | null;
  previousValue: number;
  period: string;
}
