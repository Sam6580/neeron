"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout";
import {
  formatCompact,
  formatNumber,
  formatRelativeTime,
  getTankDisplayId,
  getTankHealthStatusStyle,
} from "@/lib";
import { cn } from "@/lib/utils";
import { tanks } from "@/data/tanks";
import { zones } from "@/data/zones";
import { getActiveAlerts } from "@/data/alerts";
import { biosecurityRecords } from "@/data/biosecurity";

interface DiseaseRisk {
  pathogen: string;
  scientificName: string;
  riskPct: number;
  confidencePct: number;
  severity: "Low" | "Moderate" | "High" | "Critical";
  trend: "up" | "down" | "stable";
}

interface QuarantineZone {
  zoneName: string;
  reason: string;
  startDate: string;
  expectedClearance: string;
  status: "Quarantined" | "Restricted" | "Cleared";
}

interface InspectionEvent {
  timestamp: string;
  type: "inspection" | "lab_result" | "treatment" | "anomaly";
  inspector: string;
  description: string;
  outcome: string;
  status: "Completed" | "Pending" | "Logged";
}

interface PathogenThreat {
  name: string;
  scientific: string;
  threatLevel: "None" | "Mild" | "Elevated" | "High" | "Critical";
  confidencePct: number;
  lastScan: string;
}

export default function BiosecurityPage() {
  const activeAlerts = getActiveAlerts();
  const [hoveredCageId, setHoveredCageId] = useState<string | null>(null);

  // SECTION 2: Disease Risks Mock data
  const diseaseRisks: DiseaseRisk[] = [
    { pathogen: "Sea Lice", scientificName: "Caligus rogercresseyi", riskPct: 42, confidencePct: 91, severity: "Moderate", trend: "up" },
    { pathogen: "Amoebic Gill Disease (AGD)", scientificName: "Neoparamoeba perurans", riskPct: 28, confidencePct: 88, severity: "Low", trend: "stable" },
    { pathogen: "Furunculosis", scientificName: "Aeromonas salmonicida", riskPct: 5, confidencePct: 95, severity: "Low", trend: "down" },
    { pathogen: "ISA Virus", scientificName: "Infectious Salmon Anemia", riskPct: 2, confidencePct: 98, severity: "Low", trend: "stable" },
  ];

  // SECTION 3: Forecast mock data
  const diseaseForecasts = [
    { range: "7-Day Forecast", probability: 12, confidence: 95, impact: "Safe", desc: "Biological parameters remain stable. No treatment cycles projected." },
    { range: "14-Day Forecast", probability: 34, confidence: 89, impact: "Warning", desc: "Projected seawater temperature increase (+0.8°C) may accelerate sea lice counts in Loch Duich Cages." },
    { range: "30-Day Forecast", probability: 56, confidence: 81, impact: "Warning", desc: "Predictive model flags elevated AGD susceptibility scores in Chiloé Cage 05 due to salinity trends." },
  ];

  // SECTION 4: Quarantine Control list
  const quarantines: QuarantineZone[] = [
    { zoneName: "RAS Unit 04 — Bodø", reason: "Smolt cohort baselining & viral quarantine observation", startDate: "2026-06-10", expectedClearance: "2026-07-01", status: "Quarantined" },
    { zoneName: "Cage 05 — Chiloé", reason: "Post sea lice Azamethiphos treatment containment barrier", startDate: "2026-06-21", expectedClearance: "2026-06-28", status: "Restricted" },
  ];

  // SECTION 5: Health Inspection Timeline logs
  const timelineEvents: InspectionEvent[] = [
    { timestamp: "2026-06-22T07:15:00Z", type: "lab_result", inspector: "Dr. Ana Torres", description: "Cage 05 qPCR scan completed: ISA negative. Caligus count confirmed at 8.2 female adults per fish.", outcome: "Caligus count above limit (>6.0)", status: "Logged" },
    { timestamp: "2026-06-21T16:00:00Z", type: "treatment", inspector: "Carlos Mendez", description: "Emergency Azamethiphos 60-minute bath treatment administered to Cage 05.", outcome: "Treatment completed. Monitor post-bath stress.", status: "Completed" },
    { timestamp: "2026-06-20T10:30:00Z", type: "inspection", inspector: "Dr. James Reid", description: "Routine gill score assessment on 30 fish in Loch Duich Cage 07.", outcome: "AGD score 1-2 changes. No immediate action.", status: "Completed" },
    { timestamp: "2026-06-18T08:00:00Z", type: "treatment", inspector: "Ingrid Larsen", description: "Combined IPN/PD vaccine injection completed on Bodø smolt cohort.", outcome: "99.2% coverage achieved. Quarantine holds.", status: "Completed" },
    { timestamp: "2026-06-15T09:40:00Z", type: "anomaly", inspector: "Ecosystem AI Engine", description: "Zone Chiloé DO drop detected below 7.0 mg/L threshold for 15 minutes.", outcome: "Auto-aerators engaged. Oxygen stabilized.", status: "Logged" },
  ];

  // SECTION 6: AI Treatment recommendations
  const treatmentRecommendations = [
    { title: "Azamethiphos Bath Treatment", priority: "critical", confidence: 95, expectedOutcome: "Reduce Caligus adult count below 3.0/fish within 48h.", timeToEffect: "48 hours" },
    { title: "Auxiliary Aeration Bubbler Activation", priority: "high", confidence: 88, expectedOutcome: "Stabilize Dissolved Oxygen above 8.0 mg/L in Loch Duich.", timeToEffect: "2 hours" },
    { title: "Freshwater Bath Treatment (AGD)", priority: "medium", confidence: 82, expectedOutcome: "Reduce gill Neoparamoeba density and clear gill scores.", timeToEffect: "24 hours" },
  ];

  // SECTION 8: Pathogen threats list
  const pathogenThreats: PathogenThreat[] = [
    { name: "Sea Lice", scientific: "Caligus rogercresseyi", threatLevel: "High", confidencePct: 94, lastScan: "2 hours ago" },
    { name: "AGD Amoeba", scientific: "Neoparamoeba perurans", threatLevel: "Elevated", confidencePct: 88, lastScan: "12 hours ago" },
    { name: "ISA Virus", scientific: "Infectious Salmon Anemia", threatLevel: "None", confidencePct: 99, lastScan: "24 hours ago" },
    { name: "Furunculosis Bacteria", scientific: "Aeromonas salmonicida", threatLevel: "None", confidencePct: 98, lastScan: "2 days ago" },
  ];

  // SECTION 9: AI Insights
  const insights = [
    { priority: "critical", confidence: 94, zone: "Zone Chiloé Cage 05", message: "Suspend feeding on Cage 05 for 24h post Azamethiphos treatment to mitigate high gill respiration stresses." },
    { priority: "high", confidence: 88, zone: "Zone Loch Duich Cage 07", message: "Advance sea lice count auditing checklist by 3 days due to local thermal drift peaks (+1.2°C)." },
  ];

  // SECTION 7: Heatmap Cage Lookup
  const hoveredCageDetails = useMemo(() => {
    if (!hoveredCageId) return null;
    const tank = tanks.find(t => t.id === hoveredCageId);
    if (!tank) return null;
    const zone = zones.find(z => z.id === tank.zoneId);

    // Mock specific pathogen telemetry
    let liceCount = "0.0";
    let agdScore = "0.0";
    if (tank.id === "tank-ch-cage-05") {
      liceCount = "8.2 / fish";
      agdScore = "0.5";
    } else if (tank.id === "tank-ld-cage-07") {
      liceCount = "3.2 / fish";
      agdScore = "1.5";
    } else if (tank.status === "healthy") {
      liceCount = "0.4 / fish";
      agdScore = "0.1";
    }

    return {
      name: tank.name,
      idCode: getTankDisplayId(tank),
      zone: zone?.name || "Unknown Zone",
      health: tank.healthScore,
      status: tank.status,
      density: tank.stockingDensityKgM3,
      liceCount,
      agdScore,
    };
  }, [hoveredCageId]);

  return (
    <AppShell activePath="/biosecurity" title="Biosecurity & Health" alertCount={activeAlerts.length}>
      {/* Title section */}
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-on-surface">Biosecurity & Health Intelligence</h1>
        <p className="text-sm text-on-surface-variant">
          AI-powered disease surveillance, risk monitoring, quarantine management, and ecosystem health protection.
        </p>
      </div>

      {/* SECTION 1: Farm Health Overview (KPIs) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">Farm Health Index</span>
            <p className="text-2xl font-semibold text-on-surface mt-2">84.2 <span className="text-xs font-normal text-on-surface-variant">/100</span></p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>vs last week: -1.8%</span>
            <span className="badge-optimal px-1.5 py-0.5 rounded font-bold text-[8px] uppercase">Good</span>
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">Disease Risk Index</span>
            <p className="text-2xl font-semibold text-warning mt-2">18.4%</p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>vs last month: +2.4%</span>
            <span className="badge-warning px-1.5 py-0.5 rounded font-bold text-[8px] uppercase">Moderate</span>
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">Compliance rating</span>
            <p className="text-2xl font-semibold text-on-surface mt-2">98.6%</p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>NS 9416 standards</span>
            <span className="badge-optimal px-1.5 py-0.5 rounded font-bold text-[8px] uppercase">Compliant</span>
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">Active Incidents</span>
            <p className="text-2xl font-semibold text-error mt-2">2 Incidents</p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>Critical hold Cages</span>
            <span className="badge-critical px-1.5 py-0.5 rounded font-bold text-[8px] uppercase">Critical</span>
          </div>
        </div>
      </div>

      {/* Main 3-Column Dashboard Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-6">
        {/* Left column (col-span 2 on lg) */}
        <div className="lg:col-span-2 space-y-6">
          {/* SECTION 2 & 3: Disease Intelligence & Forecast */}
          <div className="glass-panel rounded-2xl p-6">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4">
              Biological Risk Forecast & Surveillance
            </h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 mb-6">
              {/* Risks cards */}
              <div className="space-y-3">
                <h3 className="text-[10px] font-bold uppercase tracking-widest text-primary border-b border-white/5 pb-1">Pathogen Risk Gauges</h3>
                {diseaseRisks.map((risk, i) => (
                  <div key={i} className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-3.5 flex justify-between items-center">
                    <div>
                      <h4 className="text-xs font-semibold text-on-surface">{risk.pathogen}</h4>
                      <p className="text-[9px] text-on-surface-variant italic mt-0.5">{risk.scientificName}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-bold text-on-surface">
                        {risk.riskPct}% <span className="text-[10px] text-on-surface-variant font-normal">risk</span>
                      </p>
                      <span className={cn("inline-block rounded-full px-1.5 py-0.2 text-[8px] font-bold uppercase tracking-wider mt-0.5",
                        risk.severity === "Critical" || risk.severity === "High" ? "badge-critical" : risk.severity === "Moderate" ? "badge-warning" : "badge-optimal"
                      )}>
                        {risk.severity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Forecast cards */}
              <div className="space-y-3">
                <h3 className="text-[10px] font-bold uppercase tracking-widest text-primary border-b border-white/5 pb-1">AI 30-Day Disease Forecast</h3>
                {diseaseForecasts.map((fc, i) => (
                  <div key={i} className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-3 flex flex-col justify-between h-[64px]">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="font-semibold text-on-surface">{fc.range}</span>
                      <span className={cn("rounded px-1.5 py-0.2 font-bold text-[8px] uppercase", fc.impact === "Warning" ? "badge-warning" : "badge-optimal")}>
                        {fc.impact}
                      </span>
                    </div>
                    <p className="text-[9px] text-on-surface-variant truncate mt-1">{fc.desc}</p>
                    <div className="flex justify-between text-[9px] text-on-surface-variant mt-1.5 border-t border-white/5 pt-1">
                      <span>Probability: <strong className="text-on-surface">{fc.probability}%</strong></span>
                      <span>Confidence: {fc.confidence}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SECTION 7: Biosecurity Risk Heatmap */}
          <div className="glass-panel rounded-2xl p-6 relative">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-4">
              <div>
                <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                  Biosecurity Risk Heatmap
                </h2>
                <p className="text-[10px] text-on-surface-variant mt-0.5">
                  Visual lease mapping grid. Hover over any cage block to view live biological monitoring records.
                </p>
              </div>

              <div className="flex items-center gap-3 text-[9px] text-on-surface-variant font-medium shrink-0">
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-primary/20 border border-primary/60" />Safe</span>
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-warning/20 border border-warning/60" />Warning</span>
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-error/20 border border-error/60" />Critical</span>
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-white/5 border border-white/20" />Maint.</span>
              </div>
            </div>

            {/* Heatmap Grid */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-4 space-y-4">
                {zones.map((zone) => {
                  const zoneTanks = tanks.filter(t => t.zoneId === zone.id);
                  return (
                    <div key={zone.id} className="space-y-2">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">{zone.name}</p>
                      <div className="flex flex-wrap gap-2.5">
                        {zoneTanks.map((tank) => {
                          const idCode = getTankDisplayId(tank);
                          const isHovered = hoveredCageId === tank.id;
                          return (
                            <button
                              key={tank.id}
                              type="button"
                              onMouseEnter={() => setHoveredCageId(tank.id)}
                              onMouseLeave={() => setHoveredCageId(null)}
                              className={cn(
                                "h-9 w-16 rounded-xl flex items-center justify-center text-[10px] font-bold border transition-all cursor-crosshair select-none relative",
                                tank.status === "healthy"
                                  ? "bg-primary/10 border-primary/30 text-primary hover:bg-primary/20"
                                  : tank.status === "warning"
                                  ? "bg-warning/10 border-warning/30 text-warning hover:bg-warning/20"
                                  : tank.status === "critical"
                                  ? "bg-error/10 border-error/30 text-error hover:bg-error/20"
                                  : "bg-white/5 border-white/10 text-on-surface-variant hover:bg-white/10",
                                isHovered && "scale-105 border-white/40 ring-1 ring-white/10 shadow-[0_0_12px_rgba(255,255,255,0.08)]"
                              )}
                            >
                              {idCode}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Hover Details Panel */}
              <div className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-4 flex flex-col justify-between min-h-[180px]">
                {hoveredCageDetails ? (
                  <div className="space-y-3.5">
                    <div className="flex items-start justify-between border-b border-white/5 pb-2">
                      <div>
                        <h4 className="text-sm font-bold text-on-surface">{hoveredCageDetails.idCode}</h4>
                        <p className="text-[10px] text-on-surface-variant mt-0.5">{hoveredCageDetails.name}</p>
                      </div>
                      <span className={cn("rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest", getTankHealthStatusStyle(hoveredCageDetails.status as any))}>
                        {hoveredCageDetails.status}
                      </span>
                    </div>

                    <dl className="grid grid-cols-2 gap-y-2 gap-x-4 text-xs">
                      <div>
                        <dt className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Lease Zone</dt>
                        <dd className="mt-0.5 text-on-surface font-semibold">{hoveredCageDetails.zone}</dd>
                      </div>
                      <div>
                        <dt className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Stocking Density</dt>
                        <dd className="mt-0.5 text-on-surface font-semibold">{hoveredCageDetails.density.toFixed(1)} kg/m³</dd>
                      </div>
                      <div>
                        <dt className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Sea Lice Count</dt>
                        <dd className="mt-0.5 text-primary font-bold">{hoveredCageDetails.liceCount}</dd>
                      </div>
                      <div>
                        <dt className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">AGD Amoeba Score</dt>
                        <dd className="mt-0.5 text-primary font-bold">{hoveredCageDetails.agdScore} / 5</dd>
                      </div>
                    </dl>
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center p-4">
                    <svg className="h-8 w-8 text-on-surface-variant opacity-40 mb-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.042 9.152c.582.448 1.148.89 1.676 1.345m-1.676-1.345c-.528-.407-1.125-.826-1.777-1.229M15.042 9.152a53.078 53.078 0 0 1-5.007 5.006m5.007-5.006a38.22 38.22 0 0 0-4.995-4.996m4.995 4.996c-.456.53-.898 1.096-1.347 1.677m-3.648 3.329A38.217 38.217 0 0 0 4.995 9.151m5.05 5.007a53.075 53.075 0 0 1-5.006-5.007m5.006 5.007c-.53-.456-1.096-.897-1.677-1.347m0 0a38.217 38.217 0 0 0-4.996 4.995" />
                    </svg>
                    <p className="text-[11px] text-on-surface-variant">Hover over any cage coordinate block to unwrap telemetry logs.</p>
                  </div>
                )}

                <div className="border-t border-white/5 pt-2 mt-4 text-[9px] text-on-surface-variant flex justify-between">
                  <span>Interactive Map v1.2</span>
                  <span>Sensor coverage: 100%</span>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 5: Health Inspection Timeline */}
          <div className="glass-panel rounded-2xl p-6">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4">
              Health Inspection & Treatment Log Timeline
            </h2>
            <div className="relative pl-6 border-l border-white/5 space-y-6">
              {timelineEvents.map((ev, i) => (
                <div key={i} className="relative">
                  {/* Timeline point */}
                  <span className={cn(
                    "absolute -left-[30px] top-1 h-3.5 w-3.5 rounded-full border-2 border-background flex items-center justify-center",
                    ev.type === "lab_result"
                      ? "bg-error"
                      : ev.type === "treatment"
                      ? "bg-primary"
                      : ev.type === "anomaly"
                      ? "bg-warning"
                      : "bg-on-surface-variant"
                  )} />
                  
                  <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
                    <div>
                      <span className="text-[10px] text-on-surface-variant font-medium">
                        {formatRelativeTime(ev.timestamp)} · Inspector: <strong className="text-on-surface">{ev.inspector}</strong>
                      </span>
                      <h4 className="text-xs font-semibold text-on-surface mt-0.5">{ev.description}</h4>
                    </div>
                    <div className="text-left md:text-right shrink-0 mt-1 md:mt-0">
                      <p className="text-[10px] font-semibold text-primary">{ev.outcome}</p>
                      <span className={cn("inline-block rounded px-1.5 py-0.2 text-[8px] font-bold uppercase mt-1",
                        ev.status === "Completed" ? "badge-optimal" : "badge-warning"
                      )}>
                        {ev.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SECTION 10: Compliance & Audit Status */}
          <div className="glass-panel rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                Compliance, Certification & Audit Register
              </h2>
              <span className="text-[10px] text-primary font-bold">NS 9416 Standard Audit Log</span>
            </div>
            
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-4">
              <div className="bg-[#0b1326]/40 border border-white/5 rounded-xl p-3 flex flex-col justify-between h-[64px]">
                <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Regulatory Compliance</span>
                <p className="text-lg font-bold text-on-surface">98.6% <span className="text-[9px] font-normal text-on-surface-variant">Score</span></p>
              </div>
              <div className="bg-[#0b1326]/40 border border-white/5 rounded-xl p-3 flex flex-col justify-between h-[64px]">
                <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Certification Status</span>
                <p className="text-sm font-bold text-primary">ASC & GLOBALG.A.P.</p>
              </div>
              <div className="bg-[#0b1326]/40 border border-white/5 rounded-xl p-3 flex flex-col justify-between h-[64px]">
                <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">Documentation Health</span>
                <p className="text-lg font-bold text-on-surface">100% <span className="text-[9px] font-normal text-on-surface-variant">Index</span></p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-on-surface border-t border-white/5">
                <thead className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant">
                  <tr>
                    <th className="py-2">Audited Asset</th>
                    <th className="py-2">Auditor</th>
                    <th className="py-2 text-center">Score</th>
                    <th className="py-2 text-right">Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  <tr className="hover:bg-white/5">
                    <td className="py-2 font-semibold">Hatchery Facility A (RAS Bodø)</td>
                    <td className="py-2">Robert Chen (Lloyd's Register)</td>
                    <td className="py-2 text-center font-bold text-primary">98 / 100</td>
                    <td className="py-2 text-right"><span className="badge-optimal text-[8px] font-bold uppercase px-1.5 py-0.5 rounded">Passed</span></td>
                  </tr>
                  <tr className="hover:bg-white/5">
                    <td className="py-2 font-semibold">Grow-out Pond Area 03 (Loch Duich)</td>
                    <td className="py-2">Robert Chen (Lloyd's Register)</td>
                    <td className="py-2 text-center font-bold text-primary">92 / 100</td>
                    <td className="py-2 text-right"><span className="badge-optimal text-[8px] font-bold uppercase px-1.5 py-0.5 rounded">Passed</span></td>
                  </tr>
                  <tr className="hover:bg-white/5">
                    <td className="py-2 font-semibold">Visitor Entrance & Disinfection Barriers</td>
                    <td className="py-2">Marcus Vance (Global Trust)</td>
                    <td className="py-2 text-center font-bold text-primary">100 / 100</td>
                    <td className="py-2 text-right"><span className="badge-optimal text-[8px] font-bold uppercase px-1.5 py-0.5 rounded">Passed</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right column (col-span 1 on lg) */}
        <div className="space-y-6">
          {/* SECTION 6: Treatment Recommendation Engine */}
          <div className="glass-panel-glow rounded-2xl p-6 min-h-[300px] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-white/5 pb-2 mb-4">
                <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant flex items-center gap-1.5">
                  <svg className="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
                  </svg>
                  Treatment Recommendations
                </h2>
                <span className="badge-optimal text-[8px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full">AI Active</span>
              </div>

              <div className="space-y-3">
                {treatmentRecommendations.map((rec, i) => (
                  <div key={i} className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-3.5 flex flex-col gap-2 transition-all hover:border-primary/20">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-on-surface">{rec.title}</h3>
                      <span className={cn("rounded px-1.5 py-0.2 text-[8px] font-bold uppercase tracking-widest border",
                        rec.priority === "critical" ? "bg-error/10 text-error border-error/20" : rec.priority === "high" ? "bg-warning/10 text-warning border-warning/20" : "bg-primary/10 text-primary border-primary/20"
                      )}>
                        {rec.priority}
                      </span>
                    </div>
                    <div className="space-y-0.5 text-[10px] text-on-surface-variant">
                      <p><strong className="text-primary">Expected:</strong> {rec.expectedOutcome}</p>
                      <p><strong className="text-on-surface">Time to Effect:</strong> {rec.timeToEffect} ({rec.confidence}% conf.)</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SECTION 4: Quarantine & Containment Control */}
          <div className="glass-panel rounded-2xl p-6 min-h-[220px] flex flex-col justify-between">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant border-b border-white/5 pb-2 mb-4">
                Quarantine & Containment Control
              </h2>
              <div className="space-y-3">
                {quarantines.map((q, i) => (
                  <div key={i} className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-3 flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-on-surface">{q.zoneName}</h3>
                      <span className={cn("rounded px-1.5 py-0.2 text-[8px] font-bold uppercase tracking-widest",
                        q.status === "Quarantined" ? "badge-critical" : "badge-warning"
                      )}>
                        {q.status}
                      </span>
                    </div>
                    <p className="text-[10px] text-on-surface-variant leading-relaxed">
                      {q.reason}
                    </p>
                    <div className="flex justify-between text-[9px] text-on-surface-variant border-t border-white/5 pt-1 mt-1">
                      <span>Started: {q.startDate}</span>
                      <span>Clearance: {q.expectedClearance}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SECTION 8: Pathogen Monitoring Center */}
          <div className="glass-panel rounded-2xl p-6 min-h-[240px] flex flex-col justify-between">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant border-b border-white/5 pb-2 mb-4">
                Pathogen Monitoring Center
              </h2>
              <div className="space-y-3.5">
                {pathogenThreats.map((pathogen, i) => (
                  <div key={i} className="flex justify-between items-center text-xs">
                    <div>
                      <h4 className="font-semibold text-on-surface">{pathogen.name}</h4>
                      <p className="text-[9px] text-on-surface-variant italic">{pathogen.scientific}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className={cn("rounded-full px-1.5 py-0.2 text-[8px] font-bold uppercase tracking-widest",
                        pathogen.threatLevel === "High" || pathogen.threatLevel === "Elevated" ? "badge-warning" : "badge-optimal"
                      )}>
                        {pathogen.threatLevel}
                      </span>
                      <p className="text-[9px] text-on-surface-variant mt-0.5">Scan conf: {pathogen.confidencePct}%</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-4 border-t border-white/5 pt-2 text-center text-[9px] text-on-surface-variant">
              System Scan: Furunculosis / ISA PCR logs resolved 24h ago
            </div>
          </div>

          {/* SECTION 9: AI Insights Center */}
          <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between min-h-[240px]">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant border-b border-white/5 pb-2 mb-4">
                AI Insights Center
              </h2>
              <div className="space-y-3.5">
                {insights.map((ins, i) => (
                  <div key={i} className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-3.5 flex flex-col gap-1.5">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="font-bold text-on-surface">{ins.zone}</span>
                      <span className={cn("rounded-full px-1.5 py-0.2 text-[8px] font-bold uppercase tracking-widest",
                        ins.priority === "critical" ? "badge-critical" : "badge-warning"
                      )}>
                        {ins.priority}
                      </span>
                    </div>
                    <p className="text-[11px] leading-relaxed text-on-surface-variant">{ins.message}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
