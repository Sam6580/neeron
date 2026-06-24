"use client";

import { useState } from "react";
import type { Recommendation } from "@/types";
import { RecommendationCard } from "@/components/recommendations/RecommendationCard";

interface DashboardRecommendationsProps {
  recommendations: Recommendation[];
}

export function DashboardRecommendations({
  recommendations,
}: DashboardRecommendationsProps) {
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const [acceptedIds, setAcceptedIds] = useState<Set<string>>(new Set());

  const visible = recommendations.filter(
    (rec) => !dismissedIds.has(rec.id) && !acceptedIds.has(rec.id),
  );

  function handleAccept(id: string) {
    setAcceptedIds((prev) => new Set(prev).add(id));
  }

  function handleDismiss(id: string) {
    setDismissedIds((prev) => new Set(prev).add(id));
  }

  if (visible.length === 0) {
    return (
      <p className="rounded-2xl border border-white/5 bg-white/[0.03] px-4 py-6 text-center text-xs text-on-surface-variant">
        All pending recommendations have been actioned.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {visible.slice(0, 2).map((rec) => (
        <RecommendationCard
          key={rec.id}
          recommendation={rec}
          variant="compact"
          onAccept={handleAccept}
          onDismiss={handleDismiss}
        />
      ))}
    </div>
  );
}
