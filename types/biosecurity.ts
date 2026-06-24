export type BiosecurityEventType =
  | "inspection"
  | "treatment"
  | "mortality_event"
  | "pathogen_detection"
  | "quarantine"
  | "vaccination"
  | "equipment_sanitization";

export type BiosecurityRiskLevel = "low" | "moderate" | "high" | "critical";

export interface BiosecurityRecord {
  id: string;
  zoneId: string;
  tankId: string | null;
  eventType: BiosecurityEventType;
  riskLevel: BiosecurityRiskLevel;
  title: string;
  description: string;
  pathogen: string | null;
  treatmentApplied: string | null;
  recordedBy: string;
  recordedAt: string;
  followUpRequired: boolean;
  followUpDate: string | null;
}
