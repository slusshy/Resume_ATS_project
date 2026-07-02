import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AppLayout } from "@/components/app-layout";
import { getInterviewQuestions, healthCheck } from "@/lib/api/client";
import type { InterviewQuestions } from "@/lib/api/client";

export const Route = createFileRoute("/interview")({
  head: () => ({ meta: [{ title: "Interview — RecruiterMind AI" }] }),
  component: Interview,
});

function Interview() {
  const [candidateId, setCandidateId] = useState("");
  const [jdId, setJdId] = useState("");
  const [questions, setQuestions] = useState<InterviewQuestions | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate() {
    if (!candidateId.trim() || !jdId.trim()) return;
    setLoading(true);
    setError("");
    setQuestions(null);
    try {
      await healthCheck();
      const q = await getInterviewQuestions(Number(candidateId), Number(jdId));
      setQuestions(q);
    } catch (e: any) {
      setError(e.message || "Failed to generate questions");
    }
    setLoading(false);
  }

  return (
    <AppLayout
      title="Interview Questions"
      subtitle="Generate tailored interview questions for candidates"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input panel */}
        <div className="card p-5 animate-slide-up space-y-4">
          <h2 className="text-sm font-medium">Generate Questions</h2>
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
            <label className="text-xs text-muted-foreground block mb-1">Job Description ID</label>
            <input
              className="input"
              placeholder="e.g. 1"
              value={jdId}
              onChange={e => setJdId(e.target.value)}
            />
          </div>
          <button
            className="btn-primary w-full"
            onClick={handleGenerate}
            disabled={loading || !candidateId.trim() || !jdId.trim()}
          >
            {loading ? "Generating..." : "Generate Questions"}
          </button>
          {error && <p className="text-sm text-destructive animate-fade-in">{error}</p>}
        </div>

        {/* Questions */}
        <div className="lg:col-span-2">
          {questions ? (
            <div className="animate-slide-up space-y-4">
              {questions.technical_questions.length > 0 && (
                <div className="card">
                  <div className="px-5 py-4 border-b border-border">
                    <h2 className="text-sm font-medium">Technical</h2>
                  </div>
                  <div className="divide-y divide-border">
                    {questions.technical_questions.map((q, i) => (
                      <div key={i} className="px-5 py-3 text-sm">{q}</div>
                    ))}
                  </div>
                </div>
              )}

              {questions.behavioral_questions.length > 0 && (
                <div className="card">
                  <div className="px-5 py-4 border-b border-border">
                    <h2 className="text-sm font-medium">Behavioral</h2>
                  </div>
                  <div className="divide-y divide-border">
                    {questions.behavioral_questions.map((q, i) => (
                      <div key={i} className="px-5 py-3 text-sm">{q}</div>
                    ))}
                  </div>
                </div>
              )}

              {questions.leadership_questions.length > 0 && (
                <div className="card">
                  <div className="px-5 py-4 border-b border-border">
                    <h2 className="text-sm font-medium">Leadership</h2>
                  </div>
                  <div className="divide-y divide-border">
                    {questions.leadership_questions.map((q, i) => (
                      <div key={i} className="px-5 py-3 text-sm">{q}</div>
                    ))}
                  </div>
                </div>
              )}

              {questions.risk_validation_questions.length > 0 && (
                <div className="card">
                  <div className="px-5 py-4 border-b border-border">
                    <h2 className="text-sm font-medium">Risk Validation</h2>
                  </div>
                  <div className="divide-y divide-border">
                    {questions.risk_validation_questions.map((q, i) => (
                      <div key={i} className="px-5 py-3 text-sm">{q}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card p-12 flex items-center justify-center">
              <p className="text-sm text-muted-foreground">
                Enter candidate and job IDs, then click "Generate Questions"
              </p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}