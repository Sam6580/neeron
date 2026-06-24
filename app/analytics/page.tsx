"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceDot,
  ReferenceLine,
  ReferenceArea,
} from "recharts";
import {
  formatCompact,
  formatNumber,
  formatPercent,
  formatRelativeTime,
  getPsiStatusStyle,
  getTankBiomassKg,
} from "@/lib";
import { cn } from "@/lib/utils";
import { tanks } from "@/data/tanks";
import { zones } from "@/data/zones";
import { analyticsMetrics } from "@/data/analytics";
import { getActiveAlerts } from "@/data/alerts";

// Interfaces for our Analytics Page
interface MLModel {
  name: string;
  accuracy: number;
  confidence: number;
  lastRetrained: string;
  status: "Active" | "Retraining" | "Offline";
}

interface AIInsightItem {
  id: string;
  message: string;
  priority: "low" | "medium" | "high" | "critical";
  confidence: number;
  zone: string;
  impact: string;
}

// Generate dynamic, mathematically consistent trend data for Recharts
const generateBiomassForecastData = (days: number) => {
  const points = 24;
  const historyPct = 0.7; // 70% history, 30% forecast
  const historyPoints = Math.round(points * historyPct);

  // Atlantic Salmon growth carrying capacity bounds
  const L = 2.15; // Carrying capacity (Million kg)
  const k = 0.025; // Growth coefficient
  const x0 = days === 30 ? 5 : days === 90 ? -10 : -40; // Logistic S-curve shift

  const logisticGrowth = (t: number) => {
    return L / (1 + Math.exp(-k * (t - x0)));
  };

  const currentDay = Math.round(historyPct * days);
  const fCurrent = logisticGrowth(0);
  const offsetScale = 1.67 - fCurrent; // curve passes through 1.67M kg at "Now"

  const data = [];
  for (let i = 0; i < points; i++) {
    const progress = i / (points - 1);
    const day = Math.round(progress * days);
    const t = day - currentDay;

    let label = "";
    if (t === 0) {
      label = "Now";
    } else if (t < 0) {
      label = `T-${Math.abs(t)}d`;
    } else {
      label = `T+${t}d`;
    }

    const baseValue = logisticGrowth(t) + offsetScale;
    let historical: number | null = null;
    let predicted = baseValue;

    if (i < historyPoints) {
      // Diurnal biological variation noise for historical authenticity
      const wave = Math.sin(day * 0.4) * 0.003;
      const noise = Math.sin(day * 2.3) * 0.002;
      historical = baseValue + wave + noise;
      predicted = historical;
    }

    let lowerBound = predicted;
    let upperBound = predicted;

    if (i >= historyPoints - 1) {
      const forecastProgress = (i - (historyPoints - 1)) / (points - historyPoints);
      const maxUncertainty = days === 30 ? 0.025 : days === 90 ? 0.065 : 0.15;
      const uncertainty = maxUncertainty * forecastProgress;
      lowerBound = predicted - uncertainty;
      upperBound = predicted + uncertainty;
    }

    data.push({
      label,
      day,
      historical: historical ? Math.round(historical * 1000) / 1000 : null,
      predicted: Math.round(predicted * 1000) / 1000,
      bounds: [Math.round(lowerBound * 1000) / 1000, Math.round(upperBound * 1000) / 1000],
    });
  }
  return data;
};

export default function AnalyticsPage() {
  const activeAlerts = getActiveAlerts();
  const [forecastDays, setForecastDays] = useState<30 | 90 | 180>(90);

  // Generate dynamic chart data based on active range selection
  const forecastData = useMemo(() => {
    return generateBiomassForecastData(forecastDays);
  }, [forecastDays]);

  const harvestTarget = useMemo(() => {
    return forecastDays === 30 ? 1.69 : forecastDays === 90 ? 1.78 : 1.98;
  }, [forecastDays]);

  const harvestWindowStart = useMemo(() => {
    const idx = Math.min(forecastData.length - 1, Math.round(forecastData.length * 0.82));
    return forecastData[idx]?.label || "";
  }, [forecastData]);

  const harvestWindowEnd = useMemo(() => {
    const idx = Math.min(forecastData.length - 1, Math.round(forecastData.length * 0.92));
    return forecastData[idx]?.label || "";
  }, [forecastData]);

  const accelPoint = useMemo(() => {
    const idx = Math.round(forecastData.length * 0.35);
    return {
      x: forecastData[idx]?.label || "",
      y: forecastData[idx]?.historical || 1.55
    };
  }, [forecastData]);

  // Aggregate zone metrics dynamically from tank mock data
  const zoneLeaderboard = useMemo(() => {
    return zones.map((zone) => {
      const zoneTanks = tanks.filter((t) => t.zoneId === zone.id);
      const activeTanks = zoneTanks.filter((t) => t.status !== "offline" && t.status !== "maintenance");
      
      const totalBiomassKg = zoneTanks.reduce((sum, t) => sum + getTankBiomassKg(t), 0);
      const avgHealth = zone.avgHealthScore;

      let growthRate = "+1.8%/wk";
      let trend: "up" | "down" | "stable" = "stable";
      let riskStatus: "optimal" | "warning" | "critical" = "optimal";

      if (zone.id === "zone-ras-bodø") {
        growthRate = "+2.8%/wk";
        trend = "up";
        riskStatus = "optimal";
      } else if (zone.id === "zone-hardanger") {
        growthRate = "+2.2%/wk";
        trend = "up";
        riskStatus = "optimal";
      } else if (zone.id === "zone-loch-duich") {
        growthRate = "+1.6%/wk";
        trend = "down";
        riskStatus = "warning";
      } else if (zone.id === "zone-chiloé") {
        growthRate = "+1.1%/wk";
        trend = "down";
        riskStatus = "critical";
      }

      return {
        id: zone.id,
        name: zone.name,
        healthScore: avgHealth,
        biomassTons: Math.round((totalBiomassKg / 1000) * 10) / 10,
        growthRate,
        riskStatus,
        trend,
        isTop: zone.id === "zone-ras-bodø",
      };
    }).sort((a, b) => b.healthScore - a.healthScore);
  }, []);

  // Section 7: ML Models mock dataset
  const activeModels: MLModel[] = [
    { name: "Water Quality Predictor", accuracy: 98.2, confidence: 95.0, lastRetrained: "12h ago", status: "Active" },
    { name: "Disease Outbreak Predictor", accuracy: 94.5, confidence: 91.0, lastRetrained: "3 days ago", status: "Active" },
    { name: "Mortality Risk Classifier", accuracy: 96.1, confidence: 92.5, lastRetrained: "24h ago", status: "Active" },
    { name: "Harvest Optimizer", accuracy: 92.8, confidence: 89.0, lastRetrained: "1 week ago", status: "Active" },
    { name: "Feed Efficiency Model", accuracy: 95.4, confidence: 93.0, lastRetrained: "2 days ago", status: "Active" },
  ];

  // Section 8: AI Insights Center dataset
  const aiInsights: AIInsightItem[] = [
    {
      id: "ins-01",
      message: "Zone Chiloé Cage 05 demonstrates an accelerating FCR trend (1.35) and depressed DO (6.4 mg/L). Shift 20% feed ratio to early morning hours to suppress stress.",
      priority: "critical",
      confidence: 94,
      zone: "Zone Chiloé",
      impact: "-14% Mortality Risk",
    },
    {
      id: "ins-02",
      message: "Water temperature projections at Loch Duich indicate localized temperature peak (12.2°C) on T+3d. Pre-emptive auxiliary oxygenation is recommended.",
      priority: "high",
      confidence: 88,
      zone: "Zone Loch Duich",
      impact: "+1.2 mg/L DO stability",
    },
    {
      id: "ins-03",
      message: "Biomass growth curve in Zone Hardanger Cage 01 has reached growth plateau optimization. Advancement of harvest by 5 days captures optimal pricing premium index.",
      priority: "medium",
      confidence: 92,
      zone: "Zone Hardanger",
      impact: "+$140k market premium",
    },
  ];

  // Section 1 Metric calculations from static database
  const biomassMetric = analyticsMetrics.find((m) => m.id === "metric-total-biomass");
  const fcrMetric = analyticsMetrics.find((m) => m.id === "metric-avg-fcr");
  const mortalityMetric = analyticsMetrics.find((m) => m.id === "metric-mortality-rate");
  const doMetric = analyticsMetrics.find((m) => m.id === "metric-avg-do");

  // Dynamic values for Section 2 forecast stats
  const estimatedHarvestBiomass = useMemo(() => {
    return forecastData[forecastData.length - 1].predicted;
  }, [forecastData]);

  return (
    <AppShell activePath="/analytics" title="Analytics Engine" alertCount={activeAlerts.length}>
      {/* Top Title Section */}
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-on-surface">Analytics Engine</h1>
        <p className="text-sm text-on-surface-variant">
          Predictive forecasting and biomass intelligence for aquaculture operations.
        </p>
      </div>

      {/* SECTION 1: Analytics Overview Header (KPIs) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        {/* KPI 1: Biomass Growth */}
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">Biomass Growth</span>
              <span className="text-xs font-bold text-primary flex items-center gap-0.5">
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
                </svg>
                {biomassMetric ? `${biomassMetric.trendPercent}%` : "—"}
              </span>
            </div>
            <p className="text-2xl font-semibold text-on-surface mt-2">
              {biomassMetric ? formatCompact(biomassMetric.value) : "—"} <span className="text-sm font-normal text-on-surface-variant">kg</span>
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>Target: 1.65M kg</span>
            <span className="badge-optimal px-1.5 py-0.5 rounded uppercase font-bold text-[8px]">Good</span>
          </div>
        </div>

        {/* KPI 2: Feed Conversion Ratio */}
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">Feed Conversion Ratio</span>
              <span className="text-xs font-bold text-primary flex items-center gap-0.5">
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
                </svg>
                {fcrMetric ? `${fcrMetric.trendPercent}%` : "—"}
              </span>
            </div>
            <p className="text-2xl font-semibold text-on-surface mt-2">
              {fcrMetric ? formatNumber(fcrMetric.value, 2) : "—"}
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>FCR Target: 1.15</span>
            <span className="badge-optimal px-1.5 py-0.5 rounded uppercase font-bold text-[8px]">Optimal</span>
          </div>
        </div>

        {/* KPI 3: Water Quality Stability */}
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">Water Quality Stability</span>
              <span className="text-xs font-bold text-primary flex items-center gap-0.5">
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
                </svg>
                0.5%
              </span>
            </div>
            <p className="text-2xl font-semibold text-on-surface mt-2">94.8%</p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>vs. 24h baseline</span>
            <span className="badge-optimal px-1.5 py-0.5 rounded uppercase font-bold text-[8px]">Stable</span>
          </div>
        </div>

        {/* KPI 4: Oxygen Saturation */}
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">Oxygen Saturation</span>
              <span className="text-xs font-bold text-error flex items-center gap-0.5">
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
                </svg>
                {doMetric ? `${doMetric.trendPercent}%` : "—"}
              </span>
            </div>
            <p className="text-2xl font-semibold text-on-surface mt-2">
              {doMetric ? `${formatNumber(doMetric.value, 1)}` : "—"} <span className="text-sm font-normal text-on-surface-variant">mg/L</span>
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>Critical limit: &lt; 7.0</span>
            <span className="badge-warning px-1.5 py-0.5 rounded uppercase font-bold text-[8px]">Warning</span>
          </div>
        </div>
      </div>

      {/* Main 3-Column Dashboard Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-6">
        {/* Left Side Section: Hero Chart & Leaderboard (Takes 2 Columns) */}
        <div className="lg:col-span-2 space-y-6">
          {/* SECTION 2: Biomass Growth Forecast (Hero Chart) */}
          <div className="glass-panel rounded-2xl p-6 relative">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-4">
              <div>
                <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                  Biomass Growth Forecast
                </h2>
                <p className="text-[10px] text-on-surface-variant mt-0.5">
                  Historical telemetry compared with predictive ML models and confidence intervals
                </p>
              </div>

              {/* Timeframe selector */}
              <div className="flex bg-white/5 border border-white/10 rounded-full p-1 self-start">
                {([30, 90, 180] as const).map((days) => (
                  <button
                    key={days}
                    type="button"
                    onClick={() => setForecastDays(days)}
                    className={cn(
                      "rounded-full px-3 py-1 text-[10px] font-semibold transition-all",
                      forecastDays === days
                        ? "bg-primary text-on-primary font-bold shadow-[0_0_8px_rgba(71,214,255,0.4)]"
                        : "text-on-surface-variant hover:text-on-surface"
                    )}
                  >
                    {days} Days
                  </button>
                ))}
              </div>
            </div>

            {/* Quick forecast stats row */}
            <div className="grid grid-cols-3 gap-2 border-b border-white/5 pb-4 mb-6">
              <div>
                <p className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Current Biomass</p>
                <p className="text-lg font-bold text-on-surface mt-1">1.670M kg</p>
              </div>
              <div>
                <p className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Est. Harvest Biomass</p>
                <p className="text-lg font-bold text-primary mt-1">{estimatedHarvestBiomass?.toFixed(3)}M kg</p>
              </div>
              <div>
                <p className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Growth Acceleration</p>
                <p className="text-lg font-bold text-on-surface mt-1">+12.8 kg/hr</p>
              </div>
            </div>

            {/* Recharts Container */}
            <div className="w-full h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={forecastData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="chartConfidence" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#00d2ff" stopOpacity="0.12" />
                      <stop offset="100%" stopColor="#00d2ff" stopOpacity="0.0" />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                  <XAxis
                    dataKey="label"
                    stroke="rgba(255,255,255,0.4)"
                    fontSize={10}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="rgba(255,255,255,0.4)"
                    fontSize={10}
                    tickLine={false}
                    axisLine={false}
                    domain={["auto", "auto"]}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data: any = payload[0].payload;
                        const isForecast = !data.historical;
                        return (
                          <div className="rounded-xl border border-white/10 bg-[#060e20]/95 p-3 text-xs shadow-2xl backdrop-blur-xl">
                            <p className="font-bold border-b border-white/5 pb-1 mb-1.5 text-on-surface flex justify-between gap-4">
                              <span>{isForecast ? "Forecast Node" : "Historical Node"}</span>
                              <span className="text-[10px] text-on-surface-variant">{data.label}</span>
                            </p>
                            <p className="text-on-surface-variant flex items-center justify-between gap-6">
                              <span>Biomass:</span>
                              <span className="font-bold text-on-surface">{(isForecast ? data.predicted : data.historical).toFixed(3)}M kg</span>
                            </p>
                            {isForecast && (
                              <p className="text-[10px] text-primary/80 mt-1 flex items-center justify-between gap-6">
                                <span>Conf. Limits:</span>
                                <span className="font-medium">[{data.bounds[0].toFixed(3)}M - {data.bounds[1].toFixed(3)}M]</span>
                              </p>
                            )}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  
                  {/* Projected Harvest Window Shaded Band */}
                  {harvestWindowStart && harvestWindowEnd && (
                    <ReferenceArea
                      x1={harvestWindowStart}
                      x2={harvestWindowEnd}
                      fill="#47d6ff"
                      fillOpacity={0.05}
                      label={{ value: "Projected Harvest Window", fill: "#47d6ff", fontSize: 8, position: "insideTop" }}
                    />
                  )}

                  {/* Forecast Confidence Band Area */}
                  <Area
                    dataKey="bounds"
                    stroke="none"
                    fill="url(#chartConfidence)"
                    connectNulls
                  />
                  
                  {/* Historical Solid Line */}
                  <Line
                    type="monotone"
                    dataKey="historical"
                    stroke="#47d6ff"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 5, stroke: "#47d6ff", strokeWidth: 1.5, fill: "#0b1326" }}
                  />

                  {/* Predicted Dashed Line */}
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="#47d6ff"
                    strokeWidth={1.5}
                    strokeDasharray="4 3"
                    dot={false}
                    connectNulls
                  />

                  {/* Current Position Marker Line */}
                  <ReferenceLine
                    x="Now"
                    stroke="#47d6ff"
                    strokeDasharray="3 3"
                    opacity={0.7}
                    label={{ value: "Current Position", fill: "#47d6ff", fontSize: 8, position: "insideTopLeft" }}
                  />

                  {/* Harvest Target Marker Line */}
                  <ReferenceLine
                    y={harvestTarget}
                    stroke="#edb1ff"
                    strokeDasharray="3 3"
                    opacity={0.7}
                    label={{ value: `Harvest Target (${harvestTarget.toFixed(2)}M kg)`, fill: "#edb1ff", fontSize: 8, position: "top" }}
                  />

                  {/* Growth Acceleration Marker (Reference Dot) */}
                  {accelPoint.x && (
                    <ReferenceDot
                      x={accelPoint.x}
                      y={accelPoint.y}
                      r={5}
                      fill="#0b1326"
                      stroke="#edb1ff"
                      strokeWidth={2}
                      className="cursor-help"
                      label={{ value: "Growth Accel", fill: "#edb1ff", fontSize: 8, position: "top" }}
                    />
                  )}

                  {/* Current Position Dot */}
                  <ReferenceDot
                    x="Now"
                    y={1.67}
                    r={6}
                    fill="#0b1326"
                    stroke="#47d6ff"
                    strokeWidth={2.5}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Growth Acceleration / Current Reference Dot explanation badges */}
            <div className="mt-4 flex flex-wrap gap-4 text-[9px] text-on-surface-variant border-t border-white/5 pt-3">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full border border-primary bg-background" />
                Current Status: 1.67M kg (T-0d baseline)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full border border-tertiary bg-background" />
                Growth Acceleration Point (T-8d, peak feeding temp: 11.2°C)
              </span>
            </div>
          </div>

          {/* SECTION 6: Zone Performance Leaderboard */}
          <div className="glass-panel rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                  Zone Performance Leaderboard
                </h2>
                <p className="text-[10px] text-on-surface-variant mt-0.5">
                  Production optimization rankings and biosecurity index metrics across active leases
                </p>
              </div>
              <span className="text-[10px] text-on-surface-variant font-medium">Sorted by health index</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-on-surface">
                <thead className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant border-b border-white/5">
                  <tr>
                    <th className="py-2.5 pb-2">Lease Zone</th>
                    <th className="py-2.5 pb-2 text-center">Health Index</th>
                    <th className="py-2.5 pb-2 text-right">Biomass Capacity</th>
                    <th className="py-2.5 pb-2 text-right">Growth Rate</th>
                    <th className="py-2.5 pb-2 text-center">Telemetry Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {zoneLeaderboard.map((zone) => (
                    <tr key={zone.id} className="hover:bg-white/5 transition-colors">
                      <td className="py-3 flex items-center gap-2">
                        <span className="font-semibold">{zone.name}</span>
                        {zone.isTop && (
                          <span className="text-[8px] badge-optimal px-1.5 py-0.5 rounded font-bold uppercase tracking-widest select-none shadow-[0_0_6px_rgba(71,214,255,0.2)]">
                            Top Performer
                          </span>
                        )}
                      </td>
                      <td className="py-3 text-center font-bold">
                        <span
                          className={cn(
                            zone.healthScore >= 80
                              ? "text-primary"
                              : zone.healthScore >= 60
                              ? "text-warning"
                              : "text-error"
                          )}
                        >
                          {zone.healthScore}/100
                        </span>
                      </td>
                      <td className="py-3 text-right font-medium text-on-surface-variant">
                        {zone.biomassTons} Tons
                      </td>
                      <td className="py-3 text-right font-medium text-primary flex items-center justify-end gap-1">
                        <span className="text-on-surface-variant">{zone.growthRate}</span>
                        {zone.trend === "up" && (
                          <svg className="h-3 w-3 text-primary shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
                          </svg>
                        )}
                        {zone.trend === "down" && (
                          <svg className="h-3 w-3 text-error shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
                          </svg>
                        )}
                      </td>
                      <td className="py-3 text-center">
                        <span
                          className={cn(
                            "rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                            zone.riskStatus === "optimal"
                              ? "badge-optimal"
                              : zone.riskStatus === "warning"
                              ? "badge-warning"
                              : "badge-critical"
                          )}
                        >
                          {zone.riskStatus === "optimal" ? "Optimal" : zone.riskStatus === "warning" ? "Warning" : "Critical"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column Panels (Takes 1 Column) */}
        <div className="space-y-6">
          {/* SECTION 3: Harvest Prediction Engine */}
          <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between min-h-[340px]">
            <div>
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant flex items-center gap-1.5">
                  <svg className="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0h.5m-.5 0h-10.5m10.5 0H1.5" />
                  </svg>
                  Harvest Prediction Engine
                </h2>
                <span className="badge-optimal text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full select-none shadow-[0_0_6px_rgba(71,214,255,0.2)]">
                  92% Conf.
                </span>
              </div>

              <dl className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <dt className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Estimated Yield</dt>
                  <dd className="mt-1 text-sm font-semibold text-on-surface">1,945,800 kg</dd>
                </div>
                <div>
                  <dt className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Days Until Harvest</dt>
                  <dd className="mt-1 text-sm font-semibold text-primary">42 Days</dd>
                </div>
                <div>
                  <dt className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Optimal Window</dt>
                  <dd className="mt-1 text-xs font-semibold text-on-surface">Aug 05 - Aug 12</dd>
                </div>
                <div>
                  <dt className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Market Readiness</dt>
                  <dd className="mt-1 text-xs font-semibold text-on-surface">86 / 100</dd>
                </div>
                <div className="col-span-2">
                  <dt className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Expected Revenue Index</dt>
                  <dd className="mt-1 text-base font-bold text-primary">$14,593,500 <span className="text-[10px] font-normal text-on-surface-variant">($7.50/kg avg)</span></dd>
                </div>
              </dl>
            </div>

            <div className="border-t border-white/5 pt-3 mt-2">
              <h4 className="text-[9px] font-bold uppercase tracking-widest text-primary mb-1.5">AI Engine Insight</h4>
              <p className="text-[11px] leading-relaxed text-on-surface-variant bg-[#0b1326]/50 border border-white/5 rounded-xl p-3">
                "The target window optimizes biomass tonnage against thermal oxygen capacity boundaries. Early harvest in mid-August circumvents seasonal mortality risks associated with ocean warming trends."
              </p>
            </div>
          </div>

          {/* SECTION 4: Feed Conversion Intelligence */}
          <div className="glass-panel-glow rounded-2xl p-6 flex flex-col justify-between min-h-[340px]">
            <div>
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant flex items-center gap-1.5">
                  <svg className="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18M3 12h18" />
                  </svg>
                  Feed Conversion (FCR)
                </h2>
                <span className="text-[10px] font-bold text-primary">Score: 94/100</span>
              </div>

              <div className="grid grid-cols-3 gap-2 mb-4 text-center">
                <div className="bg-[#0b1326]/40 border border-white/5 rounded-xl p-2">
                  <p className="text-[8px] font-bold uppercase tracking-wider text-on-surface-variant">Current FCR</p>
                  <p className="text-base font-bold text-on-surface mt-1">1.12</p>
                </div>
                <div className="bg-[#0b1326]/40 border border-white/5 rounded-xl p-2">
                  <p className="text-[8px] font-bold uppercase tracking-wider text-on-surface-variant">Historical</p>
                  <p className="text-base font-bold text-on-surface-variant mt-1">1.16</p>
                </div>
                <div className="bg-[#0b1326]/40 border border-white/5 rounded-xl p-2">
                  <p className="text-[8px] font-bold uppercase tracking-wider text-on-surface-variant">Target FCR</p>
                  <p className="text-base font-bold text-primary mt-1">1.08</p>
                </div>
              </div>

              <div className="mb-4 flex items-center justify-between bg-white/5 rounded-xl p-2 border border-white/5">
                <span className="text-[10px] font-semibold text-on-surface-variant uppercase">Feed Waste Reduction</span>
                <span className="text-xs font-bold text-primary">14.2% Saved</span>
              </div>
            </div>

            <div className="border-t border-white/5 pt-3">
              <h4 className="text-[9px] font-bold uppercase tracking-widest text-primary mb-2">AI Feeding recommendation</h4>
              <div className="space-y-1.5">
                {[
                  "Reduce feed ratio by 4% during peak warm hours (14:00 - 17:00)",
                  "Shift 15% feed allocation to early morning cycles (06:00 - 08:00)",
                  "Adjust sensor threshold to prevent bottom-waste drops",
                ].map((rec, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-[10px] leading-relaxed text-on-surface-variant">
                    <span className="text-primary mt-1">▪</span>
                    <span>{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SECTION 5: Mortality Forecast Engine */}
          <div className="glass-panel rounded-2xl p-6 min-h-[220px] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant flex items-center gap-1.5">
                  <svg className="h-4 w-4 text-warning" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                  </svg>
                  Mortality Forecast Engine
                </h2>
                <span className="badge-warning text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full">
                  Moderate Risk
                </span>
              </div>

              <div className="space-y-3">
                {[
                  { range: "7-Day Forecast", val: "0.08%", conf: 96 },
                  { range: "14-Day Forecast", val: "0.22%", conf: 91 },
                  { range: "30-Day Forecast", val: "0.45%", conf: 84 },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <span className="text-on-surface-variant font-medium">{item.range}</span>
                    <div className="flex items-center gap-4">
                      <span className="font-semibold text-on-surface">{item.val}</span>
                      <span className="text-[10px] text-on-surface-variant font-medium">({item.conf}% conf.)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="mt-4 border-t border-white/5 pt-2 text-center">
              <span className="text-[9px] text-on-surface-variant">
                Stochastic projection generated across 1.67M active biomass cohort counts
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid for Models & Insights Section (Sections 7, 8, 9) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-6">
        {/* SECTION 7: Active ML Models Grid (Takes 2 Columns) */}
        <div className="glass-panel rounded-2xl p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                Active ML Models
              </h2>
              <p className="text-[10px] text-on-surface-variant mt-0.5">
                Real-time operational validation and accuracy scores for biological predictors
              </p>
            </div>
            <span className="text-[10px] text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-full uppercase tracking-wider font-bold">
              All models online
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
            {activeModels.map((model, i) => (
              <div key={i} className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xs font-semibold text-on-surface line-clamp-1">{model.name}</h3>
                    <span className="inline-block h-2 w-2 rounded-full bg-primary shadow-[0_0_8px_rgba(71,214,255,0.6)]" />
                  </div>
                  
                  <div className="space-y-1 mt-3">
                    <div className="flex justify-between text-[10px]">
                      <span className="text-on-surface-variant">Accuracy:</span>
                      <span className="font-semibold text-on-surface">{model.accuracy}%</span>
                    </div>
                    <div className="flex justify-between text-[10px]">
                      <span className="text-on-surface-variant">Confidence:</span>
                      <span className="font-semibold text-on-surface">{model.confidence}%</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 border-t border-white/5 pt-2 flex justify-between text-[9px] text-on-surface-variant">
                  <span>Retrained: {model.lastRetrained}</span>
                  <span className="font-semibold text-primary">{model.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION 9: Prediction Confidence Panel (Takes 1 Column) */}
        <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                Prediction Confidence Panel
              </h2>
              <span className="badge-optimal text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full">
                95% Index
              </span>
            </div>

            <div className="space-y-4">
              {[
                { label: "Forecast Reliability", val: "94.2%", level: "High" },
                { label: "Model Agreement Score", val: "96.8%", level: "Optimal" },
                { label: "Data Quality Score", val: "98.1%", level: "Optimal" },
                { label: "Sensor Coverage Index", val: "100.0%", level: "Optimal" },
              ].map((stat, i) => (
                <div key={i} className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-on-surface-variant font-medium">{stat.label}</span>
                    <span className="font-bold text-on-surface">{stat.val}</span>
                  </div>
                  <div className="relative h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
                    <div
                      className="absolute left-0 top-0 h-full rounded-full bg-primary"
                      style={{ width: stat.val }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 border-t border-white/5 pt-3 text-center text-[10px] text-on-surface-variant">
            Stochastic model uncertainty boundaries: &plusmn;0.08 PSI score
          </div>
        </div>
      </div>

      {/* SECTION 8: AI Insights Center */}
      <div className="glass-panel rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-2 mb-4 border-b border-white/5 pb-2">
          <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
          </svg>
          <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
            AI Insights Center
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {aiInsights.map((insight) => (
            <div
              key={insight.id}
              className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-4 flex flex-col justify-between transition-all hover:border-primary/20"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider">{insight.zone}</span>
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-[8px] font-bold uppercase tracking-widest",
                      insight.priority === "critical"
                        ? "bg-error/10 text-error border border-error/20"
                        : insight.priority === "high"
                        ? "bg-warning/10 text-warning border border-warning/20"
                        : "bg-primary/10 text-primary border border-primary/20"
                    )}
                  >
                    {insight.priority}
                  </span>
                </div>
                <p className="text-xs text-on-surface leading-relaxed">{insight.message}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[10px] text-on-surface-variant">
                <span>Confidence: <strong className="text-on-surface">{insight.confidence}%</strong></span>
                <span className="font-semibold text-primary">{insight.impact}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
