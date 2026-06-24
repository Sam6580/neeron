export type RecommendationPriority = "low" | "medium" | "high" | "critical";

export type RecommendationStatus = "pending" | "accepted" | "dismissed" | "completed";

export type RecommendationCategory =
  | "feeding"
  | "water_quality"
  | "health"
  | "biosecurity"
  | "harvest"
  | "maintenance";

export interface Recommendation {
  id: string;
  tankId: string | null;
  zoneId: string | null;
  title: string;
  description: string;
  category: RecommendationCategory;
  priority: RecommendationPriority;
  status: RecommendationStatus;
  confidence: number;
  estimatedImpact: string;
  suggestedAction: string;
  createdAt: string;
  expiresAt: string | null;
}
