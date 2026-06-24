import { historicalCaseMatch } from "@/data/dashboard";
import { cn } from "@/lib/utils";

interface HistoricalCaseMatchProps {
  className?: string;
}

export function HistoricalCaseMatch({ className }: HistoricalCaseMatchProps) {
  const {
    scenarioId,
    similarity,
    expectedRecoveryHours,
    outcomeConfidence,
    summary,
    recommendedActions,
  } = historicalCaseMatch;

  return (
    <section className={cn("glass-panel rounded-2xl p-5", className)}>
      <div className="flex items-center gap-2">
        <svg className="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.348 14.652a3.75 3.75 0 0 1 0-5.304m5.304 0a3.75 3.75 0 0 1 0 5.304m-7.425 2.121a6.75 6.75 0 0 1 0-9.546m9.546 0a6.75 6.75 0 0 1 0 9.546M5.106 18.894c-3.808-3.808-3.808-9.98 0-13.788m13.788 0c3.808 3.808 3.808 9.98 0 13.788M12 12h.008v.008H12V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
        </svg>
        <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
          Historical Case Match
        </h2>
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-on-surface">
          Scenario #{scenarioId}
        </h3>
        <span className="rounded-full bg-primary/15 px-2.5 py-0.5 text-xs font-semibold text-primary">
          {similarity}% Similarity
        </span>
      </div>

      <p className="mt-3 text-xs leading-relaxed text-on-surface-variant">
        {summary}
      </p>

      <dl className="mt-4 grid grid-cols-2 gap-3 rounded-xl bg-white/5 p-3">
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
            Expected Recovery
          </dt>
          <dd className="mt-1 text-sm font-semibold text-on-surface">
            {expectedRecoveryHours} hours
          </dd>
        </div>
        <div>
          <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
            Outcome Confidence
          </dt>
          <dd className="mt-1 text-sm font-semibold text-primary">
            {outcomeConfidence}%
          </dd>
        </div>
      </dl>

      <div className="mt-4">
        <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Recommended Actions
        </p>
        <ul className="mt-2 space-y-1.5">
          {recommendedActions.map((action) => (
            <li
              key={action}
              className="flex items-start gap-2 text-xs text-on-surface-variant"
            >
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary" />
              {action}
            </li>
          ))}
        </ul>
      </div>

      <button
        type="button"
        className="mt-4 text-[10px] font-bold uppercase tracking-widest text-primary transition-colors hover:text-primary-bright"
      >
        View Case Logs
      </button>
    </section>
  );
}
