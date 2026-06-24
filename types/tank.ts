export type TankStatus = "healthy" | "warning" | "critical" | "offline" | "maintenance";

export type TankType = "sea_cage" | "ras" | "smolt" | "broodstock";

export interface WaterQualityReading {
  timestamp: string;
  dissolvedOxygenMgL: number;
  temperatureC: number;
  salinityPpt: number;
  ph: number;
  ammoniaMgL: number;
  nitriteMgL: number;
  turbidityNtu: number;
}

export interface Tank {
  id: string;
  name: string;
  zoneId: string;
  type: TankType;
  status: TankStatus;
  species: "Atlantic Salmon";
  cohortId: string;
  fishCount: number;
  avgWeightKg: number;
  stockingDensityKgM3: number;
  healthScore: number;
  fcr: number;
  mortalityRatePercent: number;
  daysInProduction: number;
  lastFedAt: string;
  lastReading: WaterQualityReading;
}
