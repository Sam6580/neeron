import { cn } from "@/lib/utils";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { RequireAuth } from "@/components/auth/RequireAuth";

interface AppShellProps {
  children: React.ReactNode;
  activePath?: string;
  title?: string;
  alertCount?: number;
  className?: string;
}

export function AppShell({
  children,
  activePath = "/",
  title,
  alertCount,
  className,
}: AppShellProps) {
  return (
    <RequireAuth>
      <div className={cn("flex h-screen overflow-hidden bg-background", className)}>
        <Sidebar activePath={activePath} />
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <Topbar title={title} alertCount={alertCount} />
          <main className="scrollbar-thin flex-1 overflow-y-auto p-4 md:p-6">
            {children}
          </main>
        </div>
      </div>
    </RequireAuth>
  );
}
