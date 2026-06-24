import type { AnalyticsMetric, Zone } from "@/types";
import { tanks } from "./tanks";
import { zones } from "./zones";

const activeTanks = tanks.filter(
  (t) => t.status !== "maintenance" && t.status !== "offline",
);

function average(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

export function getFarmHealthScore(): { score: number; trendPercent: number } {
  const score = Math.round(average(zones.map((z) => z.avgHealthScore)) * 10) / 10;
  return { score, trendPercent: 2.4 };
}

export const farmHealthOperational = {
  psiAverage: 2.4,
  riskLevel: "Moderate" as const,
  lastUpdatedMinutesAgo: 2,
};

export const mortalityRisk = {
  value: 12,
  unit: "%",
  classification: "Low Risk" as const,
  description: "7-day predictive mortality forecast across active cohorts",
};

export const psiAverage = {
  value: 2.4,
  label: "PSI Average",
  description: "Population Stress Index across active sea cages",
};

export const riskTrend = {
  direction: "down" as const,
  label: "Downwards",
  description: "Composite biosecurity and water quality risk index",
};

export const historicalCaseMatch = {
  scenarioId: "812",
  similarity: 94,
  expectedRecoveryHours: 14,
  outcomeConfidence: 94,
  summary:
    "Similar environmental drift detected in Q3 2023. Outcome: Successfully stabilized within 14h using adaptive cooling protocols.",
  recommendedActions: [
    "Activate diffused aeration in affected cages",
    "Reduce feed ration by 10–15% for 48 hours",
    "Increase dissolved oxygen monitoring to 15-minute intervals",
  ],
};

const sparkline = (base: number, variance: number, points = 12): number[] =>
  Array.from({ length: points }, (_, i) => {
    const wave = Math.sin(i * 0.8) * variance;
    return Math.round((base + wave) * 100) / 100;
  });

export function getEnvironmentalMetrics(): (AnalyticsMetric & {
  sparkline: number[];
})[] {
  const seaCages = activeTanks.filter((t) => t.type === "sea_cage");

  const avgTemp = average(activeTanks.map((t) => t.lastReading.temperatureC));
  const avgPh = average(activeTanks.map((t) => t.lastReading.ph));
  const avgDo = average(activeTanks.map((t) => t.lastReading.dissolvedOxygenMgL));
  const avgSalinity = average(seaCages.map((t) => t.lastReading.salinityPpt));
  const avgAmmonia = average(activeTanks.map((t) => t.lastReading.ammoniaMgL));

  return [
    {
      id: "env-temperature",
      label: "Temperature",
      value: avgTemp,
      unit: "°C",
      category: "environment",
      trend: "up",
      trendPercent: 4.5,
      status: avgTemp > 12 ? "warning" : "good",
      target: 12.0,
      previousValue: avgTemp - 0.5,
      period: "24h avg",
      sparkline: sparkline(avgTemp, 0.8),
    },
    {
      id: "env-ph",
      label: "pH Level",
      value: avgPh,
      unit: "",
      category: "water_quality",
      trend: "stable",
      trendPercent: 0.1,
      status: "good",
      target: 7.8,
      previousValue: avgPh,
      period: "24h avg",
      sparkline: sparkline(avgPh, 0.05),
    },
    {
      id: "env-do",
      label: "D. Oxygen",
      value: avgDo,
      unit: "mg/L",
      category: "water_quality",
      trend: "down",
      trendPercent: 2.1,
      status: avgDo < 7.5 ? "critical" : avgDo < 8.0 ? "warning" : "good",
      target: 8.0,
      previousValue: avgDo + 0.2,
      period: "24h avg",
      sparkline: sparkline(avgDo, 0.6),
    },
    {
      id: "env-salinity",
      label: "Salinity",
      value: avgSalinity,
      unit: "ppt",
      category: "water_quality",
      trend: "stable",
      trendPercent: 0.2,
      status: "good",
      target: 32.0,
      previousValue: avgSalinity,
      period: "24h avg",
      sparkline: sparkline(avgSalinity, 0.4),
    },
    {
      id: "env-ammonia",
      label: "Ammonia",
      value: avgAmmonia,
      unit: "ppm",
      category: "water_quality",
      trend: "up",
      trendPercent: 8.0,
      status: avgAmmonia > 0.025 ? "warning" : "good",
      target: 0.025,
      previousValue: avgAmmonia - 0.002,
      period: "24h avg",
      sparkline: sparkline(avgAmmonia, 0.004),
    },
  ];
}

export interface ZoneOverview extends Zone {
  population: number;
  displayStatus: "optimal" | "warning" | "critical";
  updatedMinutesAgo: number;
}

export function getZoneOverviews(): ZoneOverview[] {
  return zones.map((zone) => {
    const zoneTanks = tanks.filter((t) => t.zoneId === zone.id);
    const population = zoneTanks.reduce((sum, t) => sum + t.fishCount, 0);

    let displayStatus: ZoneOverview["displayStatus"] = "optimal";
    if (zone.status === "degraded" || zone.avgHealthScore < 75) {
      displayStatus = "warning";
    }
    if (zone.avgHealthScore < 60) {
      displayStatus = "critical";
    }

    return {
      ...zone,
      population,
      displayStatus,
      updatedMinutesAgo: zone.id === "zone-chiloé" ? 8 : zone.id === "zone-loch-duich" ? 3 : 5,
    };
  });
}
