"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ResearchStatus } from "@/lib/research-data";

export interface ResearchFiltersProps {
  query: string;
  status: ResearchStatus | "All";
  onQueryChange: (value: string) => void;
  onStatusChange: (value: ResearchStatus | "All") => void;
}

const statuses: Array<ResearchStatus | "All"> = ["All", "Pending", "Running", "Completed", "Failed"];

export default function ResearchFilters({ query, status, onQueryChange, onStatusChange }: ResearchFiltersProps) {
  return (
    <div className="glass-panel rounded-3xl border border-white/10 p-4 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div className="flex-1 min-w-0">
        <Input
          label="Search tasks"
          placeholder="Search by title or query"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          className="w-full"
        />
      </div>
      <div className="min-w-[220px]">
        <label className="block text-sm font-medium text-foreground/80 mb-2">Filter status</label>
        <select
          value={status}
          onChange={(e) => onStatusChange(e.target.value as ResearchStatus | "All")}
          className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
        >
          {statuses.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
