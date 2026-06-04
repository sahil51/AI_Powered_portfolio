import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface InterviewPrepProps {
  strongAreas: string[];
  weakAreas: string[];
  questions: string[];
}

export default function InterviewPrep({ strongAreas, weakAreas, questions }: InterviewPrepProps) {
  return (
    <Card className="rounded-3xl border border-white/10 p-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Interview Preparation</CardTitle>
        <p className="text-sm text-muted">Suggested questions and focus areas</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm text-muted">Strong areas</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {strongAreas.map((s) => (
              <span key={s} className="text-xs px-3 py-1 rounded-full bg-slate-900/80 border border-border text-muted">{s}</span>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm text-muted">Weak areas</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {weakAreas.map((s) => (
              <span key={s} className="text-xs px-3 py-1 rounded-full bg-rose-900/80 border border-border text-rose-200">{s}</span>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm text-muted">Recommended questions</p>
          <div className="mt-2 grid gap-2">
            {questions.map((q, i) => (
              <div key={i} className="rounded-3xl border border-white/5 p-3 bg-slate-950/50">
                <p className="text-sm text-foreground">{q}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-3 justify-end">
          <Button variant="secondary">Schedule Interview</Button>
          <Button variant="ghost">Download Report</Button>
        </div>
      </CardContent>
    </Card>
  );
}
