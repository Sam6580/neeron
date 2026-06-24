import type { BiosecurityRecord } from "@/types";

export const biosecurityRecords: BiosecurityRecord[] = [
  {
    id: "bio-001",
    zoneId: "zone-chiloé",
    tankId: "tank-ch-cage-05",
    eventType: "pathogen_detection",
    riskLevel: "high",
    title: "Elevated Caligus rogercresseyi counts",
    description:
      "Weekly sea lice survey recorded average of 8.2 adult female lice per fish on Cage 05, exceeding the 6.0 treatment trigger threshold for Chilean Atlantic Salmon operations.",
    pathogen: "Caligus rogercresseyi (Sea Lice)",
    treatmentApplied: null,
    recordedBy: "Dr. Ana Torres",
    recordedAt: "2026-06-21T16:00:00Z",
    followUpRequired: true,
    followUpDate: "2026-06-24T16:00:00Z",
  },
  {
    id: "bio-002",
    zoneId: "zone-loch-duich",
    tankId: "tank-ld-cage-07",
    eventType: "inspection",
    riskLevel: "moderate",
    title: "Routine gill health assessment",
    description:
      "Sample of 30 fish showed mild gill score 1–2 changes consistent with seasonal amoebic gill disease (AGD) risk. No treatment required at this stage.",
    pathogen: "Neoparamoeba perurans (AGD)",
    treatmentApplied: null,
    recordedBy: "Dr. James Reid",
    recordedAt: "2026-06-20T10:30:00Z",
    followUpRequired: true,
    followUpDate: "2026-06-27T10:30:00Z",
  },
  {
    id: "bio-003",
    zoneId: "zone-ras-bodø",
    tankId: "tank-br-ras-04",
    eventType: "vaccination",
    riskLevel: "low",
    title: "IPN/PD combined vaccination completed",
    description:
      "Full cohort vaccinated against Infectious Pancreatic Necrosis (IPN) and Pancreas Disease (PD) via intraperitoneal injection. 99.2% coverage achieved.",
    pathogen: null,
    treatmentApplied: "AquaVac PD7 + IPN vaccine",
    recordedBy: "Ingrid Larsen",
    recordedAt: "2026-06-18T08:00:00Z",
    followUpRequired: false,
    followUpDate: null,
  },
  {
    id: "bio-004",
    zoneId: "zone-hardanger",
    tankId: null,
    eventType: "equipment_sanitization",
    riskLevel: "low",
    title: "Wellboat disinfection protocol",
    description:
      "Harvest vessel NorHarvest VII completed full disinfection cycle per NS 9416 standard prior to smolt transfer operations.",
    pathogen: null,
    treatmentApplied: "Quaternary ammonium compound bath — 200 ppm, 30 min",
    recordedBy: "Erik Johansen",
    recordedAt: "2026-06-19T14:00:00Z",
    followUpRequired: false,
    followUpDate: null,
  },
  {
    id: "bio-005",
    zoneId: "zone-chiloé",
    tankId: "tank-ch-cage-05",
    eventType: "treatment",
    riskLevel: "moderate",
    title: "Emergency bath treatment — Azamethiphos",
    description:
      "Bath treatment applied to Cage 05 following sea lice count escalation. Fish monitored for 48 hours post-treatment with no adverse behavioral response observed.",
    pathogen: "Caligus rogercresseyi (Sea Lice)",
    treatmentApplied: "Azamethiphos 0.15 mg/L, 60-minute bath",
    recordedBy: "Carlos Mendez",
    recordedAt: "2026-06-15T20:00:00Z",
    followUpRequired: true,
    followUpDate: "2026-06-22T20:00:00Z",
  },
  {
    id: "bio-006",
    zoneId: "zone-loch-duich",
    tankId: null,
    eventType: "quarantine",
    riskLevel: "critical",
    title: "Incoming smolt batch quarantine hold",
    description:
      "Spring smolt delivery from external hatchery held in quarantine RAS for mandatory 21-day observation period. PCR screening for ISA and SAV negative.",
    pathogen: null,
    treatmentApplied: null,
    recordedBy: "Fiona MacLeod",
    recordedAt: "2026-06-10T09:00:00Z",
    followUpRequired: true,
    followUpDate: "2026-07-01T09:00:00Z",
  },
];

export function getBiosecurityRecordById(
  id: string,
): BiosecurityRecord | undefined {
  return biosecurityRecords.find((record) => record.id === id);
}

export function getHighRiskRecords(): BiosecurityRecord[] {
  return biosecurityRecords.filter(
    (record) =>
      record.riskLevel === "high" || record.riskLevel === "critical",
  );
}
