"use client";

import * as React from "react";
import Link from "next/link";
import { RESEARCH_STATS, RESEARCH_TASKS, ResearchStatus } from "@/lib/research-data";
import { Button } from "@/components/ui/button";
import ResearchFilters from "@/components/research/ResearchFilters";
import ResearchStats from "@/components/research/ResearchStats";
import ResearchBoard from "@/components/research/ResearchBoard";

export default function ResearchPage() {
  const [query, setQuery] = React.useState("");
  const [status, setStatus] = React.useState<ResearchStatus | "All">("All");

  const filteredTasks = RESEARCH_TASKS.filter((task) => {
    const matchesQuery = task.title.toLowerCase().includes(query.toLowerCase()) || task.query.toLowerCase().includes(query.toLowerCase());
    const matchesStatus = status === "All" || task.status === status;
    return matchesQuery && matchesStatus;
  });

  return (
    <div className="space-y-8 pb-16">
      <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-primary">Research hub</p>
          <h1 className="mt-4 text-4xl font-semibold text-foreground sm:text-5xl">AI Research tasks and insights</h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-muted">
            Manage research requests, review execution progress, and optimize AI task performance across your portfolio.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/research/create">
            <Button variant="secondary" className="rounded-full px-6 py-3">New task</Button>
          </Link>
          <Link href="/dashboard">
            <Button variant="ghost" className="rounded-full px-6 py-3">Go to dashboard</Button>
          </Link>
        </div>
      </div>

      <ResearchStats stats={RESEARCH_STATS} />

      <ResearchFilters query={query} status={status} onQueryChange={setQuery} onStatusChange={setStatus} />

      <div className="glass-panel rounded-3xl border border-white/10 p-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-foreground">Research tasks</h2>
            <p className="text-sm text-muted">Explore your active and archived research tasks below.</p>
          </div>
          <span className="rounded-3xl bg-slate-950/80 px-4 py-2 text-sm text-foreground/80">{filteredTasks.length} tasks</span>
        </div>
        <ResearchBoard tasks={filteredTasks} />
      </div>
    </div>
  );
}
