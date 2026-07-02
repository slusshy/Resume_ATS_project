import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AppLayout } from "@/components/app-layout";
import { getPrediction, getRankings, listCandidates, healthCheck } from "@/lib/api/client";
import type { PredictionResult, RankingEntry } from "@/lib/api/client";
import { useEffect } from "react";

export const Route = createFileRoute("/prediction")({
  head: () => ({ meta: [{ title: "Predictions — RecruiterMind AI" }] }),
  component: Prediction,
});

function Prediction() {
  const [jdId, setJdId] = useState("");
  const [candidateId, setCandidateId] = useState("");
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleFetch() {
    if (!candidateId.trim()) return;
    setLoading(true);
    setError("");
    setPrediction(null);
    try {
      await healthCheck();
      const p = await getPrediction(
        Number(candidateId),
        jdId.trim() ? Number(jdId) : undefined
      );
      setPrediction(p);
    } catch (e: any) {
      setError(e.message || "Failed to fetch prediction");
    }
    setLoading(false);
  }

  return (
    <AppLayout
      title="Predictions"
      subtitle="View hiring success predictions for candidates"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input panel */}
        <div className="card p-5 animate-slide-up space-y-4">
          <h2 className="text-sm font-medium">Get Prediction</h2>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Candidate ID</label>
            <input
              className="input"
              placeholder="e.g. 1"
              value={candidateId}
              onChange={e => setCandidateId(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Job Description ID (optional)</label>
            <input
              className="input"
              placeholder="e.g. 1"
              value={jdId}
              onChange={e => setJdId(e.target.value)}
            />
          </div>
          <button
            className="btn-primary w-full"
            onClick={handleFetch}
            disabled={loading || !candidateId.trim()}
          >
            {loading ? "Loading..." : "Get Prediction"}
          </button>
          {error && <p className="text-sm text-destructive animate-fade-in">{error}</p>}
        </div>

        {/* Prediction result */}
        <div className="lg:col-span-2">
          {prediction ? (
            <div className="card animate-slide-up">
              <div className="px-5 py-4 border-b border-border">
                <h2 className="text-sm font-medium">
                  Candidate #{prediction.candidate_id}
                </h2>
              </div>
              <div className="p-5 space-y-4">
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-semibold tracking-tight">
                    {prediction.success_probability}%
                  </span>
                  <span className="text-sm text-muted-foreground">success probability</span>
                </div>

                {prediction.month_1_performance && (
                  <div>
                    <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                      Month 1
                    </h3>
                    <p className="text-sm">{prediction.month_1_performance}</p>
                  </div>
                )}

                {prediction.month_3_performance && (
                  <div>
                    <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                      Month 3
                    </h3>
                    <p className="text-sm">{prediction.month_3_performance}</p>
                  </div>
                )}

                {prediction.month_6_performance && (
                  <div>
                    <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                      Month 6
                    </h3>
                    <p className="text-sm">{prediction.month_6_performance}</p>
                  </div>
                )}

                {prediction.reasoning && Object.keys(prediction.reasoning).length > 0 && (
                  <div>
                    <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                      Reasoning
                    </h3>
                    <div className="space-y-2 text-sm">
                      {Object.entries(prediction.reasoning).map(([key, val]) => (
                        <p key={key}>
                          <span className="font-medium capitalize">{key}:</span>{" "}
                          <span className="text-muted-foreground">{val}</span>
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card p-12 flex items-center justify-center">
              <p className="text-sm text-muted-foreground">
                Enter a candidate ID and click "Get Prediction"
              </p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}