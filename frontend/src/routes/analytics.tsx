import { createFileRoute, Link } from "@tanstack/react-router";
import { AppLayout } from "@/components/app-layout";
import { useEffect, useState } from "react";
import {
  healthCheck,
  listJobDescriptions,
  runAnalysis,
  getRankings,
  type JobDescriptionSummary,
  type AnalysisResult,
} from "@/lib/api/client";

export const Route = createFileRoute("/analytics")({
  head: () => ({ meta: [{ title: "AI Analysis — RecruiterMind AI" }] }),
  component: Analytics,
});

function Analytics() {
  const [backendOnline, setBackendOnline] = useState(false);
  const [jds, setJds] = useState<JobDescriptionSummary[]>([]);
  const [selectedJd, setSelectedJd] = useState<number | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    healthCheck().then(() => setBackendOnline(true)).catch(() => {});
    listJobDescriptions(0, 100).then(setJds).catch(() => {});
  }, []);

  async function handleRunAnalysis() {
    if (!selectedJd) {
      setError("Please select a job description");
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const result = await runAnalysis({
        job_description_id: selectedJd,
        // candidate_ids omitted - system will rank ALL candidates automatically
      });
      setAnalysisResult(result);
    } catch (e: any) {
      setError(e.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  async function loadRankings() {
    if (!selectedJd) return;
    setLoading(true);
    try {
      const rankings = await getRankings(selectedJd, 0, 100);
      setAnalysisResult({
        analysis_id: "rankings_view",
        job_title: jds.find(j => j.id === selectedJd)?.title || "Unknown",
        total_candidates_analyzed: rankings.length,
        total_ranked: rankings.length,
        twin_groups_found: 0,
        candidates_in_twin_groups: 0,
        rankings: rankings.map(r => ({
          candidate_id: r.candidate_id,
          rank: r.rank,
          name: "Candidate", // Will be populated if needed
          overall_score: r.overall_score,
          component_scores: {
            technical_relevance: r.technical_fit_score,
            behavioral_signals: r.behavioral_fit_score,
            learning_agility: r.learning_agility_score,
            stability: r.stability_score,
            career_growth: r.growth_potential_score,
            risk_indicators: 0,
            similarity_score: 0,
          },
          reasoning: {
            strengths: [],
            weaknesses: [],
            why_shortlisted: "",
            risk_level: "Low",
          },
          prediction: {
            success_probability: 0.5,
            month_1: "",
            month_3: "",
            month_6: "",
            reasoning: {},
          },
          twin_group_id: null,
          is_strongest_in_twin_group: null,
        })),
        twin_analysis: {},
      });
    } catch (e: any) {
      setError(e.message || "Failed to load rankings");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppLayout
      title="AI Analysis"
      subtitle={
        backendOnline
          ? "Backend connected — Select a JD to rank all candidates"
          : "Backend offline"
      }
    >
      {!backendOnline ? (
        <div className="card p-8 text-center">
          <p className="text-muted-foreground">
            Backend is not running. Start the backend server first.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Job Description Selection */}
          <div className="card p-6 animate-slide-up">
            <h2 className="text-lg font-semibold mb-4">Step 1: Select Job Description</h2>
            {jds.length === 0 ? (
              <p className="text-muted-foreground">
                No job descriptions found.{" "}
                <Link to="/jd-analysis" className="text-primary hover:underline">
                  Upload one first →
                </Link>
              </p>
            ) : (
              <select
                value={selectedJd || ""}
                onChange={(e) => setSelectedJd(Number(e.target.value))}
                className="w-full max-w-md p-2 border border-border rounded-md bg-background"
              >
                <option value="">Select a job description...</option>
                {jds.map((jd) => (
                  <option key={jd.id} value={jd.id}>
                    {jd.title} (ID: {jd.id})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Info Box */}
          <div className="card p-4 bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
            <p className="text-sm text-green-800 dark:text-green-200">
              ✓ Simple JD-only workflow: Select a job description and click "Run AI Analysis". The system automatically fetches ALL candidates from the database, ranks them, and shows you the best matches. No manual candidate selection needed!
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleRunAnalysis}
              disabled={loading || !selectedJd}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Analyzing..." : "Run AI Analysis (All Candidates)"}
            </button>
            <button
              onClick={loadRankings}
              disabled={!selectedJd}
              className="px-4 py-2 border border-border rounded-md hover:bg-secondary disabled:opacity-50"
            >
              Load Existing Rankings
            </button>
          </div>

          {error && (
            <div className="card p-4 border-red-500 bg-red-50 dark:bg-red-950">
              <p className="text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {/* Results */}
          {analysisResult && (
            <div className="space-y-4 animate-slide-up">
              <div className="card p-6">
                <h2 className="text-xl font-semibold mb-4">Analysis Results</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-xs text-muted-foreground">Job Title</div>
                    <div className="font-medium">{analysisResult.job_title}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Total Analyzed</div>
                    <div className="font-medium">{analysisResult.total_candidates_analyzed}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Total Ranked</div>
                    <div className="font-medium">{analysisResult.total_ranked}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Twin Groups</div>
                    <div className="font-medium">{analysisResult.twin_groups_found}</div>
                  </div>
                </div>
              </div>

              {/* Rankings Table */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold mb-4">Top Candidates</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-2">Rank</th>
                        <th className="text-left p-2">Candidate ID</th>
                        <th className="text-left p-2">Score</th>
                        <th className="text-left p-2">Technical</th>
                        <th className="text-left p-2">Behavioral</th>
                        <th className="text-left p-2">Risk Level</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysisResult.rankings.map((r) => (
                        <tr key={r.candidate_id} className="border-b border-border hover:bg-secondary">
                          <td className="p-2 font-mono">#{r.rank}</td>
                          <td className="p-2 font-mono">{r.candidate_id}</td>
                          <td className="p-2">
                            <span className="font-semibold">{(r.overall_score * 100).toFixed(1)}%</span>
                          </td>
                          <td className="p-2">{(r.component_scores.technical_relevance * 100).toFixed(0)}%</td>
                          <td className="p-2">{(r.component_scores.behavioral_signals * 100).toFixed(0)}%</td>
                          <td className="p-2">
                            <span className={`px-2 py-1 rounded text-xs ${
                              r.reasoning.risk_level === "Low"
                                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                                : r.reasoning.risk_level === "Medium"
                                ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                                : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                            }`}>
                              {r.reasoning.risk_level}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-sm text-muted-foreground mt-4">
                  Showing all {analysisResult.rankings.length} ranked candidates (top 100 from full database)
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}