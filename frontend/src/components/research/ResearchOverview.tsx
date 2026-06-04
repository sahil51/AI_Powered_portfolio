import { ResearchTask } from "@/lib/research-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface ResearchOverviewProps {
  task: ResearchTask;
}

export default function ResearchOverview({ task }: ResearchOverviewProps) {
  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-foreground">Overview</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <p className="text-sm uppercase tracking-[0.25em] text-muted">Title</p>
            <p className="mt-2 text-lg font-semibold text-foreground">{task.title}</p>
          </div>
          <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <p className="text-sm uppercase tracking-[0.25em] text-muted">Agent</p>
            <p className="mt-2 text-lg font-semibold text-foreground">{task.agentType}</p>
          </div>
          <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <p className="text-sm uppercase tracking-[0.25em] text-muted">Status</p>
            <p className="mt-2 text-lg font-semibold text-foreground">{task.status}</p>
          </div>
          <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <p className="text-sm uppercase tracking-[0.25em] text-muted">Created Date</p>
            <p className="mt-2 text-lg font-semibold text-foreground">{task.createdAt}</p>
          </div>
        </div>
        <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
          <p className="text-sm uppercase tracking-[0.25em] text-muted">Research Query</p>
          <p className="mt-2 text-foreground">{task.query}</p>
        </div>
      </CardContent>
    </Card>
  );
}
