import type { Recommendation } from "@/types";

export const recommendations: Recommendation[] = [
  {
    id: "rec-001",
    tankId: "tank-ld-cage-07",
    zoneId: "zone-loch-duich",
    title: "Reduce feed ration by 8%",
    description:
      "Elevated temperature and declining dissolved oxygen suggest reduced metabolic demand. AI model predicts 8% feed reduction will improve FCR without impacting growth trajectory.",
    category: "feeding",
    priority: "high",
    status: "pending",
    confidence: 0.91,
    estimatedImpact: "FCR improvement of 0.06 over 14 days",
    suggestedAction: "Adjust automatic feeder schedule from 1.8% to 1.65% body weight/day",
    createdAt: "2026-06-22T06:45:00Z",
    expiresAt: "2026-06-23T06:45:00Z",
  },
  {
    id: "rec-002",
    tankId: "tank-ch-cage-05",
    zoneId: "zone-chiloé",
    title: "Initiate sea lice treatment protocol",
    description:
      "Mortality spike and behavioral indicators correlate with elevated sea lice counts. Bath treatment recommended within 48 hours to prevent cohort-wide spread.",
    category: "biosecurity",
    priority: "critical",
    status: "pending",
    confidence: 0.87,
    estimatedImpact: "Reduce projected mortality by 0.4% over 21 days",
    suggestedAction: "Schedule SLICE bath treatment for Cage 05 and adjacent Cage 06",
    createdAt: "2026-06-22T05:30:00Z",
    expiresAt: "2026-06-24T05:30:00Z",
  },
  {
    id: "rec-003",
    tankId: null,
    zoneId: "zone-hardanger",
    title: "Optimize harvest window for Cage 01 cohort",
    description:
      "Growth curve analysis indicates peak condition factor in 18–22 days. Current market prices favor early harvest scheduling to maximize revenue per kg.",
    category: "harvest",
    priority: "medium",
    status: "accepted",
    confidence: 0.84,
    estimatedImpact: "+3.2% revenue per kg vs. standard harvest date",
    suggestedAction: "Reserve harvest vessel slot for July 10–14 window",
    createdAt: "2026-06-21T14:00:00Z",
    expiresAt: "2026-06-28T14:00:00Z",
  },
  {
    id: "rec-004",
    tankId: "tank-br-ras-04",
    zoneId: "zone-ras-bodø",
    title: "Increase photoperiod for smoltification",
    description:
      "Cohort is approaching smoltification window. Extending light period by 2 hours accelerates parr-smolt transformation based on historical RAS performance data.",
    category: "health",
    priority: "medium",
    status: "pending",
    confidence: 0.79,
    estimatedImpact: "Reduce smoltification period by 4–6 days",
    suggestedAction: "Adjust LED lighting schedule to 18L:6D photoperiod",
    createdAt: "2026-06-22T04:00:00Z",
    expiresAt: "2026-06-29T04:00:00Z",
  },
  {
    id: "rec-005",
    tankId: "tank-ld-cage-03",
    zoneId: "zone-loch-duich",
    title: "Pre-emptive oxygen supplementation",
    description:
      "Forecasted low-tide event combined with rising biomass predicts DO dip below 7.5 mg/L. Proactive aeration recommended 6 hours before predicted minimum.",
    category: "water_quality",
    priority: "high",
    status: "pending",
    confidence: 0.93,
    estimatedImpact: "Prevent DO-related stress event affecting ~148k fish",
    suggestedAction: "Activate diffused aeration system at 23:00 UTC June 22",
    createdAt: "2026-06-22T07:00:00Z",
    expiresAt: "2026-06-22T23:00:00Z",
  },
];

export function getRecommendationById(id: string): Recommendation | undefined {
  return recommendations.find((rec) => rec.id === id);
}

export function getPendingRecommendations(): Recommendation[] {
  return recommendations.filter((rec) => rec.status === "pending");
}
