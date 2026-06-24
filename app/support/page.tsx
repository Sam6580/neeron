"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout";
import { getActiveAlerts } from "@/data/alerts";

interface PingNode {
  name: string;
  ip: string;
  latency: number | null;
  status: "unknown" | "success" | "failed";
}

export default function SupportPage() {
  const activeAlerts = getActiveAlerts();
  
  // Interactive Ping states
  const [nodes, setNodes] = useState<PingNode[]>([
    { name: "Bodø RAS Controller", ip: "10.220.10.4", latency: null, status: "unknown" },
    { name: "Optical DO Probe TNK-09", ip: "10.220.12.82", latency: null, status: "unknown" },
    { name: "Hardanger Automated Feeder", ip: "10.222.40.11", latency: null, status: "unknown" },
    { name: "ML Inference Server", ip: "10.100.5.20", latency: null, status: "unknown" },
  ]);
  const [isPinging, setIsPinging] = useState(false);
  const [pingLog, setPingLog] = useState<string[]>([]);

  const handlePingAll = () => {
    setIsPinging(true);
    setPingLog(["[SYSTEM] Initializing diagnostics sequence...", "[SYSTEM] Discovering network nodes..."]);
    
    // Reset statuses
    setNodes(prev => prev.map(n => ({ ...n, latency: null, status: "unknown" })));

    let currentIndex = 0;

    const interval = setInterval(() => {
      if (currentIndex >= nodes.length) {
        clearInterval(interval);
        setIsPinging(false);
        setPingLog(prev => [...prev, "[SYSTEM] Diagnostics sequence finished. All systems nominal."]);
        return;
      }

      const node = nodes[currentIndex];
      const simulatedLatency = Math.floor(Math.random() * 25) + 8; // 8ms to 32ms
      const isSuccessful = Math.random() > 0.05; // 95% success

      setNodes(prev => {
        const next = [...prev];
        next[currentIndex] = {
          ...next[currentIndex],
          latency: isSuccessful ? simulatedLatency : null,
          status: isSuccessful ? "success" : "failed",
        };
        return next;
      });

      setPingLog(prev => [
        ...prev,
        isSuccessful
          ? `[SUCCESS] Pinged ${node.name} (${node.ip}) - Response in ${simulatedLatency}ms`
          : `[FAILED] Connection timeout from ${node.name} (${node.ip})`
      ]);

      currentIndex++;
    }, 800);
  };

  return (
    <AppShell activePath="/support" title="Support" alertCount={activeAlerts.length}>
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-lg font-semibold text-on-surface">Operations Support & Diagnostics</h1>
        <p className="text-sm text-on-surface-variant">
          Contact NEERON site support, check live telemetry connectivity, or run diagnostic ping sweeps.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Support contacts */}
        <div className="lg:col-span-2 space-y-6">
          {/* Main Support Contact Card */}
          <div className="glass-panel rounded-2xl p-6 border border-white/5 bg-surface/50 backdrop-blur-xl">
            <h2 className="text-base font-semibold text-primary mb-2">NEERON Command Center Support</h2>
            <p className="text-xs text-on-surface-variant mb-6">
              Our aquaculture operations desks are active 24/7/365. For critical site incidents, coordinate with duty supervisors immediately.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border border-white/5 bg-[#050b17]/40 rounded-xl p-4 flex flex-col gap-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Duty Biologist Desk</span>
                <span className="text-sm font-semibold text-on-surface">Sarah Jenkins</span>
                <span className="text-xs text-primary">+47 450 11 922</span>
                <span className="text-xs text-on-surface-variant">Radio Channel: VHF CH-16 (Aquacult.)</span>
              </div>

              <div className="border border-white/5 bg-[#050b17]/40 rounded-xl p-4 flex flex-col gap-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Hardware Operations Support</span>
                <span className="text-sm font-semibold text-on-surface">Telemetry Operations Team</span>
                <span className="text-xs text-primary">support@neeron.ai</span>
                <span className="text-xs text-on-surface-variant">Response Time SLA: &lt; 15 minutes</span>
              </div>
            </div>
          </div>

          {/* Interactive Diagnostic Tool */}
          <div className="glass-panel rounded-2xl p-6 border border-white/5 bg-surface/50 backdrop-blur-xl">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-base font-semibold text-on-surface">Sensor Connectivity Diagnostics</h3>
                <p className="text-xs text-on-surface-variant">Ping active nodes directly to test hardware latency.</p>
              </div>
              <button
                type="button"
                onClick={handlePingAll}
                disabled={isPinging}
                className="rounded-full bg-primary text-on-primary shadow-[0_0_8px_rgba(71,214,255,0.4)] px-4 py-2 text-xs font-semibold hover:bg-primary-bright disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {isPinging ? "Executing Ping..." : "Ping Sensor Array"}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {nodes.map((node, i) => (
                <div key={i} className="border border-white/5 bg-[#050b17]/40 rounded-xl p-3 flex items-center justify-between">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs font-semibold text-on-surface">{node.name}</span>
                    <span className="text-[10px] font-mono text-on-surface-variant">{node.ip}</span>
                  </div>
                  <div>
                    {node.status === "unknown" && (
                      <span className="text-[10px] font-semibold text-on-surface-variant bg-white/5 px-2 py-0.5 rounded-full">
                        Ready
                      </span>
                    )}
                    {node.status === "success" && (
                      <span className="text-[10px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                        {node.latency} ms
                      </span>
                    )}
                    {node.status === "failed" && (
                      <span className="text-[10px] font-semibold text-error bg-error/10 px-2 py-0.5 rounded-full">
                        Timeout
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Diagnostic Logs */}
            {pingLog.length > 0 && (
              <div className="bg-[#050b17] border border-white/10 rounded-xl p-4 font-mono text-[10px] leading-relaxed max-h-48 overflow-y-auto space-y-1">
                {pingLog.map((log, lIdx) => (
                  <div
                    key={lIdx}
                    className={
                      log.startsWith("[SUCCESS]")
                        ? "text-primary"
                        : log.startsWith("[FAILED]")
                        ? "text-error"
                        : "text-on-surface-variant"
                    }
                  >
                    {log}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Global Network Status */}
        <div className="space-y-6">
          <div className="glass-panel rounded-2xl p-5 border border-white/5 bg-surface/50 backdrop-blur-xl">
            <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-4">Operations Center Status</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-on-surface font-medium">NEERON Prediction Core</span>
                <span className="badge-optimal text-[9px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider">
                  Nominal
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-on-surface font-medium">IoT Telemetry Broker</span>
                <span className="badge-optimal text-[9px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider">
                  Nominal
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-on-surface font-medium">Edge Computing Nodes</span>
                <span className="badge-optimal text-[9px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider">
                  99.9% Uptime
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-on-surface font-medium">AWS Satellite Backup</span>
                <span className="badge-optimal text-[9px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider">
                  Connected
                </span>
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-5 border border-white/5 bg-surface/50 backdrop-blur-xl">
            <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-3">Diagnostic Status</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              If telemetry connectivity drifts or packet loss exceeds 2.5%, the ML models automatically flag associated sensors with warning status registers.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
