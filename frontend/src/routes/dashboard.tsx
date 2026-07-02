import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppLayout } from "@/components/app-layout";
import { listCandidates, healthCheck, listJobDescriptions } from "@/lib/api/client";
import type { CandidateSummary, JobDescriptionSummary } from "@/lib/api/client";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — RecruiterMind AI" }] }),
  component: Dashboard,
});

function Dashboard() {
  const [candidateCount, setCandidateCount] = useState<number | null>(null);
  const [jdCount, setJdCount] = useState(0);
  const [backendOnline, setBackendOnline] = useState(false);
  const [recentCandidates, setRecentCandidates] = useState<CandidateSummary[]>([]);
  const [jds, setJds] = useState<JobDescriptionSummary[]>([]);

  useEffect(() => {
    async function load() {
      try {
        await healthCheck();
        setBackendOnline(true);
        const cands = await listCandidates(0, 5);
        setCandidateCount(cands.length);
        setRecentCandidates(cands);
        const jobList = await listJobDescriptions(0, 10);
        setJds(jobList);
        setJdCount(jobList.length);
      } catch {
        setBackendOnline(false);
      }
    }
    load();
  }, []);

  return (
    <AppLayout
      title="Dashboard"
      subtitle={
        backendOnline
          ? <span className="inline-flex items-center gap-1.5"><span className="size-1.5 rounded-full bg-success" /> Backend connected</span>
          : <span className="text-muted-foreground">Backend offline — start the server to see data</span>
      }
      actions={
        <Link to="/jd-analysis" className="btn-primary text-sm">
          Upload JD
        </Link>
      }
    >
      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {[
          { label: "Candidates", value: candidateCount !== null ? candidateCount.toLocaleString() : "—" },
          { label: "Job Descriptions", value: String(jdCount) },
          { label: "Shortlisted", value: "—" },
          { label: "Backend", value: backendOnline ? "Online" : "Offline" },
        ].map(s => (
          <div key={s.label} className="card p-4 animate-slide-up">
            <div className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{s.label}</div>
            <div className="text-2xl font-semibold mt-1 tracking-tight">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent candidates */}
        <div className="card animate-slide-up" style={{ animationDelay: "50ms" }}>
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-sm font-medium">Recent Candidates</h2>
          </div>
          <div className="divide-y divide-border">
            {recentCandidates.length > 0 ? recentCandidates.map((c, i) => (
              <Link
                key={c.id}
                to="/candidates/$id"
                params={{ id: String(c.id) }}
                className="flex items-center gap-3 px-5 py-3 card-hover"
              >
                <span className="text-xs text-muted-foreground font-mono w-5">{i + 1}</span>
                <div className="size-8 rounded-full bg-secondary flex items-center justify-center text-xs font-semibold">
                  {c.name.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{c.name}</div>
                  {c.experience_years && (
                    <div className="text-xs text-muted-foreground">{c.experience_years} years</div>
                  )}
                </div>
              </Link>
            )) : (
              <div className="px-5 py-8 text-center text-sm text-muted-foreground">
                {backendOnline ? "No candidates uploaded yet." : "Start the backend server."}
              </div>
            )}
          </div>
        </div>

        {/* Job descriptions */}
        <div className="card animate-slide-up" style={{ animationDelay: "100ms" }}>
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-sm font-medium">Job Descriptions</h2>
          </div>
          <div className="divide-y divide-border">
            {jds.length > 0 ? jds.map((jd) => (
              <Link
                key={jd.id}
                to="/jd-analysis"
                className="flex items-center gap-3 px-5 py-3 card-hover"
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{jd.title}</div>
                  <div className="text-xs text-muted-foreground">ID: {jd.id}</div>
                </div>
              </Link>
            )) : (
              <div className="px-5 py-8 text-center text-sm text-muted-foreground">
                {backendOnline ? "No job descriptions uploaded yet." : "Start the backend server."}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}