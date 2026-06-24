export type ZoneType = "sea_site" | "land_facility" | "hatchery" | "processing";

export type ZoneStatus = "operational" | "degraded" | "offline" | "restricted";

export interface Zone {
  id: string;
  name: string;
  code: string;
  type: ZoneType;
  status: ZoneStatus;
  location: string;
  region: string;
  latitude: number;
  longitude: number;
  tankCount: number;
  totalBiomassKg: number;
  avgHealthScore: number;
  manager: string;
}
