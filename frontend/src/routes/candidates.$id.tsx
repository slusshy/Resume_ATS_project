import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AppLayout } from "@/components/app-layout";
import { getCandidate, healthCheck } from "@/lib/api/client";
import type { CandidateDetail } from "@/lib/api/client";

export const Route = createFileRoute("/candidates/$id")({
  loader: async ({ params }) => {
    try {
      const hc = await healthCheck();
      if (hc.status === "running") {
        const c = await getCandidate(Number(params.id));
        return c;
      }
    } catch {}
    return null;
  },
  head: ({ loaderData }) => ({ meta: [{ title: `${(loaderData as any)?.name ?? "Candidate"} — RecruiterMind AI` }] }),
  component: CandidateDetail,
  notFoundComponent: () => <div className="p-8 text-center text-muted-foreground">Candidate not found.</div>,
});

function CandidateDetail() {
  const data = Route.useLoaderData() as CandidateDetail | null;
  const params = Route.useParams();

  const name = data?.name ?? `Candidate #${params.id}`;
  const skills = data?.skills ?? [];
  const skillsList = Array.isArray(skills) ? skills.map(s => typeof s === "string" ? s : (s as any).name || "") : [];

  return (
    <AppLayout
      actions={
        <Link to="/candidates" className="btn-ghost text-sm">
          ← Back
        </Link>
      }
    >
      {/* Profile card */}
      <div className="card p-6 animate-slide-up">
        <div className="flex items-start gap-4">
          <div className="size-14 rounded-full bg-secondary flex items-center justify-center text-lg font-semibold shrink-0">
            {name.charAt(0)}
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-semibold tracking-tight">{name}</h1>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {skillsList.map(s => (
                <span key={s} className="tag">{s}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Profile details */}
      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
          <div className="card p-5 animate-slide-up" style={{ animationDelay: "50ms" }}>
            <h2 className="text-sm font-medium mb-3">Details</h2>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Experience</dt>
                <dd>{data.experience_years ? `${data.experience_years} years` : "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Projects</dt>
                <dd>{data.projects?.length ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Certifications</dt>
                <dd>{data.certifications?.length ?? 0}</dd>
              </div>
            </dl>
          </div>

      <div className="card p-5 animate-slide-up" style={{ animationDelay: "100ms" }}>
        <h2 className="text-sm font-medium mb-3">AI-Extracted Information</h2>
        <dl className="space-y-3 text-sm">
          {data.summary && (
            <div>
              <dt className="text-muted-foreground mb-1">Professional Summary</dt>
              <dd className="text-foreground">{data.summary}</dd>
            </div>
          )}
          <div className="flex justify-between">
            <dt className="text-muted-foreground">Experience</dt>
            <dd>{data.experience_years ? `${data.experience_years} years` : "—"}</dd>
          </div>
          {data.education && (
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Education</dt>
              <dd>{data.education}</dd>
            </div>
          )}
          {data.languages && data.languages.length > 0 && (
            <div>
              <dt className="text-muted-foreground mb-1">Languages</dt>
              <dd className="flex flex-wrap gap-1.5">
                {data.languages.map((lang: string) => <span key={lang} className="tag">{lang}</span>)}
              </dd>
            </div>
          )}
          {data.certifications && data.certifications.length > 0 && (
            <div>
              <dt className="text-muted-foreground mb-1">Certifications</dt>
              <dd className="flex flex-wrap gap-1.5">
                {data.certifications.map((cert: string) => <span key={cert} className="tag">{cert}</span>)}
              </dd>
            </div>
          )}
          {data.projects && data.projects.length > 0 && (
            <div>
              <dt className="text-muted-foreground mb-1">Projects</dt>
              <dd className="space-y-2">
                {data.projects.map((project: any, idx: number) => (
                  <div key={idx} className="pl-3 border-l-2 border-muted">
                    <p className="font-medium text-xs">{project.name || `Project ${idx + 1}`}</p>
                    {project.description && <p className="text-xs text-muted-foreground mt-0.5">{project.description}</p>}
                  </div>
                ))}
              </dd>
            </div>
          )}
        </dl>
      </div>

        </div>
      )}
    </AppLayout>
  );
}