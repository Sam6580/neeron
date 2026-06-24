import {
  clamp,
  formatNumber,
  getHealthScoreStatus,
} from "@/lib";
import { cn } from "@/lib/utils";

interface HealthScoreBreakdown {
  label: string;
  score: number;
}

interface FarmHealthOperationalMeta {
  psiAverage: number;
  riskLevel: string;
  lastUpdatedMinutesAgo: number;
}

interface HealthScoreCardProps {
  score: number;
  label?: string;
  trendPercent?: number;
  operationalMeta?: FarmHealthOperationalMeta;
  breakdown?: HealthScoreBreakdown[];
  variant?: "default" | "glass" | "hero";
  className?: string;
}

function ScoreRing({
  score,
  size = "default",
}: {
  score: number;
  size?: "default" | "large";
}) {
  const status = getHealthScoreStatus(score);
  const radius = size === "large" ? 52 : 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamp(score, 0, 100) / 100) * circumference;
  const dim = size === "large" ? 140 : 112;

  const strokeColor =
    status === "good"
      ? "stroke-primary"
      : status === "warning"
        ? "stroke-warning"
        : "stroke-error";

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: dim, height: dim }}
    >
      <svg
        className="-rotate-90"
        style={{ width: dim, height: dim }}
        viewBox="0 0 120 120"
      >
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          strokeWidth="8"
          className="stroke-white/10"
        />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={cn("transition-all duration-500", strokeColor)}
          style={{ filter: "drop-shadow(0 0 6px rgba(71,214,255,0.4))" }}
        />
      </svg>
      <div className="absolute text-center">
        <p
          className={cn(
            "font-bold text-on-surface",
            size === "large" ? "text-4xl" : "text-3xl",
          )}
        >
          {Math.round(score)}
        </p>
      </div>
    </div>
  );
}

export function HealthScoreCard({
  score,
  label = "Fleet Health Score",
  trendPercent,
  operationalMeta,
  breakdown = [],
  variant = "glass",
  className,
}: HealthScoreCardProps) {
  if (variant === "hero") {
    return (
      <article
        className={cn(
          "glass-panel-glow col-span-full flex flex-col justify-between rounded-2xl p-6 lg:col-span-2 lg:flex-row lg:items-center lg:p-8",
          className,
        )}
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">
            Global Health Status
          </p>
          <div className="mt-3 flex flex-wrap items-end gap-3">
            <h2 className="text-2xl font-semibold text-on-surface md:text-3xl">
              Farm Health Score{" "}
              <span className="text-primary">{formatNumber(score, 1)}%</span>
            </h2>
            {trendPercent !== undefined && (
              <span className="inline-flex items-center gap-1 rounded-full bg-primary/15 px-2.5 py-1 text-xs font-semibold text-primary">
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
                </svg>
                +{formatNumber(trendPercent, 1)}%
              </span>
            )}
          </div>

          {operationalMeta && (
            <dl className="mt-4 flex flex-wrap gap-x-6 gap-y-2 border-t border-white/5 pt-4">
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                  PSI Average
                </dt>
                <dd className="mt-0.5 text-sm font-semibold text-on-surface">
                  {formatNumber(operationalMeta.psiAverage, 1)}
                </dd>
              </div>
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                  Risk Level
                </dt>
                <dd className="mt-0.5 text-sm font-semibold text-warning">
                  {operationalMeta.riskLevel}
                </dd>
              </div>
              <div>
                <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
                  Last Updated
                </dt>
                <dd className="mt-0.5 text-sm font-semibold text-on-surface">
                  {operationalMeta.lastUpdatedMinutesAgo} min ago
                </dd>
              </div>
            </dl>
          )}
        </div>
        <ScoreRing score={score} size="large" />
      </article>
    );
  }

  return (
    <article
      className={cn(
        "rounded-2xl p-5",
        variant === "glass" ? "glass-panel" : "border border-slate-200 bg-white shadow-sm",
        className,
      )}
    >
      <h3 className="text-sm font-medium text-on-surface-variant">{label}</h3>
      <div className="mt-4 flex items-center gap-6">
        <ScoreRing score={score} />
        {breakdown.length > 0 && (
          <ul className="flex-1 space-y-3">
            {breakdown.map((item) => (
              <li key={item.label}>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-on-surface-variant">{item.label}</span>
                  <span className="font-medium text-on-surface">{item.score}</span>
                </div>
                <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/10">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all",
                      getHealthScoreStatus(item.score) === "good" && "bg-primary",
                      getHealthScoreStatus(item.score) === "warning" && "bg-warning",
                      getHealthScoreStatus(item.score) === "critical" && "bg-error",
                    )}
                    style={{ width: `${clamp(item.score, 0, 100)}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}
