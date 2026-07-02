import { Link, useRouterState } from "@tanstack/react-router";
import type { ReactNode } from "react";

const nav = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/jd-analysis", label: "Job Descriptions" },
  { to: "/candidates", label: "Candidates" },
  { to: "/analytics", label: "AI Analysis" },
  { to: "/prediction", label: "Predictions" },
  { to: "/interview", label: "Interview" },
] as const;

export function AppLayout({ children, title, subtitle, actions }: {
  children: ReactNode; title?: string; subtitle?: ReactNode; actions?: ReactNode;
}) {
  const pathname = useRouterState({ select: s => s.location.pathname });

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top bar */}
      <header className="sticky top-0 z-30 border-b border-border bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="font-semibold text-lg tracking-tight">
              RecruiterMind
            </Link>
            <nav className="hidden md:flex items-center gap-1">
              {nav.map(n => {
                const active = pathname === n.to || pathname.startsWith(n.to);
                return (
                  <Link
                    key={n.to}
                    to={n.to}
                    className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                      active
                        ? "bg-secondary text-foreground font-medium"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {n.label}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      </header>

      {/* Page header */}
      {(title || actions) && (
        <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 pt-8 pb-4 flex items-end justify-between gap-4 flex-wrap">
          <div className="min-w-0">
            {title && <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>}
            {subtitle && <p className="text-muted-foreground mt-1 text-sm">{subtitle}</p>}
          </div>
          {actions}
        </div>
      )}

      {/* Main */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 pb-12">
        <div className="animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}