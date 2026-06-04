"use client";

import { ResearchTask } from "@/lib/research-data";
import ResearchTaskCard from "@/components/research/ResearchTaskCard";

export interface ResearchBoardProps {
  tasks: ResearchTask[];
}

const statusOrder: Array<"Pending" | "Running" | "Completed" | "Failed"> = ["Pending", "Running", "Completed", "Failed"];

export default function ResearchBoard({ tasks }: ResearchBoardProps) {
  return (
    <div className="grid gap-6 xl:grid-cols-4">
      {statusOrder.map((status) => {
        const columnTasks = tasks.filter((task) => task.status === status);
        return (
          <div key={status} className="space-y-4">
            <div className="rounded-3xl border border-white/10 bg-slate-950/70 px-4 py-4">
              <h3 className="text-base font-semibold text-foreground">{status}</h3>
              <p className="text-xs text-muted mt-1">{columnTasks.length} tasks</p>
            </div>
            <div className="space-y-4">
              {columnTasks.length ? (
                columnTasks.map((task) => <ResearchTaskCard key={task.id} task={task} />)
              ) : (
                <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-6 text-sm text-muted">No tasks in this column.</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
