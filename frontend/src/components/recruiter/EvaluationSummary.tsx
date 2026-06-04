import { CandidateEvaluation } from "@/lib/recruiter-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface EvaluationSummaryProps {
  evaluation: CandidateEvaluation;
}

export default function EvaluationSummary({ evaluation }: EvaluationSummaryProps) {
  return (
    <Card className="rounded-3xl border border-white/10 p-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">AI Evaluation</CardTitle>
        <p className="text-sm text-muted">Interview readiness and technical summary</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-muted">Interview Readiness</p>
            <p className="text-3xl font-bold text-foreground">{evaluation.readinessScore}%</p>
          </div>
          <div className="text-right">
            <Badge className={evaluation.recommendation === "Strong Hire" ? "bg-emerald-500/10 text-emerald-300" : evaluation.recommendation === "Consider" ? "bg-amber-500/10 text-amber-300" : "bg-rose-500/10 text-rose-300"}>{evaluation.recommendation}</Badge>
            <p className="text-sm text-muted mt-2">Missing skills: {evaluation.missingSkills.length}</p>
          </div>
        </div>

        <div className="space-y-2">
          {Object.entries(evaluation.technicalAnalysis).slice(0,5).map(([skill, info]) => (
            <div key={skill} className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm text-foreground">{skill}</p>
                <p className="text-xs text-muted">{info.comment}</p>
              </div>
              <p className="text-sm font-semibold text-foreground">{info.score}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
