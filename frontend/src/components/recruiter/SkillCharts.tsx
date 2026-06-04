import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface SkillChartsProps {
  skills: Record<string, string>;
}

export default function SkillCharts({ skills }: SkillChartsProps) {
  const entries = Object.entries(skills);

  return (
    <Card className="rounded-3xl border border-white/10 p-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Skill Gap Analysis</CardTitle>
        <p className="text-sm text-muted">Coverage and missing skills visualized</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3">
          {entries.map(([skill, level]) => {
            const widths = { Expert: 100, Advanced: 85, Intermediate: 60, Beginner: 30 } as Record<string, number>;
            return (
              <div key={skill} className="space-y-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-foreground">{skill}</p>
                  <p className="text-xs text-muted">{level}</p>
                </div>
                <div className="h-2 rounded-full bg-slate-900/70">
                  <div className="h-full rounded-full bg-gradient-to-r from-primary to-accent" style={{ width: `${widths[level] || 20}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
