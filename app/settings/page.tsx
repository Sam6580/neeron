"use client";

import { useMemo, useState } from "react";
import { useAppData } from "@/lib/hooks/useAppData";
import Link from "next/link";
import { AppShell } from "@/components/layout";
import {
  formatCompact,
  formatNumber,
  formatRelativeTime,
} from "@/lib";
import { cn } from "@/lib/utils";

// Interfaces for Settings page
interface SensorDevice {
  id: string;
  type: string;
  status: "Active" | "Warning" | "Calibration Overdue" | "Offline";
  calibration: string;
  signal: "Strong" | "Medium" | "Weak";
}

interface AIModelConfig {
  name: string;
  algorithm: string;
  accuracy: number;
  status: "Active" | "Retraining" | "Offline";
  lastRetrained: string;
}

interface TeamUser {
  name: string;
  role: string;
  status: "Online" | "Away" | "Offline";
}

interface ConsoleLog {
  level: "INFO" | "WARNING" | "ERROR";
  message: string;
  time: string;
}

export default function SettingsPage() {
  const { getActiveAlerts } = useAppData();
  const activeAlerts = getActiveAlerts();

  // Threshold States (Section 4)
  const [tempMin, setTempMin] = useState(22.0);
  const [tempMax, setTempMax] = useState(28.0);
  const [phMin, setPhMin] = useState(6.8);
  const [phMax, setPhMax] = useState(7.4);
  const [doMin, setDoMin] = useState(6.0);
  const [doMax, setDoMax] = useState(10.0);
  const [ammoniaMin, setAmmoniaMin] = useState(0.00);
  const [ammoniaMax, setAmmoniaMax] = useState(0.05);

  const [isSaved, setIsSaved] = useState(false);

  // SECTION 2: Devices mock database
  const [devices, setDevices] = useState<SensorDevice[]>([
    { id: "TNK-01-TEMP", type: "Temperature Sensor", status: "Active", calibration: "Due in 14 days", signal: "Strong" },
    { id: "TNK-01-PH", type: "pH Probe", status: "Warning", calibration: "Overdue", signal: "Medium" },
    { id: "TNK-01-DO", type: "Dissolved Oxygen", status: "Active", calibration: "Due in 7 days", signal: "Strong" },
    { id: "AERATOR-SEC4", type: "Aerator Controller", status: "Active", calibration: "N/A", signal: "Strong" },
    { id: "FEEDER-A7", type: "Automated Feeder", status: "Active", calibration: "Due in 30 days", signal: "Strong" },
  ]);

  // SECTION 5: AI Models database
  const [models, setModels] = useState<AIModelConfig[]>([
    { name: "Water Quality Predictor", algorithm: "XGBoost", accuracy: 98.4, status: "Active", lastRetrained: "12h ago" },
    { name: "Disease Outbreak Predictor", algorithm: "Random Forest", accuracy: 94.2, status: "Active", lastRetrained: "3 days ago" },
    { name: "PSI Predictor", algorithm: "LSTM", accuracy: 90.5, status: "Active", lastRetrained: "1 day ago" },
    { name: "Feed Optimization Engine", algorithm: "Gradient Boosting", accuracy: 95.1, status: "Active", lastRetrained: "8 hours ago" },
    { name: "Harvest Optimizer", algorithm: "Ensemble Model", accuracy: 92.7, status: "Active", lastRetrained: "2 days ago" },
  ]);

  // SECTION 6: Team Management database
  const teamUsers: TeamUser[] = [
    { name: "Sarah Jenkins", role: "Chief Biologist", status: "Online" },
    { name: "Marcus Chen", role: "Operations Lead", status: "Online" },
    { name: "Alex Rivera", role: "Site Manager", status: "Away" },
    { name: "Ingrid Larsen", role: "Aquaculture Analyst", status: "Online" },
  ];

  // SECTION 9: System Event Logs database
  const consoleLogs: ConsoleLog[] = [
    { level: "INFO", message: "Sensor TNK-01-TEMP calibrated successfully", time: "07:32:04" },
    { level: "INFO", message: "Water Quality Predictor retrained", time: "07:12:45" },
    { level: "WARNING", message: "pH Sensor TNK-01-PH variance detected", time: "06:44:12" },
    { level: "INFO", message: "Daily backup completed", time: "05:30:00" },
    { level: "INFO", message: "Forecast reliability improved to 94.2%", time: "04:15:22" },
    { level: "INFO", message: "New telemetry node discovered", time: "03:02:11" },
    { level: "WARNING", message: "DO Sensor drift exceeds threshold", time: "01:24:55" },
    { level: "INFO", message: "Validation completed for PSI Predictor", time: "00:05:10" },
  ];

  const handleSaveThresholds = () => {
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const handleResetThresholds = () => {
    setTempMin(22.0);
    setTempMax(28.0);
    setPhMin(6.8);
    setPhMax(7.4);
    setDoMin(6.0);
    setDoMax(10.0);
    setAmmoniaMin(0.00);
    setAmmoniaMax(0.05);
  };

  const handleRetrainModel = (index: number) => {
    const updated = [...models];
    updated[index].status = "Retraining";
    updated[index].lastRetrained = "Just now";
    setModels(updated);
    setTimeout(() => {
      const restored = [...updated];
      restored[index].status = "Active";
      restored[index].accuracy = Math.round((restored[index].accuracy + (Math.random() * 0.4 - 0.2)) * 10) / 10;
      setModels(restored);
    }, 4000);
  };

  return (
    <AppShell activePath="/settings" title="Settings & Operations" alertCount={activeAlerts.length}>
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-lg font-semibold text-on-surface">Settings & Operations Control</h1>
          <p className="text-sm text-on-surface-variant">
            Sensor infrastructure, AI model governance, threshold management and enterprise administration.
          </p>
        </div>
        <div className="flex gap-2.5 shrink-0 self-start sm:self-auto">
          <button
            type="button"
            className="rounded-full border border-white/10 px-4 py-2 text-xs font-semibold text-on-surface-variant hover:border-white/20 hover:text-on-surface transition-colors"
          >
            Refresh Data
          </button>
          <button
            type="button"
            className="rounded-full bg-primary text-on-primary shadow-[0_0_8px_rgba(71,214,255,0.4)] px-4 py-2 text-xs font-semibold hover:bg-primary-bright transition-colors"
          >
            Add Device
          </button>
        </div>
      </div>

      {/* SECTION 1: Operations Overview (KPIs) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        {/* KPI 1: Sensor Infrastructure */}
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">Sensor Infrastructure</span>
              <span className="badge-optimal text-[8px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full">
                98% Uptime
              </span>
            </div>
            <p className="text-2xl font-semibold text-on-surface mt-2">42 Devices</p>
          </div>
          <div className="mt-3 flex items-center gap-4 border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-primary" />39 Online</span>
            <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-warning" />3 Maint.</span>
          </div>
        </div>

        {/* KPI 2: System Latency */}
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">System Latency</span>
              <span className="text-primary text-[10px] font-bold">
                Stable
              </span>
            </div>
            <p className="text-2xl font-semibold text-on-surface mt-2">14 ms</p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>vs. 24h baseline</span>
            <span className="text-primary font-medium">Improved by 2 ms</span>
          </div>
        </div>

        {/* KPI 3: Data Storage */}
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">Data Storage</span>
              <span className="text-[10px] font-semibold text-on-surface-variant">Active</span>
            </div>
            <p className="text-2xl font-semibold text-on-surface mt-2">1.2 TB</p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>AWS Cloud Replica</span>
            <span className="font-semibold text-primary">Backup in 2h 15m</span>
          </div>
        </div>

        {/* KPI 4: AI Systems */}
        <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">AI Systems</span>
              <span className="badge-optimal text-[8px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full">
                Operational
              </span>
            </div>
            <p className="text-2xl font-semibold text-on-surface mt-2">5 Active Models</p>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-white/5 pt-2 text-[10px] text-on-surface-variant">
            <span>Accuracy Avg: 94.2%</span>
            <span className="font-semibold text-primary">All Nominals</span>
          </div>
        </div>
      </div>

      {/* Main Grid Layout (Desktop: 3 Columns, Tablet: 2 Columns, Mobile: 1 Column) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
        
        {/* COLUMN 1: Sensors, Sliders & Team Management */}
        <div className="space-y-6 lg:col-span-1">
          
          {/* SECTION 2: Sensor Management */}
          <div className="glass-panel rounded-2xl p-6">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                Sensor Management
              </h2>
              <span className="text-[10px] text-on-surface-variant font-medium">5 active nodes</span>
            </div>
            <p className="text-[10px] text-on-surface-variant mb-4 leading-relaxed">
              Manage, calibrate and monitor connected telemetry devices.
            </p>

            <div className="overflow-x-auto mb-4">
              <table className="w-full text-left text-xs text-on-surface">
                <thead className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant border-b border-white/5">
                  <tr>
                    <th className="py-2">Device ID</th>
                    <th className="py-2 text-center">Status</th>
                    <th className="py-2">Calibration</th>
                    <th className="py-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {devices.map((dev) => (
                    <tr key={dev.id} className="hover:bg-white/5 transition-colors">
                      <td className="py-2.5">
                        <p className="font-semibold">{dev.id}</p>
                        <p className="text-[8px] text-on-surface-variant">{dev.type}</p>
                      </td>
                      <td className="py-2.5 text-center">
                        <span className={cn("inline-block h-1.5 w-1.5 rounded-full",
                          dev.status === "Active" ? "bg-primary shadow-[0_0_6px_rgba(71,214,255,0.6)]" : "bg-warning animate-pulse"
                        )} />
                      </td>
                      <td className="py-2.5 text-on-surface-variant">
                        <span className={cn(dev.calibration === "Overdue" ? "text-error font-bold" : "")}>
                          {dev.calibration}
                        </span>
                      </td>
                      <td className="py-2.5 text-right">
                        <button
                          type="button"
                          className={cn(
                            "rounded px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider border",
                            dev.calibration === "Overdue"
                              ? "bg-warning/10 text-warning border-warning/20 hover:bg-warning/20"
                              : "bg-white/5 text-on-surface-variant border-white/10 hover:bg-white/10 hover:text-on-surface"
                          )}
                        >
                          {dev.calibration === "Overdue" ? "Calibrate" : dev.id.startsWith("AERATOR") ? "Diagnose" : "Manage"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button
              type="button"
              className="w-full rounded-full border border-white/10 py-2 text-center text-xs font-semibold text-on-surface transition-colors hover:border-primary/30 hover:bg-white/5"
            >
              Scan New Devices
            </button>
          </div>

          {/* SECTION 4: Global Threshold Management */}
          <div className="glass-panel rounded-2xl p-6">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4 border-b border-white/5 pb-2">
              Global Threshold Configuration
            </h2>

            <div className="space-y-4 mb-6">
              {/* Temp Range Slider */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-on-surface-variant">Water Temperature</span>
                  <span className="text-primary font-bold">{tempMin.toFixed(1)}°C — {tempMax.toFixed(1)}°C</span>
                </div>
                <div className="flex gap-4 items-center">
                  <input
                    type="range"
                    min="15"
                    max="25"
                    step="0.5"
                    value={tempMin}
                    onChange={(e) => setTempMin(parseFloat(e.target.value))}
                    className="w-full accent-primary h-1 bg-white/10 rounded-lg cursor-pointer"
                  />
                  <input
                    type="range"
                    min="25"
                    max="35"
                    step="0.5"
                    value={tempMax}
                    onChange={(e) => setTempMax(parseFloat(e.target.value))}
                    className="w-full accent-primary h-1 bg-white/10 rounded-lg cursor-pointer"
                  />
                </div>
              </div>

              {/* pH Range Slider */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-on-surface-variant">pH Level</span>
                  <span className="text-primary font-bold">{phMin.toFixed(1)} — {phMax.toFixed(1)}</span>
                </div>
                <div className="flex gap-4 items-center">
                  <input
                    type="range"
                    min="5.5"
                    max="7.0"
                    step="0.1"
                    value={phMin}
                    onChange={(e) => setPhMin(parseFloat(e.target.value))}
                    className="w-full accent-primary h-1 bg-white/10 rounded-lg cursor-pointer"
                  />
                  <input
                    type="range"
                    min="7.0"
                    max="8.5"
                    step="0.1"
                    value={phMax}
                    onChange={(e) => setPhMax(parseFloat(e.target.value))}
                    className="w-full accent-primary h-1 bg-white/10 rounded-lg cursor-pointer"
                  />
                </div>
              </div>

              {/* DO Slider */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-on-surface-variant">Dissolved Oxygen</span>
                  <span className="text-primary font-bold">{doMin.toFixed(1)} — {doMax.toFixed(1)} mg/L</span>
                </div>
                <div className="flex gap-4 items-center">
                  <input
                    type="range"
                    min="4.0"
                    max="8.0"
                    step="0.2"
                    value={doMin}
                    onChange={(e) => setDoMin(parseFloat(e.target.value))}
                    className="w-full accent-primary h-1 bg-white/10 rounded-lg cursor-pointer"
                  />
                  <input
                    type="range"
                    min="8.0"
                    max="12.0"
                    step="0.2"
                    value={doMax}
                    onChange={(e) => setDoMax(parseFloat(e.target.value))}
                    className="w-full accent-primary h-1 bg-white/10 rounded-lg cursor-pointer"
                  />
                </div>
              </div>

              {/* Ammonia Slider */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-on-surface-variant">Ammonia Index</span>
                  <span className="text-primary font-bold">{ammoniaMin.toFixed(2)} — {ammoniaMax.toFixed(2)} ppm</span>
                </div>
                <div className="flex gap-4 items-center">
                  <input
                    type="range"
                    min="0.00"
                    max="0.03"
                    step="0.01"
                    value={ammoniaMin}
                    onChange={(e) => setAmmoniaMin(parseFloat(e.target.value))}
                    className="w-full accent-primary h-1 bg-white/10 rounded-lg cursor-pointer"
                  />
                  <input
                    type="range"
                    min="0.03"
                    max="0.10"
                    step="0.01"
                    value={ammoniaMax}
                    onChange={(e) => setAmmoniaMax(parseFloat(e.target.value))}
                    className="w-full accent-primary h-1 bg-white/10 rounded-lg cursor-pointer"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-2.5">
              <button
                type="button"
                onClick={handleResetThresholds}
                className="flex-1 rounded-full border border-white/10 py-2 text-xs font-semibold text-on-surface hover:bg-white/5 transition-colors"
              >
                Reset Defaults
              </button>
              <button
                type="button"
                onClick={handleSaveThresholds}
                className="flex-1 rounded-full bg-primary text-on-primary font-bold shadow-[0_0_8px_rgba(71,214,255,0.4)] py-2 text-xs hover:bg-primary-bright transition-colors relative"
              >
                {isSaved ? "Saved Successfully ✓" : "Save Thresholds"}
              </button>
            </div>
          </div>

          {/* SECTION 6: Team Management */}
          <div className="glass-panel rounded-2xl p-6">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4 border-b border-white/5 pb-2">
              Team & Permissions Management
            </h2>

            <div className="overflow-x-auto mb-4">
              <table className="w-full text-left text-xs text-on-surface">
                <thead className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant">
                  <tr>
                    <th className="py-2">User Profile</th>
                    <th className="py-2">Operational Role</th>
                    <th className="py-2 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {teamUsers.map((user, i) => (
                    <tr key={i} className="hover:bg-white/5">
                      <td className="py-2 font-semibold">{user.name}</td>
                      <td className="py-2 text-on-surface-variant">{user.role}</td>
                      <td className="py-2 text-right flex items-center justify-end gap-1.5">
                        <span className={cn("inline-block h-1.5 w-1.5 rounded-full",
                          user.status === "Online" ? "bg-primary" : user.status === "Away" ? "bg-warning" : "bg-white/10"
                        )} />
                        <span className="text-[10px] font-medium text-on-surface-variant">{user.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex gap-2.5">
              <button
                type="button"
                className="flex-1 rounded-full border border-white/10 py-2 text-xs font-semibold text-on-surface hover:bg-white/5"
              >
                Invite User
              </button>
              <button
                type="button"
                className="flex-1 rounded-full border border-white/10 py-2 text-xs font-semibold text-on-surface hover:bg-white/5"
              >
                Manage Permissions
              </button>
            </div>
          </div>
        </div>

        {/* COLUMN 2: AI Model Governance, AI Ops Monitor & Terminal Console */}
        <div className="space-y-6 lg:col-span-1">
          
          {/* SECTION 5: AI Model Management */}
          <div className="glass-panel rounded-2xl p-6">
            <div className="border-b border-white/5 pb-2 mb-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                AI Model Governance
              </h2>
              <p className="text-[10px] text-on-surface-variant mt-0.5">
                Monitor and govern operational machine learning systems.
              </p>
            </div>

            <div className="space-y-3.5">
              {models.map((model, i) => (
                <div key={i} className="border border-white/5 bg-[#0b1326]/40 rounded-xl p-3.5 flex flex-col justify-between">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-on-surface">{model.name}</h3>
                      <p className="text-[9px] text-on-surface-variant mt-0.5">Algorithm: {model.algorithm}</p>
                    </div>
                    <span className={cn("text-[9px] font-bold uppercase tracking-wider rounded px-1.5 py-0.2",
                      model.status === "Active" ? "badge-optimal" : "badge-warning animate-pulse"
                    )}>
                      {model.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-on-surface-variant mt-3 border-t border-white/5 pt-2">
                    <span>Acc: <strong className="text-on-surface">{model.accuracy}%</strong></span>
                    <span>Retrained: {model.lastRetrained}</span>
                  </div>

                  <div className="flex gap-2.5 mt-3 pt-2 border-t border-white/5">
                    <button
                      type="button"
                      onClick={() => handleRetrainModel(i)}
                      disabled={model.status === "Retraining"}
                      className="flex-1 rounded py-1 text-[9px] font-bold uppercase tracking-widest bg-white/5 border border-white/10 hover:bg-primary/10 hover:text-primary transition-all disabled:opacity-50"
                    >
                      Retrain
                    </button>
                    <button
                      type="button"
                      className="flex-1 rounded py-1 text-[9px] font-bold uppercase tracking-widest bg-white/5 border border-white/10 hover:bg-white/10 transition-all"
                    >
                      Validate
                    </button>
                    <button
                      type="button"
                      className="flex-1 rounded py-1 text-[9px] font-bold uppercase tracking-widest bg-white/5 border border-white/10 hover:bg-white/10 transition-all"
                    >
                      Deploy
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SECTION 8: AI Operations Monitor (MLOps) */}
          <div className="glass-panel rounded-2xl p-6">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4 border-b border-white/5 pb-2">
              AI Operations Monitor (MLOps)
            </h2>

            <div className="space-y-4">
              {[
                { label: "Forecast Reliability", val: "94.2%" },
                { label: "Model Agreement Score", val: "96.8%" },
                { label: "Data Quality Score", val: "98.1%" },
                { label: "Sensor Coverage Index", val: "100%" },
              ].map((m, i) => (
                <div key={i} className="flex flex-col gap-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-on-surface-variant">{m.label}</span>
                    <span className="text-on-surface font-bold">{m.val}</span>
                  </div>
                  <div className="relative h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="absolute left-0 top-0 h-full rounded-full bg-primary"
                      style={{ width: m.val }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* SECTION 9: System Event Stream */}
          <div className="glass-panel bg-black/60 rounded-2xl p-6 border border-white/5">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4 font-sans">
              System Event Stream Console
            </h2>

            <div className="h-56 overflow-y-auto font-mono text-[9px] leading-relaxed space-y-2.5 scrollbar-thin scroll-smooth pr-2">
              {consoleLogs.map((log, i) => (
                <div key={i} className="flex gap-2">
                  <span className="text-white/30 shrink-0">{log.time}</span>
                  <span className={cn("font-bold shrink-0",
                    log.level === "INFO" ? "text-primary" : "text-warning"
                  )}>
                    [{log.level}]
                  </span>
                  <span className="text-on-surface">{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* COLUMN 3: Calibrations, Security & AI Core Status */}
        <div className="space-y-6 lg:col-span-1">
          
          {/* SECTION 3: Active Calibration Panel */}
          <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between min-h-[300px]">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant border-b border-white/5 pb-2 mb-4">
                Active Telemetry Calibration
              </h2>

              <div className="flex flex-col items-center justify-center py-4">
                {/* SVG Circular Progress Progress Loader */}
                <div className="relative h-24 w-24">
                  <svg viewBox="0 0 100 100" className="h-full w-full">
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="rgba(255,255,255,0.05)"
                      strokeWidth="6"
                      fill="transparent"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      stroke="#35D6FF"
                      strokeWidth="6"
                      fill="transparent"
                      strokeDasharray="251.2"
                      strokeDashoffset={251.2 - (251.2 * 75) / 100}
                      strokeLinecap="round"
                      transform="rotate(-90 50 50)"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-bold text-on-surface font-sans">75%</span>
                  </div>
                </div>

                <div className="text-center mt-4">
                  <p className="text-xs font-semibold text-on-surface">TNK-09 Optical DO Sensor</p>
                  <p className="text-[10px] text-warning mt-1 animate-pulse">Synchronizing telemetry baseline...</p>
                </div>
              </div>

              <dl className="grid grid-cols-2 gap-y-2 gap-x-4 text-[10px] text-on-surface-variant border-t border-white/5 pt-3">
                <div>
                  <dt className="font-medium">Signal Strength</dt>
                  <dd className="font-bold text-primary">Strong (-44 dBm)</dd>
                </div>
                <div>
                  <dt className="font-medium">Firmware Version</dt>
                  <dd className="font-bold text-on-surface">v2.4.11-alpha</dd>
                </div>
                <div className="col-span-2">
                  <dt className="font-medium">Calibration Started</dt>
                  <dd className="font-bold text-on-surface">2026-06-24 07:15:00 UTC</dd>
                </div>
              </dl>
            </div>

            <button
              type="button"
              className="w-full rounded-full border border-error/20 bg-error/5 py-2 text-center text-xs font-bold text-error transition-colors hover:bg-error/15 mt-6"
            >
              Abort Calibration
            </button>
          </div>

          {/* SECTION 7: Security & Access Control */}
          <div className="glass-panel rounded-2xl p-6">
            <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-4 border-b border-white/5 pb-2">
              Security & Access Control
            </h2>

            <div className="space-y-3 mb-6">
              {[
                { title: "Two Factor Authentication", desc: "Enabled for all biologists & admin roles" },
                { title: "Role Based Access Control", desc: "Active under operational policy v4.2" },
                { title: "Audit Logging Database", desc: "Enabled, writing replicas to secure bucket" },
                { title: "AES-256 Encryption", desc: "Active on all database tables & telemetry streams" },
              ].map((sec, i) => (
                <div key={i} className="flex justify-between items-center text-xs">
                  <div>
                    <h3 className="font-semibold text-on-surface">{sec.title}</h3>
                    <p className="text-[9px] text-on-surface-variant mt-0.5">{sec.desc}</p>
                  </div>
                  <span className="shrink-0 flex items-center justify-center h-4 w-4 rounded-full bg-primary/20 border border-primary/40 text-primary text-[9px] font-bold shadow-[0_0_6px_rgba(71,214,255,0.2)]">
                    ✓
                  </span>
                </div>
              ))}
            </div>

            <button
              type="button"
              className="w-full rounded-full border border-white/10 py-2 text-center text-xs font-semibold text-on-surface hover:bg-white/5"
            >
              View Audit Logs
            </button>
          </div>

          {/* SECTION 10: NEERON AI Core Status */}
          <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between min-h-[300px]">
            <div>
              <div className="flex items-center justify-between border-b border-white/5 pb-2 mb-4">
                <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                  NEERON AI Core Status
                </h2>
                <span className="badge-optimal text-[8px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full shadow-[0_0_6px_rgba(71,214,255,0.2)]">
                  98.7% Health
                </span>
              </div>

              <div className="space-y-3">
                {[
                  "Recommendation Engine",
                  "Disease Prediction Engine",
                  "Forecast Engine",
                  "Case Matching Engine",
                  "Alert Engine",
                ].map((engine, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <span className="font-medium text-on-surface">{engine}</span>
                    <span className="text-[10px] text-primary font-bold flex items-center gap-1">
                      <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary shadow-[0_0_6px_rgba(71,214,255,0.6)] animate-pulse" />
                      Online
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-primary/5 border border-primary/25 rounded-xl p-3.5 text-center mt-6 select-none">
              <span className="text-xs font-bold text-primary uppercase tracking-widest">
                ALL SYSTEMS NOMINAL
              </span>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
