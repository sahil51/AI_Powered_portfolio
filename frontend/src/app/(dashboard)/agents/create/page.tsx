"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import AgentForm, { AgentFormPayload } from "@/components/agents/AgentForm";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function CreateAgentPage() {
  const router = useRouter();
  const [status, setStatus] = React.useState<string>("");

  const handleSubmit = (values: AgentFormPayload) => {
    setStatus("Agent created successfully. Redirecting to agent list...");
    setTimeout(() => {
      router.push("/agents");
    }, 900);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-primary/80">Create agent</p>
          <h1 className="text-3xl font-bold text-foreground">New Agent Configuration</h1>
          <p className="max-w-2xl text-sm text-muted mt-2">
            Build a new agent for your multi-agent portfolio and customize its behavior with advanced settings.
          </p>
        </div>
        <Link href="/agents">
          <Button variant="outline" size="md" className="inline-flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" /> Back to agents
          </Button>
        </Link>
      </div>

      <AgentForm onSubmit={handleSubmit} />

      {status && (
        <div className="rounded-3xl border border-primary/20 bg-primary/10 p-4 text-sm text-primary">{status}</div>
      )}
    </div>
  );
}
