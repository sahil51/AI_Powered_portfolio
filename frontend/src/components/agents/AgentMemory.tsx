"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { AgentMemory } from "@/lib/agent-data";

export interface AgentMemoryProps {
  initialMemory: AgentMemory[];
}

export default function AgentMemory({ initialMemory }: AgentMemoryProps) {
  const [memory, setMemory] = React.useState<AgentMemory[]>(initialMemory);
  const [newContent, setNewContent] = React.useState("");

  const handleAdd = () => {
    if (!newContent.trim()) return;
    const newEntry: AgentMemory = {
      id: `memory-${Date.now()}`,
      content: newContent.trim(),
      createdAt: new Date().toISOString().slice(0, 10),
    };
    setMemory((current) => [newEntry, ...current]);
    setNewContent("");
  };

  const handleDelete = (id: string) => {
    setMemory((current) => current.filter((item) => item.id !== id));
  };

  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-foreground">Memory</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground/80">Add Memory</label>
          <textarea
            rows={4}
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            placeholder="Add a new memory entry for this agent"
            className="w-full rounded-3xl border border-border bg-slate-950/80 px-4 py-3 text-sm text-foreground outline-none transition focus:border-primary/60 focus:ring-1 focus:ring-primary/30"
          />
          <Button variant="primary" size="sm" onClick={handleAdd} className="px-5">
            Add Memory
          </Button>
        </div>

        <div className="space-y-4">
          {memory.map((entry) => (
            <div key={entry.id} className="rounded-3xl border border-border/50 bg-slate-950/50 p-4">
              <div className="flex items-start justify-between gap-4">
                <p className="text-sm text-foreground">{entry.content}</p>
                <Button variant="ghost" size="sm" className="text-destructive" onClick={() => handleDelete(entry.id)}>
                  Delete
                </Button>
              </div>
              <p className="mt-2 text-xs text-muted">{entry.createdAt}</p>
            </div>
          ))}
          {memory.length === 0 && <p className="text-sm text-muted">No memory entries yet. Start building the agent's context.</p>}
        </div>
      </CardContent>
    </Card>
  );
}
