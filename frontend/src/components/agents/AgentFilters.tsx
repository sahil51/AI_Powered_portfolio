"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AgentType, AGENT_TYPES } from "@/lib/agent-data";

export interface AgentFiltersProps {
  searchQuery: string;
  activeType: AgentType | "All";
  onSearchChange: (value: string) => void;
  onTypeChange: (value: AgentType | "All") => void;
}

export default function AgentFilters({ searchQuery, activeType, onSearchChange, onTypeChange }: AgentFiltersProps) {
  return (
    <div className="glass-panel rounded-3xl border border-white/10 p-4 flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
      <div className="flex-1 min-w-0">
        <Input
          label="Search Agent"
          placeholder="Search by name or goal"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full"
        />
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="min-w-[220px]">
          <label className="block text-sm font-medium text-foreground/80 mb-2">Filter By Agent Type</label>
          <select
            value={activeType}
            onChange={(e) => onTypeChange(e.target.value as AgentType | "All")}
            className="w-full rounded-xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
          >
            <option value="All">All types</option>
            {AGENT_TYPES.map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
