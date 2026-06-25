"use client";

import { useEffect, useState } from "react";
import { uiApi } from "@/lib/api/resources";
import type { DashboardData } from "@/lib/api/types";
import type {
  Alert,
  AnalyticsMetric,
  BiosecurityRecord,
  Recommendation,
  Tank,
  Zone,
} from "@/types";

// Demo content used as an instant first render and as a fallback when the
// backend is unreachable.
import { tanks as demoTanks } from "@/data/tanks";
import { zones as demoZones } from "@/data/zones";
import { alerts as demoAlerts } from "@/data/alerts";
import { recommendations as demoRecommendations } from "@/data/recommendations";
import { biosecurityRecords as demoBiosecurity } from "@/data/biosecurity";
import { analyticsMetrics as demoAnalytics } from "@/data/analytics";
import {
  getFarmHealthScore,
  getEnvironmentalMetrics,
  getZoneOverviews,
  farmHealthOperational,
  mortalityRisk,
  psiAverage,
  riskTrend,
  historicalCaseMatch,
} from "@/data/dashboard";

const demoDashboard: DashboardData = {
  farmHealthScore: getFarmHealthScore(),
  environmentalMetrics: getEnvironmentalMetrics(),
  zoneOverviews: getZoneOverviews(),
  farmHealthOperational,
  mortalityRisk,
  psiAverage,
  riskTrend,
  historicalCaseMatch,
};

export interface AppData {
  zones: Zone[];
  tanks: Tank[];
  alerts: Alert[];
  recommendations: Recommendation[];
  biosecurity: BiosecurityRecord[];
  analytics: AnalyticsMetric[];
  dashboard: DashboardData;
  source: "live" | "demo";
  loading: boolean;
  // helpers (mirror the @/data helpers, computed over the active dataset)
  getActiveAlerts: () => Alert[];
  getZoneById: (id: string) => Zone | undefined;
  getTankById: (id: string) => Tank | undefined;
}

const demoState = {
  zones: demoZones,
  tanks: demoTanks,
  alerts: demoAlerts,
  recommendations: demoRecommendations,
  biosecurity: demoBiosecurity,
  analytics: demoAnalytics,
  dashboard: demoDashboard,
};

/**
 * Loads all view collections from the backend in parallel. Falls back to the
 * bundled demo content per-collection if a request fails, so the UI always
 * renders. Returns helper accessors mirroring the old @/data helpers.
 */
export function useAppData(): AppData {
  const [state, setState] = useState(demoState);
  const [source, setSource] = useState<"live" | "demo">("demo");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    (async () => {
      const [
        zones,
        tanks,
        alerts,
        recommendations,
        biosecurity,
        analytics,
        dashboard,
      ] = await Promise.allSettled([
        uiApi.zones(),
        uiApi.tanks(),
        uiApi.alerts(),
        uiApi.recommendations(),
        uiApi.biosecurity(),
        uiApi.analytics(),
        uiApi.dashboard(),
      ]);
      if (!active) return;

      const pick = <T,>(r: PromiseSettledResult<T>, fallback: T): [T, boolean] =>
        r.status === "fulfilled" && r.value ? [r.value, true] : [fallback, false];

      const [z, z1] = pick(zones, demoState.zones);
      const [t, t1] = pick(tanks, demoState.tanks);
      const [a, a1] = pick(alerts, demoState.alerts);
      const [rec, r1] = pick(recommendations, demoState.recommendations);
      const [bio, b1] = pick(biosecurity, demoState.biosecurity);
      const [an, an1] = pick(analytics, demoState.analytics);
      const [dash, d1] = pick(dashboard, demoState.dashboard);

      setState({
        zones: z,
        tanks: t,
        alerts: a,
        recommendations: rec,
        biosecurity: bio,
        analytics: an,
        dashboard: dash,
      });
      setSource(z1 && t1 && a1 && r1 && b1 && an1 && d1 ? "live" : "demo");
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  return {
    ...state,
    source,
    loading,
    getActiveAlerts: () => state.alerts.filter((al) => al.status === "active"),
    getZoneById: (id: string) => state.zones.find((zn) => zn.id === id),
    getTankById: (id: string) => state.tanks.find((tk) => tk.id === id),
  };
}
