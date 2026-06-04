"use client";

import * as React from "react";
import { MOCK_CANDIDATES, evaluateCandidate } from "@/lib/recruiter-data";
import CandidateCard from "@/components/recruiter/CandidateCard";
import EvaluationSummary from "@/components/recruiter/EvaluationSummary";
import SkillCharts from "@/components/recruiter/SkillCharts";
import ProjectEvaluation from "@/components/recruiter/ProjectEvaluation";
import InterviewPrep from "@/components/recruiter/InterviewPrep";
import ActivityFeed from "@/components/analytics/ActivityFeed";
import { ACTIVITY_FEED } from "@/lib/analytics-data";

export default function RecruiterPage() {
  const [candidates] = React.useState(MOCK_CANDIDATES);
  const [selectedId, setSelectedId] = React.useState<string>(candidates[0]?.id ?? "");

  React.useEffect(() => {
    if (!selectedId && candidates.length) setSelectedId(candidates[0].id);
  }, [candidates, selectedId]);

  const selected = candidates.find((c) => c.id === selectedId) ?? candidates[0];
  const evaluation = evaluateCandidate(selected.id);

  const strongAreas = Object.entries(selected.skills).filter(([,level]) => level === "Expert" || level === "Advanced").map(([s]) => s);
  const weakAreas = Object.entries(selected.skills).filter(([,level]) => level === "Beginner" || level === "Intermediate").map(([s]) => s);

  const recommendedQuestions = [
    "Describe a time you improved API performance at scale.",
    "How do you approach schema design for analytics workloads?",
    "Walk me through the architecture of your Realtime Recommendation Service.",
  ];

  return (
    <div className="space-y-8 pb-16">
      <div className="glass-panel rounded-3xl border border-white/10 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-primary/80">Recruiter Intelligence</p>
            <h1 className="text-3xl font-bold text-foreground">Candidate evaluation and interview preparation</h1>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <aside className="space-y-4">
          <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
            <p className="text-sm uppercase tracking-[0.3em] text-muted mb-3">Candidates</p>
            <div className="space-y-3">
              {candidates.map((cand) => (
                <CandidateCard key={cand.id} candidate={cand} onSelect={() => setSelectedId(cand.id)} />
              ))}
            </div>
          </div>

          <ActivityFeed items={ACTIVITY_FEED} />
        </aside>

        <main className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            <EvaluationSummary evaluation={evaluation} />
            <SkillCharts skills={selected.skills} />
            <div className="rounded-3xl border border-white/10 p-4">
              <p className="text-sm uppercase tracking-[0.3em] text-muted">Quick actions</p>
              <div className="mt-4 flex flex-col gap-3">
                <button className="rounded-3xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-foreground">Schedule interview</button>
                <button className="rounded-3xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-foreground">Download report</button>
                <button className="rounded-3xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-foreground">Share candidate</button>
              </div>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-4">
              <p className="text-sm uppercase tracking-[0.3em] text-muted">Project evaluations</p>
              {selected.projects.map((project) => (
                <ProjectEvaluation key={project.id} project={project} />
              ))}
            </div>

            <div className="space-y-4">
              <InterviewPrep strongAreas={strongAreas} weakAreas={weakAreas} questions={recommendedQuestions} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
