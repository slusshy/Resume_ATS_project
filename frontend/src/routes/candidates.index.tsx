import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppLayout } from "@/components/app-layout";
import { listCandidates, healthCheck } from "@/lib/api/client";
import type { CandidateSummary } from "@/lib/api/client";

export const Route = createFileRoute("/candidates/")({
  head: () => ({ meta: [{ title: "Candidates — RecruiterMind AI" }] }),
  component: CandidatesPage,
});

function CandidatesPage() {
  const [candidates, setCandidates] = useState<CandidateSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function load() {
      try {
        await healthCheck();
        const cands = await listCandidates(0, 100);
        setCandidates(cands);
      } catch {}
      setLoading(false);
    }
    load();
  }, []);

  const filtered = candidates.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppLayout
      title="Candidates"
      subtitle={loading ? "Loading..." : `${candidates.length} candidates`}
    >
      {/* Search */}
      <div className="mb-4">
        <input
          className="input max-w-xs"
          placeholder="Search by name..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Table */}
      <div className="card overflow-hidden animate-slide-up">
        <div className="grid grid-cols-[1fr_100px_100px] gap-3 px-5 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider border-b border-border bg-muted">
          <div>Name</div>
          <div>Experience</div>
          <div className="text-right">ID</div>
        </div>
        <div className="divide-y divide-border">
          {loading ? (
            <div className="px-5 py-12 text-center text-sm text-muted-foreground">Loading...</div>
          ) : filtered.length === 0 ? (
            <div className="px-5 py-12 text-center text-sm text-muted-foreground">
              {candidates.length === 0
                ? "No candidates uploaded yet. Use the API to upload candidates."
                : "No candidates match your search."}
            </div>
          ) : (
            filtered.map((c, i) => (
              <Link
                key={c.id}
                to="/candidates/$id"
                params={{ id: String(c.id) }}
                className="grid grid-cols-[1fr_100px_100px] gap-3 px-5 py-3 items-center card-hover"
                style={{ animationDelay: `${i * 20}ms` }}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="size-8 rounded-full bg-secondary flex items-center justify-center text-xs font-semibold shrink-0">
                    {c.name.charAt(0)}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{c.name}</div>
                    <div className="text-xs text-muted-foreground truncate">
                      {c.skills?.slice(0, 2).join(", ") || "—"}
                    </div>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  {c.experience_years ? `${c.experience_years}y` : "—"}
                </div>
                <div className="text-sm text-muted-foreground text-right font-mono">
                  #{c.id}
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </AppLayout>
  );
}