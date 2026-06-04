import { ResearchTask } from "@/lib/research-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface ResearchTimelineProps {
  task: ResearchTask;
}

export default function ResearchTimeline({ task }: ResearchTimelineProps) {
  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-foreground">Execution Timeline</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          {task.timeline.map((entry, index) => (
            <div key={`${entry.date}-${index}`} className="rounded-3xl border border-border/50 bg-slate-950/50 p-4">
              <p className="text-sm text-muted">{entry.date}</p>
              <p className="mt-1 text-base text-foreground">{entry.label}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
