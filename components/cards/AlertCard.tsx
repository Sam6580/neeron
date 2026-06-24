import type { Alert } from "@/types";
import {
  formatRelativeTime,
  getAlertSeverityLabel,
} from "@/lib";
import { cn } from "@/lib/utils";

interface AlertCardProps {
  alert: Alert;
  zoneCode?: string;
  onAcknowledge?: (id: string) => void;
  variant?: "default" | "glass" | "compact";
  className?: string;
}

const severityIconColor: Record<Alert["severity"], string> = {
  critical: "text-error bg-error/15 border-error/30",
  warning: "text-warning bg-warning/15 border-warning/30",
  info: "text-tertiary bg-tertiary/15 border-tertiary/30",
};

export function AlertCard({
  alert,
  zoneCode,
  onAcknowledge,
  variant = "glass",
  className,
}: AlertCardProps) {
  if (variant === "compact") {
    return (
      <article
        className={cn(
          "flex items-start gap-3 rounded-xl border border-white/5 bg-white/[0.03] p-3 transition-colors hover:border-white/10",
          className,
        )}
      >
        <div
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border",
            severityIconColor[alert.severity],
          )}
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-on-surface">{alert.title}</h3>
          <p className="mt-0.5 truncate text-xs text-on-surface-variant">
            {alert.currentValue
              ? `${alert.metric}: ${alert.currentValue}`
              : alert.message}
          </p>
          <dl className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[10px]">
            <div className="flex gap-1">
              <dt className="font-semibold uppercase tracking-widest text-on-surface-variant">
                Priority:
              </dt>
              <dd
                className={cn(
                  "font-semibold uppercase",
                  alert.severity === "critical" && "text-error",
                  alert.severity === "warning" && "text-warning",
                  alert.severity === "info" && "text-tertiary",
                )}
              >
                {getAlertSeverityLabel(alert.severity)}
              </dd>
            </div>
            {zoneCode && (
              <div className="flex gap-1">
                <dt className="font-semibold uppercase tracking-widest text-on-surface-variant">
                  Affected Zone:
                </dt>
                <dd className="font-semibold text-on-surface">{zoneCode}</dd>
              </div>
            )}
          </dl>
        </div>
      </article>
    );
  }

  return (
    <article
      className={cn(
        "rounded-2xl p-5 transition-all",
        variant === "glass"
          ? "glass-panel hover:border-primary/20"
          : "border bg-white shadow-sm",
        alert.severity === "critical" && variant !== "glass" && "border-red-200",
        alert.severity === "warning" && variant !== "glass" && "border-amber-200",
        className,
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={cn(
            "inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide",
            severityIconColor[alert.severity],
          )}
        >
          {getAlertSeverityLabel(alert.severity)}
        </span>
        <span className="text-xs capitalize text-on-surface-variant">
          {alert.category.replace("_", " ")}
        </span>
        {zoneCode && (
          <span className="text-xs text-on-surface-variant">· {zoneCode}</span>
        )}
      </div>

      <h3 className="mt-2 text-sm font-semibold text-on-surface">{alert.title}</h3>
      <p className="mt-1 text-sm leading-relaxed text-on-surface-variant">
        {alert.message}
      </p>

      {(alert.metric || alert.currentValue) && (
        <dl className="mt-4 grid grid-cols-3 gap-3 rounded-xl bg-white/5 p-3 text-xs">
          {alert.metric && (
            <div>
              <dt className="text-on-surface-variant">Metric</dt>
              <dd className="mt-0.5 font-medium text-on-surface">{alert.metric}</dd>
            </div>
          )}
          {alert.currentValue && (
            <div>
              <dt className="text-on-surface-variant">Current</dt>
              <dd className="mt-0.5 font-medium text-on-surface">{alert.currentValue}</dd>
            </div>
          )}
          {alert.threshold && (
            <div>
              <dt className="text-on-surface-variant">Threshold</dt>
              <dd className="mt-0.5 font-medium text-on-surface">{alert.threshold}</dd>
            </div>
          )}
        </dl>
      )}

      <div className="mt-4 flex items-center justify-between">
        <time className="text-xs text-on-surface-variant" dateTime={alert.triggeredAt}>
          {formatRelativeTime(alert.triggeredAt)}
        </time>
        {alert.status === "active" && onAcknowledge && (
          <button
            type="button"
            onClick={() => onAcknowledge(alert.id)}
            className="rounded-full px-3 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/10"
          >
            Acknowledge
          </button>
        )}
      </div>
    </article>
  );
}
