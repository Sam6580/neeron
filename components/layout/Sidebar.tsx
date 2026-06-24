import Link from "next/link";
import {
  APP_NAME,
  APP_TAGLINE,
  FOOTER_NAV_ITEMS,
  NAV_ITEMS,
  SECONDARY_NAV_ITEMS,
} from "@/lib/constants";
import { cn } from "@/lib/utils";
import { NavIcon } from "@/components/ui/NavIcon";

interface SidebarProps {
  activePath?: string;
  className?: string;
}

export function Sidebar({ activePath = "/", className }: SidebarProps) {
  return (
    <aside
      className={cn(
        "flex h-full w-60 shrink-0 flex-col border-r border-white/5 bg-[#060e20]",
        className,
      )}
    >
      <div className="px-6 py-6">
        <h1 className="text-xl font-bold tracking-tight text-primary">{APP_NAME}</h1>
        <p className="mt-0.5 text-xs text-on-surface-variant">{APP_TAGLINE}</p>
      </div>

      <nav className="flex-1 space-y-0.5 px-3">
        {NAV_ITEMS.map((item) => {
          const isActive = activePath === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-on-surface-variant hover:bg-white/5 hover:text-on-surface",
              )}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 h-6 w-0.5 -translate-y-1/2 rounded-full bg-primary shadow-[0_0_8px_rgba(71,214,255,0.6)]" />
              )}
              <NavIcon name={item.icon} className={isActive ? "text-primary" : undefined} />
              {item.label}
            </Link>
          );
        })}

        <div className="my-4 border-t border-white/5" />

        {SECONDARY_NAV_ITEMS.map((item) => {
          const isActive = activePath === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-on-surface-variant hover:bg-white/5 hover:text-on-surface",
              )}
            >
              <NavIcon name={item.icon} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="space-y-3 px-4 pb-4">
        <button
          type="button"
          className="btn-primary-gradient flex w-full items-center justify-center gap-2 rounded-full px-4 py-2.5 text-sm font-semibold text-white transition-all"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.288 15.038a5.25 5.25 0 0 1 7.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M1.924 8.674c5.565-5.565 14.587-5.565 20.152 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 0 1 1.06 0Z" />
          </svg>
          Deploy Sensor
        </button>

        <div className="space-y-0.5">
          {FOOTER_NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-on-surface-variant transition-colors hover:text-on-surface"
            >
              <NavIcon name={item.icon} className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </aside>
  );
}
