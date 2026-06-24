import type { Recommendation } from "@/types";
import { formatRelativeTime } from "@/lib";
import { cn } from "@/lib/utils";

interface RecommendationCardProps {
  recommendation: Recommendation;
  onAccept?: (id: string) => void;
  onDismiss?: (id: string) => void;
  variant?: "default" | "glass" | "compact";
  className?: string;
}

const priorityLabels: Record<Recommendation["priority"], string> = {
  low: "Low Priority",
  medium: "Medium Priority",
  high: "High Priority",
  critical: "High Priority",
};

export function RecommendationCard({
  recommendation,
  onAccept,
  onDismiss,
  variant = "glass",
  className,
}: RecommendationCardProps) {
  const confidencePercent = Math.round(recommendation.confidence * 100);
  const isPending = recommendation.status === "pending";

  if (variant === "compact") {
    return (
      <article
        className={cn(
          "rounded-2xl border border-white/5 bg-white/[0.03] p-4 transition-all hover:border-primary/20",
          className,
        )}
      >
        <div className="flex items-center justify-between gap-2">
          <p className="text-xs font-semibold text-primary">
            {confidencePercent}% Confidence
          </p>
          <span className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
            {priorityLabels[recommendation.priority]}
          </span>
        </div>
        <h3 className="mt-2 text-sm font-semibold text-on-surface">
          {recommendation.title}
        </h3>
        <p className="mt-1.5 text-xs leading-relaxed text-on-surface-variant">
          {recommendation.description}
        </p>

        {isPending && (
          <div className="mt-4 flex gap-2">
            <button
              type="button"
              onClick={() => onAccept?.(recommendation.id)}
              className="flex-1 rounded-full bg-primary/20 py-2 text-xs font-semibold text-primary transition-colors hover:bg-primary/30"
            >
              Accept
            </button>
            <button
              type="button"
              onClick={() => onDismiss?.(recommendation.id)}
              className="flex-1 rounded-full border border-white/10 py-2 text-xs font-semibold text-on-surface-variant transition-colors hover:border-white/20 hover:bg-white/5 hover:text-on-surface"
            >
              Dismiss
            </button>
          </div>
        )}
      </article>
    );
  }

  return (
    <article
      className={cn(
        "rounded-2xl p-5 transition-all",
        variant === "glass"
          ? "glass-panel hover:border-primary/20"
          : "border border-slate-200 bg-white shadow-sm",
        className,
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1 rounded-full bg-primary/15 px-2.5 py-0.5 text-xs font-semibold text-primary">
          AI Insight · {confidencePercent}%
        </span>
        <span className="text-xs capitalize text-on-surface-variant">
          {recommendation.priority} priority
        </span>
      </div>

      <h3 className="mt-3 text-sm font-semibold text-on-surface">
        {recommendation.title}
      </h3>
      <p className="mt-1.5 text-sm leading-relaxed text-on-surface-variant">
        {recommendation.description}
      </p>

      <div className="mt-4 rounded-xl border border-primary/20 bg-primary/5 p-3">
        <p className="text-xs font-semibold uppercase tracking-widest text-primary">
          Suggested Action
        </p>
        <p className="mt-1 text-sm text-on-surface">{recommendation.suggestedAction}</p>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
        <time className="text-xs text-on-surface-variant" dateTime={recommendation.createdAt}>
          {formatRelativeTime(recommendation.createdAt)}
        </time>

        {isPending && (onAccept || onDismiss) && (
          <div className="flex gap-2">
            {onDismiss && (
              <button
                type="button"
                onClick={() => onDismiss(recommendation.id)}
                className="rounded-full px-3 py-1.5 text-xs font-medium text-on-surface-variant hover:bg-white/5"
              >
                Dismiss
              </button>
            )}
            {onAccept && (
              <button
                type="button"
                onClick={() => onAccept(recommendation.id)}
                className="rounded-full bg-primary/20 px-3 py-1.5 text-xs font-semibold text-primary hover:bg-primary/30"
              >
                Accept
              </button>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
