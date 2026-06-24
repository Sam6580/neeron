import type { AnalyticsMetric } from "@/types";
import { Sparkline } from "@/components/charts/Sparkline";
import {
  formatCompact,
  formatNumber,
  getTrendColor,
} from "@/lib";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  metric: AnalyticsMetric;
  sparkline?: number[];
  variant?: "default" | "glass" | "compact";
  className?: string;
}

const invertTrendCategories: AnalyticsMetric["category"][] = [
  "mortality",
  "feed",
  "water_quality",
];

function TrendIndicator({
  trend,
  percent,
  category,
  dark = true,
}: {
  trend: AnalyticsMetric["trend"];
  percent: number;
  category: AnalyticsMetric["category"];
  dark?: boolean;
}) {
  const invert = invertTrendCategories.includes(category);
  const color = getTrendColor(trend, invert);

  if (trend === "stable") {
    return (
      <span className={cn("inline-flex items-center gap-1 text-xs font-medium", dark ? "text-on-surface-variant" : color)}>
        Stable
      </span>
    );
  }

  const isUp = trend === "up";
  return (
    <span className={cn("inline-flex items-center gap-1 text-xs font-medium", dark ? color : color)}>
      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d={isUp ? "M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" : "M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3"}
        />
      </svg>
      {formatNumber(percent, 1)}%
    </span>
  );
}

export function MetricCard({
  metric,
  sparkline,
  variant = "glass",
  className,
}: MetricCardProps) {
  const displayValue =
    metric.value >= 10_000
      ? formatCompact(metric.value)
      : formatNumber(
          metric.value,
          metric.unit === "" || metric.unit === "ppm" ? 2 : 1,
        );

  if (variant === "compact") {
    return (
      <article
        className={cn(
          "glass-panel flex flex-col rounded-2xl p-4 transition-all hover:border-primary/20",
          className,
        )}
      >
        <div className="mb-3 flex items-start justify-between">
          <p className="text-xs font-medium text-on-surface-variant">
            {metric.label}
          </p>
          {sparkline && <Sparkline data={sparkline} />}
        </div>
        <p className="text-xl font-semibold tracking-tight text-on-surface">
          {displayValue}
          {metric.unit && (
            <span className="ml-1 text-sm font-normal text-on-surface-variant">
              {metric.unit === "°C" ? "°C" : metric.unit === "" ? "" : ` ${metric.unit}`}
            </span>
          )}
        </p>
      </article>
    );
  }

  return (
    <article
      className={cn(
        "rounded-2xl p-5 transition-all",
        variant === "glass"
          ? "glass-panel hover:border-primary/20"
          : "border border-slate-200 bg-white shadow-sm hover:shadow-md",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p
            className={cn(
              "text-sm font-medium",
              variant === "glass" ? "text-on-surface-variant" : "text-slate-500",
            )}
          >
            {metric.label}
          </p>
          <p
            className={cn(
              "mt-1 text-2xl font-semibold tracking-tight",
              variant === "glass" ? "text-on-surface" : "text-slate-900",
            )}
          >
            {displayValue}
            {metric.unit && (
              <span
                className={cn(
                  "ml-1 text-base font-normal",
                  variant === "glass" ? "text-on-surface-variant" : "text-slate-500",
                )}
              >
                {metric.unit}
              </span>
            )}
          </p>
        </div>
        {sparkline && <Sparkline data={sparkline} />}
      </div>

      <div
        className={cn(
          "mt-4 flex items-center justify-between border-t pt-3",
          variant === "glass" ? "border-white/5" : "border-slate-100",
        )}
      >
        <TrendIndicator
          trend={metric.trend}
          percent={metric.trendPercent}
          category={metric.category}
          dark={variant === "glass"}
        />
        <span
          className={cn(
            "text-xs",
            variant === "glass" ? "text-on-surface-variant" : "text-slate-400",
          )}
        >
          {metric.period}
        </span>
      </div>
    </article>
  );
}

export function SummaryStatCard({
  label,
  value,
  subValue,
  trend,
  valueClassName,
  className,
}: {
  label: string;
  value: string;
  subValue?: React.ReactNode;
  trend?: "up" | "down";
  valueClassName?: string;
  className?: string;
}) {
  return (
    <article
      className={cn(
        "glass-panel flex flex-col justify-center rounded-2xl p-6",
        className,
      )}
    >
      <p className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant">
        {label}
      </p>
      <div className="mt-2 flex items-center gap-2">
        <p className={cn("text-2xl font-semibold", valueClassName ?? "text-on-surface")}>
          {value}
        </p>
        {trend === "down" && (
          <svg className="h-5 w-5 text-error" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
          </svg>
        )}
        {trend === "up" && (
          <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" />
          </svg>
        )}
      </div>
      {subValue && <div className="mt-1">{subValue}</div>}
    </article>
  );
}
