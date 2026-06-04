"use client";

import * as React from "react";
import { Agent } from "@/lib/agent-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import AgentOverview from "@/components/agents/AgentOverview";
import AgentMemory from "@/components/agents/AgentMemory";
import AgentExecutions from "@/components/agents/AgentExecutions";
import AgentAnalytics from "@/components/agents/AgentAnalytics";
import AgentSettings from "@/components/agents/AgentSettings";

const tabs = ["Overview", "Memory", "Executions", "Analytics", "Settings"] as const;

type TabKey = (typeof tabs)[number];

export interface AgentDetailsTabsProps {
  agent: Agent;
}

export default function AgentDetailsTabs({ agent }: AgentDetailsTabsProps) {
  const [activeTab, setActiveTab] = React.useState<TabKey>("Overview");

  return (
    <div className="space-y-6">
      <Card className="glass-panel rounded-3xl border border-white/10">
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pb-4">
          <div>
            <CardTitle className="text-xl font-semibold text-foreground">Agent Details</CardTitle>
            <p className="text-sm text-muted">Explore the selected agent's lifecycle across tabs.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {tabs.map((tab) => (
              <Button
                key={tab}
                variant={activeTab === tab ? "primary" : "outline"}
                size="sm"
                className="rounded-full text-xs px-4"
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </Button>
            ))}
          </div>
        </CardHeader>
      </Card>

      <div className="space-y-6">
        {activeTab === "Overview" && <AgentOverview agent={agent} />}
        {activeTab === "Memory" && <AgentMemory initialMemory={agent.memory} />}
        {activeTab === "Executions" && <AgentExecutions executions={agent.executions} />}
        {activeTab === "Analytics" && <AgentAnalytics metrics={agent.metrics} />}
        {activeTab === "Settings" && <AgentSettings agent={agent} />}
      </div>
    </div>
  );
}
