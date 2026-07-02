import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { healthCheck } from "@/lib/api/client";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [{ title: "RecruiterMind AI — Candidate Ranking & Hiring Predictions" }] }),
  component: Landing,
});

function Landing() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    healthCheck()
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));
  }, []);

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <header className="sticky top-0 z-30 border-b border-border bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <Link to="/" className="font-semibold text-lg tracking-tight">
            RecruiterMind
          </Link>
          <nav className="flex items-center gap-4">
            {backendStatus === "online" ? (
              <span className="text-xs text-muted-foreground inline-flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-success" /> API connected
              </span>
            ) : backendStatus === "offline" ? (
              <span className="text-xs text-muted-foreground inline-flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-destructive" /> API offline
              </span>
            ) : null}
            <Link to="/dashboard" className="btn-primary text-sm">
              Dashboard
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pt-24 pb-16 text-center">
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight leading-tight">
          Rank candidates with AI.
          <br />
          Predict who will succeed.
        </h1>
        <p className="mt-4 text-muted-foreground max-w-lg mx-auto text-lg leading-relaxed">
          Upload job descriptions and candidate profiles. Get ranked shortlists,
          hiring success predictions, and tailored interview questions — all from
          your own backend.
        </p>
        <div className="mt-8 flex items-center justify-center gap-3">
          <Link to="/dashboard" className="btn-primary">
            Go to Dashboard
          </Link>
          <Link to="/jd-analysis" className="btn-ghost">
            Upload a JD
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-24">
        <div className="grid sm:grid-cols-3 gap-4">
          {[
            { title: "Semantic Matching", desc: "Embedding-based similarity scoring between JDs and candidate profiles." },
            { title: "Feature Engineering", desc: "14-dimensional feature extraction covering technical, behavioral, and career signals." },
            { title: "Weighted Ranking", desc: "Configurable scoring formula with technical, retrieval, behavioral, and startup weights." },
            { title: "Hiring Prediction", desc: "1-month, 3-month, and 6-month success probability forecasts with narrative reasoning." },
            { title: "Interview Questions", desc: "Auto-generated technical, behavioral, leadership, and risk-focused questions per candidate." },
            { title: "Twin Detection", desc: "Hierarchical clustering to identify behaviorally similar candidate profiles." },
          ].map((f, i) => (
            <div
              key={f.title}
              className="card p-5 animate-slide-up"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <h3 className="text-sm font-medium mb-1">{f.title}</h3>
              <p className="text-sm text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 text-center text-xs text-muted-foreground">
        RecruiterMind AI — Built with FastAPI + TanStack Start
      </footer>
    </div>
  );
}