"use client";

import * as React from "react";
import Link from "next/link";
import { Agent, AgentType, AGENT_TYPES } from "@/lib/agent-data";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export interface AgentFormPayload {
  name: string;
  type: AgentType;
  goal: string;
  description: string;
  systemPrompt: string;
  temperature: number;
  maxTokens: number;
  model: string;
}

export interface AgentFormProps {
  initialValues?: Partial<AgentFormPayload>;
  onSubmit?: (values: AgentFormPayload) => void;
}

const defaultValues: AgentFormPayload = {
  name: "",
  type: "Research Agent",
  goal: "",
  description: "",
  systemPrompt: "",
  temperature: 0.35,
  maxTokens: 1000,
  model: "gpt-4o-mini",
};

export default function AgentForm({ initialValues, onSubmit }: AgentFormProps) {
  const [values, setValues] = React.useState<AgentFormPayload>({
    ...defaultValues,
    ...initialValues,
  });
  const [showAdvanced, setShowAdvanced] = React.useState(true);
  const [statusMessage, setStatusMessage] = React.useState<string>("");

  const handleChange = (key: keyof AgentFormPayload, value: string | number) => {
    setValues((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatusMessage("");
    onSubmit?.(values);
    setStatusMessage("Agent configuration saved successfully.");
  };

  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl font-semibold text-foreground">Create Agent</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {statusMessage && (
          <div className="rounded-2xl bg-emerald-500/10 border border-emerald-500/20 px-4 py-3 text-sm text-emerald-200">
            {statusMessage}
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          <Input
            label="Agent Name"
            placeholder="Example: Talent Scout"
            value={values.name}
            onChange={(e) => handleChange("name", e.target.value)}
          />
          <div>
            <label className="block text-sm font-medium text-foreground/80 mb-2">Agent Type</label>
            <select
              value={values.type}
              onChange={(e) => handleChange("type", e.target.value as AgentType)}
              className="w-full rounded-xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
            >
              {AGENT_TYPES.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground/80 mb-2">Goal</label>
            <textarea
              value={values.goal}
              onChange={(e) => handleChange("goal", e.target.value)}
              rows={3}
              className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground/80 mb-2">Description</label>
            <textarea
              value={values.description}
              onChange={(e) => handleChange("description", e.target.value)}
              rows={4}
              className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground/80 mb-2">System Prompt</label>
            <textarea
              value={values.systemPrompt}
              onChange={(e) => handleChange("systemPrompt", e.target.value)}
              rows={5}
              className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
            />
          </div>
        </div>

        <div className="rounded-3xl border border-border/50 bg-slate-950/30 p-4">
          <div className="flex items-center justify-between gap-4 mb-4">
            <div>
              <p className="text-sm font-semibold text-foreground">Advanced Settings</p>
              <p className="text-xs text-muted">Fine tune your agent's behavior.</p>
            </div>
            <Badge className="bg-white/5 text-foreground border border-white/10 cursor-pointer" onClick={() => setShowAdvanced((value) => !value)}>
              {showAdvanced ? "Hide" : "Show"}
            </Badge>
          </div>

          {showAdvanced && (
            <div className="grid gap-6 md:grid-cols-3">
              <div>
                <label className="block text-sm font-medium text-foreground/80 mb-2">Temperature</label>
                <input
                  type="number"
                  step="0.05"
                  min={0}
                  max={1}
                  value={values.temperature}
                  onChange={(e) => handleChange("temperature", Number(e.target.value))}
                  className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground/80 mb-2">Max Tokens</label>
                <input
                  type="number"
                  min={100}
                  step={50}
                  value={values.maxTokens}
                  onChange={(e) => handleChange("maxTokens", Number(e.target.value))}
                  className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground/80 mb-2">Model</label>
                <select
                  value={values.model}
                  onChange={(e) => handleChange("model", e.target.value)}
                  className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
                >
                  <option value="gpt-4o-mini">gpt-4o-mini</option>
                  <option value="gpt-4o">gpt-4o</option>
                  <option value="gpt-4o-realtime">gpt-4o-realtime</option>
                </select>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
          <Link href="/agents" className="inline-flex justify-center rounded-xl border border-white/10 bg-slate-900/70 px-5 py-3 text-sm font-semibold text-muted hover:bg-slate-900 transition">
            Cancel
          </Link>
          <Button type="submit" variant="primary" className="px-6 py-3">
            Create Agent
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
