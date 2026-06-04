"use client";

import * as React from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AGENTS, AgentType } from "@/lib/agent-data";
import AgentCard from "@/components/agents/AgentCard";
import AgentFilters from "@/components/agents/AgentFilters";

export default function AgentsPage() {
  const [agents, setAgents] = React.useState(AGENTS);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [activeType, setActiveType] = React.useState<AgentType | "All">("All");

  const filteredAgents = React.useMemo(
    () =>
      agents.filter((agent) => {
        const matchesSearch = [agent.name, agent.goal, agent.type].some((value) =>
          value.toLowerCase().includes(searchQuery.toLowerCase())
        );
        const matchesType = activeType === "All" || agent.type === activeType;
        return matchesSearch && matchesType;
      }),
    [agents, searchQuery, activeType]
  );

  const activeCount = agents.filter((agent) => agent.status === "Active").length;
  const inactiveCount = agents.filter((agent) => agent.status !== "Active").length;
  const totalExecutions = agents.reduce((sum, agent) => sum + agent.totalExecutions, 0);

  const toggleStatus = (id: string) => {
    setAgents((current) =>
      current.map((agent) =>
        agent.id === id
          ? {
              ...agent,
              status: agent.status === "Active" ? "Inactive" : "Active",
            }
          : agent
      )
    );
  };

  const handleDelete = (id: string) => {
    setAgents((current) => current.filter((agent) => agent.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-3xl border border-white/10 p-6">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="space-y-2">
            <p className="text-sm uppercase tracking-[0.3em] text-primary/80">Agents</p>
            <h1 className="text-3xl font-bold text-foreground">Agent Management</h1>
            <p className="max-w-2xl text-sm leading-6 text-muted">
              Manage your multi-agent workforce, inspect performance, and configure new AI assistants.
            </p>
          </div>
          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center">
            <Link href="/agents/create">
              <Button variant="primary" size="lg" className="inline-flex items-center gap-2">
                <Plus className="w-4 h-4" /> Create Agent
              </Button>
            </Link>
          </div>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <Card className="glass-panel rounded-3xl border border-white/10 bg-slate-950/60">
            <CardContent className="space-y-2">
              <p className="text-sm uppercase tracking-[0.25em] text-muted">Total Agents</p>
              <p className="text-3xl font-bold text-foreground">{agents.length}</p>
            </CardContent>
          </Card>
          <Card className="glass-panel rounded-3xl border border-white/10 bg-slate-950/60">
            <CardContent className="space-y-2">
              <p className="text-sm uppercase tracking-[0.25em] text-muted">Active Agents</p>
              <p className="text-3xl font-bold text-foreground">{activeCount}</p>
            </CardContent>
          </Card>
          <Card className="glass-panel rounded-3xl border border-white/10 bg-slate-950/60">
            <CardContent className="space-y-2">
              <p className="text-sm uppercase tracking-[0.25em] text-muted">Total Executions</p>
              <p className="text-3xl font-bold text-foreground">{totalExecutions}</p>
            </CardContent>
          </Card>
        </div>
      </div>

      <AgentFilters
        searchQuery={searchQuery}
        activeType={activeType}
        onSearchChange={setSearchQuery}
        onTypeChange={setActiveType}
      />

      <div className="grid gap-6 xl:grid-cols-3">
        {filteredAgents.length ? (
          filteredAgents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} onToggleStatus={toggleStatus} onDelete={handleDelete} />
          ))
        ) : (
          <div className="glass-panel col-span-full rounded-3xl border border-white/10 p-8 text-center">
            <p className="text-lg font-semibold text-foreground mb-2">No agents matched your search.</p>
            <p className="text-sm text-muted">Try a different query or create a new agent.</p>
          </div>
        )}
      </div>
    </div>
  );
}
