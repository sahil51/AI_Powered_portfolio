"use client";

import * as React from "react";
import Link from "next/link";
import { ResearchAgentType, ResearchPriority } from "@/lib/research-data";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const AGENT_TYPES: ResearchAgentType[] = ["Research", "Portfolio", "Recruiter", "Client", "Recommendation", "Project Explainer"];
const PRIORITIES: ResearchPriority[] = ["Low", "Medium", "High"];

export interface ResearchFormPayload {
  title: string;
  query: string;
  agentType: ResearchAgentType;
  priority: ResearchPriority;
}

export interface ResearchFormProps {
  initialData?: Partial<ResearchFormPayload>;
  onSubmit?: (payload: ResearchFormPayload) => void;
}

export default function ResearchForm({ initialData, onSubmit }: ResearchFormProps) {
  const [state, setState] = React.useState<ResearchFormPayload>({
    title: "",
    query: "",
    agentType: "Research",
    priority: "Medium",
    ...initialData,
  });
  const [message, setMessage] = React.useState("");

  const handleChange = <K extends keyof ResearchFormPayload>(key: K, value: ResearchFormPayload[K]) => {
    setState((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!state.title.trim() || !state.query.trim()) {
      setMessage("Please complete title and query before creating the task.");
      return;
    }

    onSubmit?.(state);
    setMessage("Research task created successfully.");
  };

  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-foreground">Create Research Task</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {message && (
          <div className="rounded-3xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-200">
            {message}
          </div>
        )}

        <form className="grid gap-6" onSubmit={handleSubmit}>
          <Input
            label="Task Title"
            placeholder="Enter a descriptive task title"
            value={state.title}
            onChange={(e) => handleChange("title", e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-foreground/80 mb-2">Research Query</label>
            <textarea
              rows={4}
              value={state.query}
              onChange={(e) => handleChange("query", e.target.value)}
              className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
              placeholder="Example: Analyze the latest AI recruiting market shifts."
            />
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-foreground/80 mb-2">Agent Type</label>
              <select
                value={state.agentType}
                onChange={(e) => handleChange("agentType", e.target.value as ResearchAgentType)}
                className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
              >
                {AGENT_TYPES.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground/80 mb-2">Priority</label>
              <select
                value={state.priority}
                onChange={(e) => handleChange("priority", e.target.value as ResearchPriority)}
                className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
              >
                {PRIORITIES.map((level) => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <Link href="/research" className="inline-flex justify-center rounded-xl border border-white/10 bg-slate-900/70 px-5 py-3 text-sm font-semibold text-muted hover:bg-slate-900 transition">
              Cancel
            </Link>
            <Button type="submit" variant="primary" className="inline-flex items-center justify-center px-6 py-3">
              Create Task
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
