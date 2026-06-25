"use client";

import Link from "next/link";
import { useAppData } from "@/lib/hooks/useAppData";
import { AppShell } from "@/components/layout";

export default function DocumentationPage() {
  const { getActiveAlerts } = useAppData();
  const activeAlerts = getActiveAlerts();

  const docSections = [
    {
      title: "Core Platform Architecture",
      description: "Understand the telemetry and data ingestion pipeline for the Atlantic Salmon precision aquaculture system.",
      articles: [
        { title: "Ingestion Pipeline Specs", readTime: "5 min read", category: "Data Flow" },
        { title: "Sensor Calibration Manual", readTime: "12 min read", category: "Hardware" },
        { title: "Modbus/RS485 Protocol Maps", readTime: "8 min read", category: "Networking" },
      ],
    },
    {
      title: "AI & ML Predictive Engines",
      description: "Technical references for biological growth modeling, risk prediction LSTM models, and XAI thresholds.",
      articles: [
        { title: "Logistic Growth S-Curve Modeling", readTime: "15 min read", category: "Modeling" },
        { title: "Explainable AI (XAI) Rule Engine", readTime: "10 min read", category: "AI Governance" },
        { title: "Disease Propagation LSTM Models", readTime: "18 min read", category: "MLOps" },
      ],
    },
    {
      title: "Biosecurity & Incident Response",
      description: "Operational guidelines for pathogen outbreaks, quarantine containment protocols, and veterinary compliance.",
      articles: [
        { title: "Sea Lice (Caligus) Management Plan", readTime: "20 min read", category: "Compliance" },
        { title: "Amoebic Gill Disease (AGD) Protocols", readTime: "14 min read", category: "Mitigation" },
        { title: "Biosecurity Incident Levels (1-4)", readTime: "7 min read", category: "Standard Ops" },
      ],
    },
  ];

  return (
    <AppShell activePath="/docs" title="Documentation" alertCount={activeAlerts.length}>
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-on-surface">Platform Documentation & Knowledge Base</h1>
        <p className="text-sm text-on-surface-variant">
          Technical user guides, predictive model parameters, aquaculture domain references, and standard operating procedures.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main Doc Directory */}
        <div className="lg:col-span-2 space-y-6">
          {docSections.map((section, index) => (
            <div key={index} className="glass-panel rounded-2xl p-6 border border-white/5 bg-surface/50 backdrop-blur-xl">
              <h2 className="text-base font-semibold text-primary mb-1">{section.title}</h2>
              <p className="text-xs text-on-surface-variant mb-4">{section.description}</p>
              
              <div className="divide-y divide-white/5">
                {section.articles.map((art, aIdx) => (
                  <div key={aIdx} className="group py-3.5 flex items-center justify-between hover:bg-white/[0.01] transition-colors rounded-lg px-2 -mx-2">
                    <div className="flex flex-col gap-1">
                      <span className="text-sm text-on-surface font-medium group-hover:text-primary transition-colors cursor-pointer">
                        {art.title}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] uppercase font-semibold text-on-surface-variant tracking-wider bg-white/5 px-2 py-0.5 rounded">
                          {art.category}
                        </span>
                        <span className="text-[10px] text-on-surface-variant/70">{art.readTime}</span>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="text-xs font-semibold text-primary opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1"
                    >
                      Read Article
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Sidebar References */}
        <div className="space-y-6">
          {/* Quick Lookup Panel */}
          <div className="glass-panel rounded-2xl p-5 border border-white/5 bg-surface/50 backdrop-blur-xl">
            <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-3">Biological Parameter Limits</h3>
            <div className="space-y-3.5 text-xs text-on-surface">
              <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                <span className="text-on-surface-variant">Optimal Temperature</span>
                <span className="font-semibold text-primary">8.0°C – 14.0°C</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                <span className="text-on-surface-variant">Dissolved Oxygen (DO)</span>
                <span className="font-semibold text-primary">&gt; 7.0 mg/L</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-white/5">
                <span className="text-on-surface-variant">pH Range</span>
                <span className="font-semibold text-primary">6.5 – 8.2</span>
              </div>
              <div className="flex justify-between items-center py-1.5">
                <span className="text-on-surface-variant">Ammonia Limit</span>
                <span className="font-semibold text-warning">&lt; 0.05 mg/L</span>
              </div>
            </div>
          </div>

          {/* Code Integration Panel */}
          <div className="glass-panel rounded-2xl p-5 border border-white/5 bg-surface/50 backdrop-blur-xl">
            <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-2">NEERON API SDK</h3>
            <p className="text-xs text-on-surface-variant mb-4">
              Query telemetry registers directly from terminal integrations.
            </p>
            <div className="bg-[#050b17] border border-white/10 rounded-xl p-3 font-mono text-[10px] text-primary space-y-1.5">
              <div><span className="text-on-surface-variant"># Fetch cage health score</span></div>
              <div>curl -X GET \</div>
              <div>&nbsp;&nbsp;https://api.neeron.ai/v1/cages/CH-05 \</div>
              <div>&nbsp;&nbsp;-H <span className="text-on-surface">&quot;Authorization: Bearer $KEY&quot;</span></div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
