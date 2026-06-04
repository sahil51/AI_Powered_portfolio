"use client";

import Link from "next/link";
import { Eye, Pencil, Trash2, Play, Pause } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Agent } from "@/lib/agent-data";

export interface AgentCardProps {
  agent: Agent;
  onToggleStatus: (id: string) => void;
  onDelete: (id: string) => void;
}

const statusClasses: Record<string, string> = {
  Active: "bg-emerald-500/10 text-emerald-200 border border-emerald-500/20",
  Inactive: "bg-slate-700/60 text-muted border border-slate-600/50",
  Paused: "bg-violet-500/10 text-violet-200 border border-violet-500/20",
};

export default function AgentCard({ agent, onToggleStatus, onDelete }: AgentCardProps) {
  return (
    <Card className="h-full flex flex-col justify-between bg-slate-950/70 border border-white/10 shadow-[0_25px_50px_-25px_rgba(15,23,42,0.8)]">
      <div>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="text-lg font-semibold text-foreground/95">{agent.name}</CardTitle>
            <Badge className={statusClasses[agent.status]}>{agent.status}</Badge>
          </div>
          <p className="mt-3 text-sm text-muted">{agent.description}</p>
        </CardHeader>

        <CardContent className="space-y-3 pt-0">
          <div className="grid grid-cols-2 gap-3 text-sm text-muted">
            <div>
              <p className="text-foreground/80">Type</p>
              <p className="mt-1 text-foreground">{agent.type}</p>
            </div>
            <div>
              <p className="text-foreground/80">Created</p>
              <p className="mt-1 text-foreground">{agent.createdAt}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm text-muted">
            <div>
              <p className="text-foreground/80">Last Execution</p>
              <p className="mt-1 text-foreground">{agent.lastExecution}</p>
            </div>
            <div>
              <p className="text-foreground/80">Total Execs</p>
              <p className="mt-1 text-foreground">{agent.totalExecutions}</p>
            </div>
          </div>
        </CardContent>
      </div>

      <div className="border-t border-border/50 pt-4 mt-4">
        <div className="flex flex-wrap gap-2">
          <Link href={`/agents/${agent.id}`} className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-foreground bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors">
            <Eye className="w-4 h-4" /> View
          </Link>
          <Button variant="outline" size="sm" className="px-3" onClick={() => onToggleStatus(agent.id)}>
            {agent.status === "Active" ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {agent.status === "Active" ? "Deactivate" : "Activate"}
          </Button>
          <Button variant="ghost" size="sm" className="text-destructive" onClick={() => onDelete(agent.id)}>
            <Trash2 className="w-4 h-4" /> Delete
          </Button>
        </div>
      </div>
    </Card>
  );
}
