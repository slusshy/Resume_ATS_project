import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AppLayout } from "@/components/app-layout";
import { uploadJobDescription, listJobDescriptions } from "@/lib/api/client";
import type { JobDescriptionSummary } from "@/lib/api/client";
import { useEffect } from "react";

export const Route = createFileRoute("/jd-analysis")({
  head: () => ({ meta: [{ title: "Job Descriptions — RecruiterMind AI" }] }),
  component: JDAnalysis,
});

function JDAnalysis() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [jds, setJds] = useState<JobDescriptionSummary[]>([]);

  useEffect(() => {
    listJobDescriptions(0, 20).then(setJds).catch(() => {});
  }, []);

  async function handleUpload() {
    if (!title.trim() || !description.trim()) return;
    setUploading(true);
    setMessage("");
    try {
      const res = await uploadJobDescription({ title, description });
      setMessage(`Uploaded: ${res.title} (ID: ${res.job_description_id})`);
      setTitle("");
      setDescription("");
      const updated = await listJobDescriptions(0, 20);
      setJds(updated);
    } catch (e: any) {
      setMessage(e.message || "Upload failed");
    }
    setUploading(false);
  }

  return (
    <AppLayout
      title="Job Descriptions"
      subtitle="Upload job descriptions to use in candidate analysis"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload form */}
        <div className="card p-5 animate-slide-up space-y-4">
          <h2 className="text-sm font-medium">Upload New JD</h2>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Title</label>
            <input
              className="input"
              placeholder="e.g. Senior ML Engineer"
              value={title}
              onChange={e => setTitle(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Description</label>
            <textarea
              className="input min-h-[180px] py-2 resize-y"
              placeholder="Paste the full job description here..."
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
          </div>
          <button
            className="btn-primary w-full"
            onClick={handleUpload}
            disabled={uploading || !title.trim() || !description.trim()}
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>
          {message && (
            <p className="text-sm text-muted-foreground animate-fade-in">{message}</p>
          )}
        </div>

        {/* Existing JDs */}
        <div className="card animate-slide-up" style={{ animationDelay: "50ms" }}>
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-sm font-medium">Uploaded JDs ({jds.length})</h2>
          </div>
          <div className="divide-y divide-border">
            {jds.length === 0 ? (
              <div className="px-5 py-12 text-center text-sm text-muted-foreground">
                No job descriptions uploaded yet.
              </div>
            ) : (
              jds.map((jd, i) => (
                <div key={jd.id} className="px-5 py-3 flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium truncate">{jd.title}</div>
                    <div className="text-xs text-muted-foreground">ID: {jd.id}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}