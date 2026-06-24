"use client";

import { useMemo, useState } from "react";
import type { Tank } from "@/types";
import type { TankRiskLevel } from "@/lib";
import { TankCard } from "./TankCard";
import { cn } from "@/lib/utils";
import { getTankRiskLevel } from "@/lib/tank-metrics";

interface TankWithZone {
  tank: Tank;
  zoneName: string;
  zoneCode: string;
}

interface TankManagementGridProps {
  tanks: TankWithZone[];
}

const SPECIES_FILTERS = ["All Species", "Atlantic Salmon"] as const;

const RISK_FILTERS: { label: string; value: "all" | TankRiskLevel }[] = [
  { label: "All Risk", value: "all" },
  { label: "Low Risk", value: "low" },
  { label: "Moderate", value: "moderate" },
  { label: "High Risk", value: "high" },
  { label: "Critical", value: "critical" },
];

export function TankManagementGrid({ tanks }: TankManagementGridProps) {
  const [search, setSearch] = useState("");
  const [speciesFilter, setSpeciesFilter] = useState<string>("All Species");
  const [riskFilter, setRiskFilter] = useState<"all" | TankRiskLevel>("all");

  const filteredTanks = useMemo(() => {
    const query = search.trim().toLowerCase();

    return tanks.filter(({ tank, zoneName, zoneCode }) => {
      if (speciesFilter !== "All Species" && tank.species !== speciesFilter) {
        return false;
      }

      if (riskFilter !== "all" && getTankRiskLevel(tank) !== riskFilter) {
        return false;
      }

      if (!query) return true;

      return (
        tank.id.toLowerCase().includes(query) ||
        tank.name.toLowerCase().includes(query) ||
        tank.species.toLowerCase().includes(query) ||
        zoneName.toLowerCase().includes(query) ||
        zoneCode.toLowerCase().includes(query) ||
        tank.cohortId.toLowerCase().includes(query)
      );
    });
  }, [tanks, search, speciesFilter, riskFilter]);

  const activeCount = tanks.filter(
    (t) => t.tank.status !== "maintenance" && t.tank.status !== "offline",
  ).length;
  const atRiskCount = tanks.filter((t) => {
    const risk = getTankRiskLevel(t.tank);
    return risk === "high" || risk === "critical";
  }).length;

  return (
    <div className="space-y-6">
      {/* Filter bar */}
      <div className="glass-panel rounded-2xl p-4 md:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative min-w-0 flex-1 lg:max-w-md">
            <svg
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-on-surface-variant"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search tanks, zones, cohorts..."
              aria-label="Search tanks"
              className="h-10 w-full rounded-full border border-white/10 bg-white/5 pl-9 pr-4 text-sm text-on-surface placeholder:text-on-surface-variant focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {SPECIES_FILTERS.map((species) => (
              <button
                key={species}
                type="button"
                onClick={() => setSpeciesFilter(species)}
                className={cn(
                  "rounded-full px-3 py-1.5 text-xs font-medium transition-all",
                  speciesFilter === species
                    ? "bg-primary/15 text-primary border border-primary/30"
                    : "border border-white/10 text-on-surface-variant hover:border-white/20 hover:text-on-surface",
                )}
              >
                {species}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-white/5 pt-4">
          <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
            Risk Level
          </span>
          {RISK_FILTERS.map(({ label, value }) => (
            <button
              key={value}
              type="button"
              onClick={() => setRiskFilter(value)}
              className={cn(
                "rounded-full px-3 py-1.5 text-xs font-medium transition-all",
                riskFilter === value
                  ? "bg-primary/15 text-primary border border-primary/30"
                  : "border border-white/10 text-on-surface-variant hover:border-white/20 hover:text-on-surface",
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary stats */}
      <div className="flex flex-wrap gap-4 text-sm">
        <p className="text-on-surface-variant">
          <span className="font-semibold text-on-surface">{filteredTanks.length}</span>{" "}
          of {tanks.length} tanks shown
        </p>
        <p className="text-on-surface-variant">
          <span className="font-semibold text-primary">{activeCount}</span> active
        </p>
        <p className="text-on-surface-variant">
          <span className="font-semibold text-error">{atRiskCount}</span> at elevated risk
        </p>
      </div>

      {/* Tank grid */}
      {filteredTanks.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filteredTanks.map(({ tank, zoneName, zoneCode }) => (
            <TankCard
              key={tank.id}
              tank={tank}
              zoneName={zoneName}
              zoneCode={zoneCode}
            />
          ))}
        </div>
      ) : (
        <div className="glass-panel rounded-2xl px-6 py-12 text-center">
          <p className="text-sm font-medium text-on-surface">No tanks match your filters</p>
          <p className="mt-1 text-xs text-on-surface-variant">
            Adjust search terms or risk filters to view active production units.
          </p>
        </div>
      )}
    </div>
  );
}
