"use client";

import * as React from "react";
import { Agent } from "@/lib/agent-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export interface AgentSettingsProps {
  agent: Agent;
}

export default function AgentSettings({ agent }: AgentSettingsProps) {
  const [goal, setGoal] = React.useState(agent.goal);
  const [systemPrompt, setSystemPrompt] = React.useState(agent.systemPrompt);
  const [temperature, setTemperature] = React.useState(agent.temperature);
  const [model, setModel] = React.useState(agent.model);
  const [message, setMessage] = React.useState("");

  const handleSave = () => {
    setMessage("Settings saved successfully.");
    window.setTimeout(() => setMessage(""), 3000);
  };

  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-foreground">Settings</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {message && (
          <div className="rounded-2xl bg-primary/10 border border-primary/20 px-4 py-3 text-sm text-primary">
            {message}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground/80 mb-2">Agent Goal</label>
            <textarea
              rows={3}
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground/80 mb-2">System Prompt</label>
            <textarea
              rows={4}
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
            />
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-foreground/80 mb-2">Temperature</label>
              <input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground/80 mb-2">Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
              >
                <option value="gpt-4o-mini">gpt-4o-mini</option>
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-4o-realtime">gpt-4o-realtime</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground/80 mb-2">Max Tokens</label>
              <input
                type="number"
                min={100}
                step={50}
                value={agent.maxTokens}
                className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none cursor-not-allowed"
                disabled
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <Button variant="primary" onClick={handleSave} className="px-6 py-3">
            Save Settings
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
