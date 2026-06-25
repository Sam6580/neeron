"use client";

import Link from "next/link";
import { useAppData } from "@/lib/hooks/useAppData";
import type { Tank } from "@/types";
import { notFound } from "next/navigation";
import { use, useState } from "react";
import { AppShell } from "@/components/layout";
import {
  computePsiScore,
  formatCompact,
  formatNumber,
  formatRelativeTime,
  getTankBiomassKg,
  getTankDisplayId,
  getTankHealthStatusLabel,
  getTankHealthStatusStyle,
  getTankRiskLabel,
  getTankRiskLevel,
  getPsiStatusStyle,
} from "@/lib";
import { cn } from "@/lib/utils";

interface TankDetailPageProps {
  params: Promise<{ id: string }>;
}

// Interfaces for structured AI mock telemetry
interface AIPrediction {
  label: string;
  score: number;
  level: "Low" | "Moderate" | "High" | "Critical";
  statusStyle: string;
}

interface AIRecommendation {
  title: string;
  priority: "low" | "medium" | "high" | "critical";
  confidence: number;
  expectedOutcome: string;
}

interface AICaseMatch {
  scenarioId: string;
  similarity: number;
  summary: string;
  resolution: string;
}

interface PSITrendPoint {
  time: string;
  psi: number;
  isForecast?: boolean;
}

interface AIDetails {
  predictions: AIPrediction[];
  recommendations: AIRecommendation[];
  explainableAI: string;
  psiTrend: PSITrendPoint[];
  caseMatch: AICaseMatch;
}

// Helper to generate dynamic, state-appropriate AI details for each tank
function getTankAiDetails(tank: Tank): AIDetails {
  const health = tank.healthScore;
  const psi = computePsiScore(tank);

  if (tank.status === "offline" || tank.status === "maintenance" || tank.fishCount === 0) {
    return {
      predictions: [
        { label: "Stress Risk", score: 0, level: "Low", statusStyle: "text-on-surface-variant bg-white/5 border border-white/10" },
        { label: "Disease Risk", score: 0, level: "Low", statusStyle: "text-on-surface-variant bg-white/5 border border-white/10" },
        { label: "Mortality Risk", score: 0, level: "Low", statusStyle: "text-on-surface-variant bg-white/5 border border-white/10" },
      ],
      recommendations: [
        {
          title: "System Maintenance Baseline",
          priority: "low",
          confidence: 99,
          expectedOutcome: "Nominal maintenance or offline validation state. No intervention required.",
        },
      ],
      explainableAI: "The production unit is currently offline or undergoing maintenance. Biomass population is zero. Environmental sensors are active for background baseline calibrations only.",
      caseMatch: {
        scenarioId: "SCN-000",
        similarity: 100,
        summary: "Standard offline/maintenance baseline calibration.",
        resolution: "Nominal status verified. Sensor validation checks complete.",
      },
      psiTrend: [
        { time: "-24h", psi: 0 },
        { time: "-20h", psi: 0 },
        { time: "-16h", psi: 0 },
        { time: "-12h", psi: 0 },
        { time: "-8h", psi: 0 },
        { time: "-4h", psi: 0 },
        { time: "Now", psi: 0 },
        { time: "+6h", psi: 0, isForecast: true },
        { time: "+12h", psi: 0, isForecast: true },
        { time: "+24h", psi: 0, isForecast: true },
      ],
    };
  }

  // Critical State
  if (health < 60) {
    return {
      predictions: [
        { label: "Stress Risk", score: 94, level: "Critical", statusStyle: "badge-critical" },
        { label: "Disease Risk (AGD)", score: 81, level: "High", statusStyle: "badge-critical" },
        { label: "Mortality Risk", score: 28, level: "High", statusStyle: "badge-critical" },
      ],
      recommendations: [
        {
          title: "Increase Aeration Flow rate",
          priority: "critical",
          confidence: 95,
          expectedOutcome: "Elevate dissolved oxygen levels to target safety zone (> 7.5 mg/L) within 2 hours.",
        },
        {
          title: "Water Exchange & Bio-filtration Flush",
          priority: "critical",
          confidence: 91,
          expectedOutcome: "Dilute critical ammonia levels (0.041 mg/L) and reduce water turbidity.",
        },
        {
          title: "Reduce Feed Ratio by 20%",
          priority: "high",
          confidence: 89,
          expectedOutcome: "Lower metabolic oxygen requirements and minimize digestive organic loading.",
        },
      ],
      explainableAI: `Critically depressed Dissolved Oxygen (${tank.lastReading.dissolvedOxygenMgL} mg/L) driven by elevated sea temperature (${tank.lastReading.temperatureC}°C) has triggered biological stress alarms. High stocking density (${tank.stockingDensityKgM3} kg/m³) combines with elevated ammonia (${tank.lastReading.ammoniaMgL} mg/L) to accelerate metabolic exhaustion. Turbidity at ${tank.lastReading.turbidityNtu} NTU indicates high suspended solids, multiplying gill disease risk.`,
      caseMatch: {
        scenarioId: "SCN-912",
        similarity: 94,
        summary: "Warm-water low DO dip event in Chiloé Cage 05, Q3 2024.",
        resolution: "Immediate oxygenation boost, 24h feed suspension, and active water exchange recovered health score from 50 to 88 with zero cohort mortality.",
      },
      psiTrend: [
        { time: "-24h", psi: 2.2 },
        { time: "-20h", psi: 2.4 },
        { time: "-16h", psi: 2.5 },
        { time: "-12h", psi: 2.9 },
        { time: "-8h", psi: 3.2 },
        { time: "-4h", psi: 3.8 },
        { time: "Now", psi: psi },
        { time: "+6h", psi: Math.min(5, psi + 0.4), isForecast: true },
        { time: "+12h", psi: Math.max(1, psi - 0.5), isForecast: true },
        { time: "+24h", psi: Math.max(1, psi - 1.6), isForecast: true },
      ],
    };
  }

  // Warning State
  if (health < 75) {
    return {
      predictions: [
        { label: "Stress Risk", score: 72, level: "High", statusStyle: "badge-warning" },
        { label: "Disease Risk (Sea Lice)", score: 64, level: "Moderate", statusStyle: "badge-warning" },
        { label: "Mortality Risk", score: 12, level: "Moderate", statusStyle: "badge-warning" },
      ],
      recommendations: [
        {
          title: "Auxiliary Aeration Support",
          priority: "high",
          confidence: 88,
          expectedOutcome: "Stabilize Dissolved Oxygen level above optimal threshold (> 8.0 mg/L).",
        },
        {
          title: "Reduce Feed Ratio by 10%",
          priority: "medium",
          confidence: 82,
          expectedOutcome: "Reduce digestive oxygen drag during peak afternoon temperatures.",
        },
      ],
      explainableAI: `Dissolved Oxygen level is depressed at ${tank.lastReading.dissolvedOxygenMgL} mg/L, approaching stress boundaries. Temperature remains elevated at ${tank.lastReading.temperatureC}°C, increasing fish metabolic rates and oxygen demands. Ammonia is high at ${tank.lastReading.ammoniaMgL} mg/L, causing moderate systemic stress.`,
      caseMatch: {
        scenarioId: "SCN-284",
        similarity: 89,
        summary: "Summer thermal drift and low flow in Loch Duich Cage 07, Q2 2025.",
        resolution: "Activating auxiliary oxygen micro-bubblers and decreasing feed rates by 10% for 48 hours returned parameters to baseline.",
      },
      psiTrend: [
        { time: "-24h", psi: 1.8 },
        { time: "-20h", psi: 1.9 },
        { time: "-16h", psi: 2.1 },
        { time: "-12h", psi: 2.3 },
        { time: "-8h", psi: 2.4 },
        { time: "-4h", psi: 2.6 },
        { time: "Now", psi: psi },
        { time: "+6h", psi: Math.min(5, psi + 0.3), isForecast: true },
        { time: "+12h", psi: Math.max(1, psi - 0.2), isForecast: true },
        { time: "+24h", psi: Math.max(1, psi - 0.8), isForecast: true },
      ],
    };
  }

  // Healthy/Optimal State
  return {
    predictions: [
      { label: "Stress Risk", score: 24, level: "Low", statusStyle: "badge-optimal" },
      { label: "Disease Risk (IPN)", score: 18, level: "Low", statusStyle: "badge-optimal" },
      { label: "Mortality Risk", score: 3, level: "Low", statusStyle: "badge-optimal" },
    ],
    recommendations: [
      {
        title: "Maintain Standard Protocol",
        priority: "low",
        confidence: 95,
        expectedOutcome: "Sustain steady biomass expansion and high FCR performance.",
      },
      {
        title: "Preventive Weekly Sea Lice Audit",
        priority: "low",
        confidence: 85,
        expectedOutcome: "Validate biosecurity compliance indexes.",
      },
    ],
    explainableAI: `All environmental telemetry indicators are in optimal ranges. Temperature (${tank.lastReading.temperatureC}°C) and Dissolved Oxygen (${tank.lastReading.dissolvedOxygenMgL} mg/L) show steady equilibrium. Ammonia (${tank.lastReading.ammoniaMgL} mg/L) remains well below stress limits.`,
    caseMatch: {
      scenarioId: "SCN-102",
      similarity: 98,
      summary: "Baseline spring smolt cohort monitoring in Loch Duich, 2024.",
      resolution: "Nominal operational telemetry. Standard feeding program and weekly audits maintained healthy growth.",
    },
    psiTrend: [
      { time: "-24h", psi: 1.3 },
      { time: "-20h", psi: 1.2 },
      { time: "-16h", psi: 1.2 },
      { time: "-12h", psi: 1.1 },
      { time: "-8h", psi: 1.1 },
      { time: "-4h", psi: 1.2 },
      { time: "Now", psi: psi },
      { time: "+6h", psi: psi, isForecast: true },
      { time: "+12h", psi: Math.max(1, psi - 0.1), isForecast: true },
      { time: "+24h", psi: Math.max(1, psi - 0.2), isForecast: true },
    ],
  };
}

export default function TankDetailPage({ params }: TankDetailPageProps) {
  const { getActiveAlerts, getTankById, getZoneById } = useAppData();
  const { id } = use(params);
  const tank = getTankById(id);

  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null);

  if (!tank) {
    notFound();
  }

  const zone = getZoneById(tank.zoneId);
  const activeAlerts = getActiveAlerts();
  const displayId = getTankDisplayId(tank);
  const biomass = getTankBiomassKg(tank);
  const psiScore = computePsiScore(tank);
  const riskLevel = getTankRiskLevel(tank);
  const { lastReading } = tank;

  const aiDetails = getTankAiDetails(tank);

  // Proportional X positioning variables for the SVG chart
  const hoursMap: Record<string, number> = {
    "-24h": -24,
    "-20h": -20,
    "-16h": -16,
    "-12h": -12,
    "-8h": -8,
    "-4h": -4,
    "Now": 0,
    "+6h": 6,
    "+12h": 12,
    "+24h": 24,
  };

  const getX = (time: string) => {
    const hr = hoursMap[time] ?? 0;
    return 45 + ((hr + 24) / 48) * 425; // 45px left offset, 425px chart area width (total 500px)
  };

  const getY = (psi: number) => {
    return 155 - (psi / 5) * 125; // 155px baseline height, 125px chart height range (0 to 5)
  };

  // Build the forecast shaded confidence polygon (for +6h, +12h, +24h forecasts)
  const nowPt = aiDetails.psiTrend.find(pt => pt.time === "Now");
  const p6 = aiDetails.psiTrend.find(pt => pt.time === "+6h");
  const p12 = aiDetails.psiTrend.find(pt => pt.time === "+12h");
  const p24 = aiDetails.psiTrend.find(pt => pt.time === "+24h");

  let forecastPolygonPoints = "";
  if (nowPt && p6 && p12 && p24) {
    const nowX = getX("Now");
    const x6 = getX("+6h");
    const x12 = getX("+12h");
    const x24 = getX("+24h");

    // Upper bounds
    const uNow = getY(nowPt.psi);
    const u6 = getY(p6.psi + 0.3);
    const u12 = getY(p12.psi + 0.5);
    const u24 = getY(p24.psi + 0.8);

    // Lower bounds
    const l24 = getY(Math.max(0, p24.psi - 0.8));
    const l12 = getY(Math.max(0, p12.psi - 0.5));
    const l6 = getY(Math.max(0, p6.psi - 0.3));
    const lNow = getY(nowPt.psi);

    forecastPolygonPoints = `${nowX},${uNow} ${x6},${u6} ${x12},${u12} ${x24},${u24} ${x24},${l24} ${x12},${l12} ${x6},${l6} ${nowX},${lNow}`;
  }

  return (
    <AppShell activePath="/tanks" title="Tank Management" alertCount={activeAlerts.length}>
      <div className="mb-6">
        <Link
          href="/tanks"
          className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:text-primary-bright"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
          Back to Tank Management
        </Link>
        <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-on-surface">{displayId}</h1>
            <p className="mt-1 text-sm text-on-surface-variant">{tank.name}</p>
            <p className="mt-0.5 text-xs text-on-surface-variant">
              {zone?.code} · {zone?.name} · {tank.species}
            </p>
          </div>
          <span
            className={cn(
              "rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-widest",
              getTankHealthStatusStyle(tank.status),
            )}
          >
            {getTankHealthStatusLabel(tank.status)}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Production Metrics */}
        <div className="glass-panel-glow rounded-2xl p-6 lg:col-span-2">
          <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
            Production Metrics
          </h2>
          <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Population
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {tank.fishCount > 0 ? formatCompact(tank.fishCount) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Biomass
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {biomass > 0 ? `${formatCompact(biomass)} kg` : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Avg Weight
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {tank.avgWeightKg > 0 ? `${formatNumber(tank.avgWeightKg, 2)} kg` : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                FCR
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {tank.fcr > 0 ? formatNumber(tank.fcr, 2) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Mortality Rate
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {formatNumber(tank.mortalityRatePercent, 2)}%
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Days in Production
              </dt>
              <dd className="mt-1 text-lg font-semibold text-on-surface">
                {tank.daysInProduction > 0 ? tank.daysInProduction : "—"}
              </dd>
            </div>
          </dl>
        </div>

        {/* Risk Assessment */}
        <div className="glass-panel rounded-2xl p-6">
          <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
            Risk Assessment
          </h2>
          <dl className="mt-4 space-y-4">
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Health Score
              </dt>
              <dd className="mt-1 text-3xl font-bold text-on-surface">
                {tank.healthScore > 0 ? tank.healthScore : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                PSI Score
              </dt>
              <dd className={cn("mt-1 text-2xl font-semibold", getPsiStatusStyle(psiScore))}>
                {psiScore > 0 ? formatNumber(psiScore, 1) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Risk Classification
              </dt>
              <dd className="mt-1 text-sm font-medium text-on-surface">
                {getTankRiskLabel(riskLevel)}
              </dd>
            </div>
          </dl>
        </div>

        {/* Water Quality */}
        <div className="glass-panel rounded-2xl p-6 lg:col-span-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
              Water Quality — Last Sensor Reading
            </h2>
            <span className="text-xs text-on-surface-variant">
              {formatRelativeTime(lastReading.timestamp)}
            </span>
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Temperature
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.temperatureC, 1)}°C
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                pH
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.ph, 1)}
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Dissolved Oxygen
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.dissolvedOxygenMgL, 1)} mg/L
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Salinity
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.salinityPpt, 1)} ppt
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Ammonia
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.ammoniaMgL, 3)} mg/L
              </dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                Turbidity
              </dt>
              <dd className="mt-1 text-base font-semibold text-on-surface">
                {formatNumber(lastReading.turbidityNtu, 1)} NTU
              </dd>
            </div>
          </dl>
        </div>

        {/* AI Predictive Intelligence Section Header */}
        <div className="lg:col-span-3 mt-4">
          <div className="flex items-center gap-2 border-b border-white/5 pb-2">
            <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
            </svg>
            <h2 className="text-sm font-semibold uppercase tracking-widest text-on-surface">
              AI Precision Aquaculture Intelligence
            </h2>
          </div>
        </div>

        {/* 1. AI Prediction Engine */}
        <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-6">
              AI Predictions & Diagnostics
            </h3>
            <div className="space-y-6">
              {aiDetails.predictions.map((pred, i) => (
                <div key={i} className="flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-on-surface-variant">{pred.label}</span>
                    <span className={cn("rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider", pred.statusStyle)}>
                      {pred.level}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="relative h-2 flex-1 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className={cn(
                          "absolute left-0 top-0 h-full rounded-full transition-all duration-500",
                          pred.level === "Critical" || pred.level === "High"
                            ? "bg-error"
                            : pred.level === "Moderate"
                            ? "bg-warning"
                            : "bg-primary"
                        )}
                        style={{ width: `${pred.score}%` }}
                      />
                    </div>
                    <span className="text-sm font-bold text-on-surface min-w-[36px] text-right">
                      {pred.score}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="mt-8 border-t border-white/5 pt-4 text-center">
            <span className="text-[10px] text-on-surface-variant font-medium">
              Diagnostics refreshed: {formatRelativeTime(lastReading.timestamp)}
            </span>
          </div>
        </div>

        {/* 2. Recommendation Engine & 3. Explainable AI (XAI) Panel */}
        <div className="glass-panel-glow rounded-2xl p-6 lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                AI Recommendation Actions
              </h3>
              <span className="text-[10px] font-bold badge-optimal uppercase tracking-widest px-2.5 py-0.5 rounded-full">
                AI Agent Active
              </span>
            </div>

            <div className="space-y-3">
              {aiDetails.recommendations.map((rec, i) => (
                <div
                  key={i}
                  className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-4 transition-all hover:border-primary/20"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h4 className="text-sm font-semibold text-on-surface">{rec.title}</h4>
                      <p className="mt-1.5 text-xs text-on-surface-variant flex items-center gap-1">
                        <span className="font-semibold text-primary">Expected Outcome:</span>
                        <span>{rec.expectedOutcome}</span>
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <span
                        className={cn(
                          "inline-block rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest mb-1",
                          rec.priority === "critical"
                            ? "bg-error/10 text-error border border-error/20"
                            : rec.priority === "high"
                            ? "bg-warning/10 text-warning border border-warning/20"
                            : "bg-primary/10 text-primary border border-primary/20"
                        )}
                      >
                        {rec.priority}
                      </span>
                      <p className="text-[10px] text-on-surface-variant font-medium">
                        {rec.confidence}% confidence
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Explainable AI (XAI) Panel */}
          <div className="mt-6 border-t border-white/5 pt-4">
            <h4 className="text-[10px] font-bold uppercase tracking-widest text-primary mb-2 flex items-center gap-1.5">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 1 1 .517 1.403l-.041.02a.75.75 0 0 1-.517-1.403Zm0 6.844.041-.02a.75.75 0 1 1 .517 1.403l-.041.02a.75.75 0 0 1-.517-1.403Zm0-13.688.041-.02a.75.75 0 1 1 .517 1.403l-.041.02a.75.75 0 0 1-.517-1.403ZM12 2.25a9.75 9.75 0 1 0 9.75 9.75A9.75 9.75 0 0 0 12 2.25Z" />
              </svg>
              Explainable AI (Reasoning Model)
            </h4>
            <p className="text-xs leading-relaxed text-on-surface-variant bg-[#0b1326]/60 border border-white/5 rounded-xl p-3.5">
              {aiDetails.explainableAI}
            </p>
          </div>
        </div>

        {/* 4. PSI Trend Chart with Forecast */}
        <div className="glass-panel rounded-2xl p-6 lg:col-span-2 relative">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                PSI Trend & Forecast
              </h3>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Composite Population Stress Index · 24h History & 24h Prediction Model
              </p>
            </div>
            <div className="flex items-center gap-4 text-[10px]">
              <span className="flex items-center gap-1.5 font-medium text-on-surface-variant">
                <span className="inline-block h-1.5 w-4 rounded-full bg-primary" />
                Historical
              </span>
              <span className="flex items-center gap-1.5 font-medium text-on-surface-variant">
                <span className="inline-block h-1.5 w-4 border-t-2 border-dashed border-primary" />
                Forecast (Confidence Band)
              </span>
            </div>
          </div>

          <div className="relative select-none">
            {/* SVG PSI Line Chart */}
            <svg viewBox="0 0 500 180" className="w-full h-auto">
              <defs>
                <linearGradient id="forecastGlow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#47d6ff" stopOpacity="0.18" />
                  <stop offset="100%" stopColor="#47d6ff" stopOpacity="0.0" />
                </linearGradient>
                <filter id="glowEffect" x="-10%" y="-10%" width="120%" height="120%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Horizontal Gridlines */}
              {[0, 1, 2, 3, 4, 5].map((gridVal) => (
                <g key={gridVal} opacity={gridVal === 0 ? 0.3 : 0.08}>
                  <line
                    x1={45}
                    y1={getY(gridVal)}
                    x2={480}
                    y2={getY(gridVal)}
                    stroke="#ffffff"
                    strokeWidth={1}
                  />
                  <text
                    x={35}
                    y={getY(gridVal) + 3.5}
                    fill="#dae2fd"
                    fontSize={9}
                    textAnchor="end"
                    fontWeight="500"
                    opacity={0.7}
                  >
                    {gridVal.toFixed(1)}
                  </text>
                </g>
              ))}

              {/* Vertical Gridlines & Labels */}
              {aiDetails.psiTrend.map((pt, i) => {
                const x = getX(pt.time);
                const showGrid = pt.time === "-24h" || pt.time === "-12h" || pt.time === "Now" || pt.time === "+12h" || pt.time === "+24h";
                return (
                  <g key={i}>
                    {showGrid && (
                      <line
                        x1={x}
                        y1={20}
                        x2={x}
                        y2={155}
                        stroke="#ffffff"
                        strokeWidth={1}
                        strokeDasharray={pt.isForecast ? "2 2" : undefined}
                        opacity={pt.time === "Now" ? 0.25 : 0.05}
                      />
                    )}
                    {showGrid && (
                      <text
                        x={x}
                        y={170}
                        fill="#dae2fd"
                        fontSize={9}
                        textAnchor="middle"
                        fontWeight="500"
                        opacity={pt.isForecast ? 0.5 : 0.7}
                      >
                        {pt.time}
                      </text>
                    )}
                  </g>
                );
              })}

              {/* Shaded Forecast Confidence Bounds */}
              {forecastPolygonPoints && (
                <polygon
                  points={forecastPolygonPoints}
                  fill="url(#forecastGlow)"
                  stroke="none"
                />
              )}

              {/* Historical Trend Line (Solid) */}
              <path
                d={aiDetails.psiTrend
                  .filter((pt) => !pt.isForecast)
                  .map((pt, i) => `${i === 0 ? "M" : "L"} ${getX(pt.time)} ${getY(pt.psi)}`)
                  .join(" ")}
                fill="none"
                stroke="#47d6ff"
                strokeWidth={2.5}
                strokeLinecap="round"
                strokeLinejoin="round"
                filter="url(#glowEffect)"
              />

              {/* Forecast Trend Line (Dashed) */}
              <path
                d={aiDetails.psiTrend
                  .filter((pt) => pt.time === "Now" || pt.isForecast)
                  .map((pt, i) => `${i === 0 ? "M" : "L"} ${getX(pt.time)} ${getY(pt.psi)}`)
                  .join(" ")}
                fill="none"
                stroke="#47d6ff"
                strokeWidth={2.0}
                strokeDasharray="4 3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Data points markers */}
              {aiDetails.psiTrend.map((pt, i) => {
                const x = getX(pt.time);
                const y = getY(pt.psi);
                const isHovered = hoveredPoint === i;

                return (
                  <g key={i}>
                    {/* Ring for interactive focus */}
                    {isHovered && (
                      <circle
                        cx={x}
                        cy={y}
                        r={8}
                        fill="#47d6ff"
                        fillOpacity={0.2}
                        className="animate-ping"
                      />
                    )}
                    <circle
                      cx={x}
                      cy={y}
                      r={pt.time === "Now" ? 5 : isHovered ? 4.5 : 3}
                      fill={pt.time === "Now" ? "#0b1326" : "#47d6ff"}
                      stroke="#47d6ff"
                      strokeWidth={pt.time === "Now" ? 2.5 : 1}
                    />
                  </g>
                );
              })}

              {/* Hover Indicator Vertical Line */}
              {hoveredPoint !== null && (
                <line
                  x1={getX(aiDetails.psiTrend[hoveredPoint].time)}
                  y1={20}
                  x2={getX(aiDetails.psiTrend[hoveredPoint].time)}
                  y2={155}
                  stroke="#47d6ff"
                  strokeWidth={1}
                  strokeDasharray="2 2"
                  opacity={0.6}
                />
              )}

              {/* Interactive Hover Area overlay */}
              {aiDetails.psiTrend.map((pt, i) => {
                const x = getX(pt.time);
                const left = i === 0 ? 45 : (getX(aiDetails.psiTrend[i - 1].time) + x) / 2;
                const right = i === aiDetails.psiTrend.length - 1 ? 480 : (getX(aiDetails.psiTrend[i + 1].time) + x) / 2;
                const width = right - left;

                return (
                  <rect
                    key={i}
                    x={left}
                    y={10}
                    width={width}
                    height={150}
                    fill="transparent"
                    className="cursor-crosshair"
                    onMouseEnter={() => setHoveredPoint(i)}
                    onMouseLeave={() => setHoveredPoint(null)}
                  />
                );
              })}
            </svg>

            {/* Custom Tooltip */}
            {hoveredPoint !== null && (
              <div
                className="absolute pointer-events-none rounded-xl border border-white/10 bg-[#060e20]/95 p-3 text-xs shadow-2xl backdrop-blur-xl transition-all duration-100"
                style={{
                  left: `${(getX(aiDetails.psiTrend[hoveredPoint].time) / 500) * 100}%`,
                  top: `${(getY(aiDetails.psiTrend[hoveredPoint].psi) / 180) * 100 - 32}%`,
                  transform: "translate(-50%, -100%)",
                }}
              >
                <div className="flex flex-col gap-1 min-w-[100px]">
                  <div className="flex items-center justify-between border-b border-white/5 pb-1 mb-1">
                    <span className="font-semibold text-on-surface">
                      {aiDetails.psiTrend[hoveredPoint].time === "Now" ? "Current State" : aiDetails.psiTrend[hoveredPoint].isForecast ? "Prediction" : "Telemetry Log"}
                    </span>
                    <span className="text-[10px] text-on-surface-variant font-medium ml-3">
                      {aiDetails.psiTrend[hoveredPoint].time}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-on-surface-variant">PSI Score:</span>
                    <span className={cn("font-bold", getPsiStatusStyle(aiDetails.psiTrend[hoveredPoint].psi))}>
                      {aiDetails.psiTrend[hoveredPoint].psi.toFixed(1)}
                    </span>
                  </div>
                  {aiDetails.psiTrend[hoveredPoint].isForecast && (
                    <div className="flex items-center justify-between text-[10px] text-on-surface-variant mt-0.5">
                      <span>Conf. Interval:</span>
                      <span className="font-medium text-primary">
                        ±{hoveredPoint === 7 ? "0.3" : hoveredPoint === 8 ? "0.5" : "0.8"} PSI
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 5. Historical Case Match */}
        <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                Historical Case Match
              </h3>
              <span className="text-[10px] font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-full">
                {aiDetails.caseMatch.similarity}% Match
              </span>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                  Scenario ID
                </p>
                <p className="mt-1 text-sm font-semibold text-primary hover:text-primary-bright cursor-pointer underline decoration-dotted">
                  {aiDetails.caseMatch.scenarioId}
                </p>
              </div>

              <div>
                <p className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                  Match Summary
                </p>
                <p className="mt-1 text-xs text-on-surface leading-relaxed">
                  {aiDetails.caseMatch.summary}
                </p>
              </div>

              <div>
                <p className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                  Successful Resolution
                </p>
                <p className="mt-1 text-xs text-on-surface-variant leading-relaxed">
                  {aiDetails.caseMatch.resolution}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 border-t border-white/5 pt-4">
            <button
              type="button"
              className="w-full rounded-full border border-white/10 py-2 text-center text-xs font-medium text-on-surface transition-colors hover:border-primary/30 hover:bg-white/5"
            >
              Verify Case Match Details
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
