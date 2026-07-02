import { createFileRoute } from "@tanstack/react-router";
import { AppLayout } from "@/components/app-layout";
import { useEffect, useState } from "react";
import { healthCheck } from "@/lib/api/client";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings — RecruiterMind AI" }] }),
  component: Settings,
});

function Settings() {
  const [backendInfo, setBackendInfo] = useState<{ version?: string; status?: string }>({});

  useEffect(() => {
    healthCheck().then(setBackendInfo).catch(() => {});
  }, []);

  return (
    <AppLayout title="Settings">
      <div className="card p-5 animate-slide-up space-y-4 max-w-lg">
        <h2 className="text-sm font-medium">API Configuration</h2>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-muted-foreground">API URL</dt>
            <dd className="font-mono text-xs">http://localhost:8000</dd>
          </div>
          {backendInfo.status && (
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Status</dt>
              <dd>{backendInfo.status}</dd>
            </div>
          )}
          {backendInfo.version && (
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Version</dt>
              <dd>{backendInfo.version}</dd>
            </div>
          )}
        </dl>
      </div>
    </AppLayout>
  );
}