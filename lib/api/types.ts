// TypeScript shapes mirroring the backend API v1 response schemas.

export interface PaginationMeta {
  currentPage: number;
  totalPages: number;
  limit: number;
  totalCount: number;
}

export interface Paginated<T> {
  success: boolean;
  timestamp?: string;
  data: T[];
  pagination: PaginationMeta;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role_name: string;
  permissions: Record<string, boolean>;
}

export interface TankResponse {
  id: string;
  name: string;
  type: string;
  volumeM3: number;
  maxBiomassKg: number;
  species: string;
  currentBiomassKg: number;
  healthStatus: string;
}

export interface TankHealthResponse {
  tank_id: string;
  psi_score: number | null;
  stress_level: string;
  psi_generated_at: string | null;
  stability: { temperature: string; dissolved_oxygen: string; ph: string };
  averages_7d: {
    temperature: number | null;
    dissolved_oxygen: number | null;
    ph: number | null;
  } | null;
}

export interface AlertResponse {
  id: string;
  time: string;
  tank_id: string;
  sensor_id?: string | null;
  type: string;
  severity: string;
  status: string;
  message: string;
}

// ---- Dashboard composite (matches backend /ui/dashboard payload) ----
import type { AnalyticsMetric } from "@/types";
import type { ZoneOverview } from "@/data/dashboard";

export type EnvironmentalMetric = AnalyticsMetric & { sparkline: number[] };

export interface DashboardData {
  farmHealthScore: { score: number; trendPercent: number };
  environmentalMetrics: EnvironmentalMetric[];
  zoneOverviews: ZoneOverview[];
  farmHealthOperational: {
    psiAverage: number;
    riskLevel: string;
    lastUpdatedMinutesAgo: number;
  };
  mortalityRisk: { value: number; unit: string; classification: string; description: string };
  psiAverage: { value: number; label: string; description: string };
  riskTrend: { direction: "up" | "down" | "stable"; label: string; description: string };
  historicalCaseMatch: {
    scenarioId: string;
    similarity: number;
    expectedRecoveryHours: number;
    outcomeConfidence: number;
    summary: string;
    recommendedActions: string[];
  };
}
