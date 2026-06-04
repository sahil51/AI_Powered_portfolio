import { ProjectSummary } from "@/lib/recruiter-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ProjectEvaluationProps {
  project: ProjectSummary;
}

export default function ProjectEvaluation({ project }: ProjectEvaluationProps) {
  return (
    <Card className="rounded-3xl border border-white/10 p-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Project: {project.title}</CardTitle>
        <p className="text-sm text-muted">Code quality and backend readiness</p>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground/90">{project.description}</p>
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-muted">Code Quality</p>
          <p className="text-lg font-semibold text-foreground">{project.codeQualityScore}%</p>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <p className="text-sm text-muted">Backend Ready</p>
          <p className="text-sm font-semibold text-foreground">{project.backendReady ? "Yes" : "No"}</p>
        </div>
      </CardContent>
    </Card>
  );
}
