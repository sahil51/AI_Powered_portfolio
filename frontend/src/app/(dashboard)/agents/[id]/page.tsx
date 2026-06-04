import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { AGENTS } from "@/lib/agent-data";
import AgentDetailsTabs from "@/components/agents/AgentDetailsTabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AgentDetailsPageProps {
  params: {
    id: string;
  };
}

const statusClasses: Record<string, string> = {
  Active: "bg-emerald-500/10 text-emerald-200 border border-emerald-500/20",
  Inactive: "bg-slate-700/60 text-muted border border-slate-600/50",
  Paused: "bg-violet-500/10 text-violet-200 border border-violet-500/20",
};

export default function AgentDetailsPage({ params }: AgentDetailsPageProps) {
  const agent = AGENTS.find((item) => item.id === params.id);
  if (!agent) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-3xl border border-white/10 p-6">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-primary/80">Agent details</p>
            <h1 className="text-3xl font-bold text-foreground">{agent.name}</h1>
            <p className="mt-2 text-sm text-muted">{agent.type} • Last executed {agent.lastExecution}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Badge className={statusClasses[agent.status]}>{agent.status}</Badge>
            <Link href="/agents">
              <Button variant="outline" size="sm" className="rounded-full px-4">
                <ArrowLeft className="w-4 h-4" /> Back
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <AgentDetailsTabs agent={agent} />
    </div>
  );
}
