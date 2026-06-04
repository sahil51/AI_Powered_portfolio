import { ResearchTask } from "@/lib/research-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface ResearchLogsProps {
  task: ResearchTask;
}

export default function ResearchLogs({ task }: ResearchLogsProps) {
  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-foreground">Execution Logs</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {task.logs.map((log) => (
            <div key={log.id} className="rounded-3xl border border-border/50 bg-slate-950/50 p-4">
              <div className="flex items-center justify-between gap-4 text-sm text-muted">
                <span>{log.timestamp}</span>
                <span className="rounded-full bg-slate-800 px-3 py-1 text-xs uppercase tracking-[0.25em] text-slate-300">{log.duration}</span>
              </div>
              <p className="mt-3 text-foreground font-semibold">{log.event}</p>
              <p className="mt-2 text-sm text-muted">{log.details}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
