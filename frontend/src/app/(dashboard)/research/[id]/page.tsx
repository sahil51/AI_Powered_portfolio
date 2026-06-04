import { notFound } from "next/navigation";
import { RESEARCH_TASKS } from "@/lib/research-data";
import ResearchOverview from "@/components/research/ResearchOverview";
import ResearchTimeline from "@/components/research/ResearchTimeline";
import ResearchLogs from "@/components/research/ResearchLogs";
import ResearchResult from "@/components/research/ResearchResult";
import Link from "next/link";

interface ResearchDetailPageProps {
  params: { id: string };
}

export default function ResearchDetailPage({ params }: ResearchDetailPageProps) {
  const task = RESEARCH_TASKS.find((item) => item.id === params.id);

  if (!task) {
    notFound();
  }

  return (
    <div className="space-y-8 pb-16">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-primary">Research detail</p>
          <h1 className="mt-4 text-4xl font-semibold text-foreground">{task.title}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-muted">Review the current task status, execution log, and final research output.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/research" className="inline-flex items-center rounded-full border border-white/10 bg-slate-950/80 px-5 py-3 text-sm font-semibold text-foreground transition hover:border-primary/40">
            Back to research
          </Link>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="space-y-6">
          <ResearchOverview task={task} />
          <ResearchTimeline task={task} />
          <ResearchResult task={task} />
        </div>
        <div className="space-y-6">
          <ResearchLogs task={task} />
        </div>
      </div>
    </div>
  );
}
