import { Agent } from "@/lib/agent-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export interface AgentOverviewProps {
  agent: Agent;
}

const statusClasses: Record<string, string> = {
  Active: "bg-emerald-500/10 text-emerald-200 border border-emerald-500/20",
  Inactive: "bg-slate-700/60 text-muted border border-slate-600/50",
  Paused: "bg-violet-500/10 text-violet-200 border border-violet-500/20",
};

export default function AgentOverview({ agent }: AgentOverviewProps) {
  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-foreground">Overview</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-3 rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <p className="text-sm uppercase tracking-[0.25em] text-muted">Agent Name</p>
            <p className="text-lg font-semibold text-foreground">{agent.name}</p>
            <p className="text-sm text-muted">{agent.description}</p>
          </div>
          <div className="space-y-3 rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.25em] text-muted">Type</p>
                <p className="text-foreground">{agent.type}</p>
              </div>
              <Badge className={statusClasses[agent.status]}>{agent.status}</Badge>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-sm uppercase tracking-[0.25em] text-muted">Created at</p>
                <p className="text-foreground">{agent.createdAt}</p>
              </div>
              <div>
                <p className="text-sm uppercase tracking-[0.25em] text-muted">Total executions</p>
                <p className="text-foreground">{agent.totalExecutions}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <p className="text-sm uppercase tracking-[0.25em] text-muted">Goal</p>
            <p className="mt-3 text-foreground">{agent.goal}</p>
          </div>
          <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <p className="text-sm uppercase tracking-[0.25em] text-muted">System Prompt</p>
            <p className="mt-3 text-foreground">{agent.systemPrompt}</p>
          </div>
          <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <p className="text-sm uppercase tracking-[0.25em] text-muted">Model</p>
            <p className="mt-3 text-foreground">{agent.model}</p>
            <p className="text-sm text-muted mt-1">Temperature {agent.temperature}, {agent.maxTokens} tokens</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
