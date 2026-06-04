"use client";

import Link from "next/link";
import { ArrowRight, Clock3, Flag } from "lucide-react";
import { ResearchTask } from "@/lib/research-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const statusClasses: Record<string, string> = {
  Pending: "bg-yellow-500/10 text-yellow-200 border border-yellow-500/20",
  Running: "bg-blue-500/10 text-blue-200 border border-blue-500/20",
  Completed: "bg-emerald-500/10 text-emerald-200 border border-emerald-500/20",
  Failed: "bg-red-500/10 text-red-200 border border-red-500/20",
};

const priorityClasses: Record<string, string> = {
  Low: "bg-slate-700/60 text-slate-200",
  Medium: "bg-violet-500/10 text-violet-200",
  High: "bg-red-500/10 text-red-200",
};

export interface ResearchTaskCardProps {
  task: ResearchTask;
}

export default function ResearchTaskCard({ task }: ResearchTaskCardProps) {
  return (
    <Card className="glass-panel rounded-3xl border border-white/10 bg-slate-950/70 shadow-2xl shadow-slate-950/20">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="text-lg font-semibold text-foreground">{task.title}</CardTitle>
          <Badge className={statusClasses[task.status]}>{task.status}</Badge>
        </div>
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted">
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-900/60 border border-border">{task.agentType}</span>
          <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full ${priorityClasses[task.priority]} border border-border`}>{task.priority}</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        <div className="grid gap-3 text-sm text-muted">
          <div className="flex items-center justify-between rounded-3xl border border-border/50 bg-slate-950/50 p-3">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted">Created</p>
              <p className="text-sm text-foreground">{task.createdAt}</p>
            </div>
            <div className="inline-flex items-center gap-1 text-xs text-muted">
              <Clock3 className="w-4 h-4" /> {task.agentType}
            </div>
          </div>
          <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-3 text-sm text-foreground">
            <p className="text-sm font-medium text-foreground">Query</p>
            <p className="mt-2 text-sm text-muted">{task.query}</p>
          </div>
        </div>

        <div className="flex items-center justify-between gap-3">
          <Link href={`/research/${task.id}`} className="inline-flex items-center gap-2 text-sm font-semibold text-accent hover:text-foreground">
            View details <ArrowRight className="w-4 h-4" />
          </Link>
          <div className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.25em] text-muted">
            <Flag className="w-4 h-4" /> {task.status}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
