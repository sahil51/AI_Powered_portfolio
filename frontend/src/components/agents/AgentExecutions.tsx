"use client";

import * as React from "react";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import { AgentExecution } from "@/lib/agent-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export interface AgentExecutionsProps {
  executions: AgentExecution[];
}

const PAGE_SIZE = 4;

export default function AgentExecutions({ executions }: AgentExecutionsProps) {
  const [page, setPage] = React.useState(1);
  const [query, setQuery] = React.useState("");
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  const filtered = React.useMemo(
    () => executions.filter((item) => item.prompt.toLowerCase().includes(query.toLowerCase()) || item.response.toLowerCase().includes(query.toLowerCase())),
    [executions, query]
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  React.useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-4">
        <div>
          <CardTitle className="text-xl font-semibold text-foreground">Executions</CardTitle>
          <p className="text-sm text-muted">Live execution log with search and pagination.</p>
        </div>
        <div className="w-full sm:w-72">
          <Input
            label="Search executions"
            placeholder="Filter by prompt or response"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        <div className="overflow-x-auto rounded-3xl border border-border/50 bg-slate-950/40">
          <table className="min-w-full divide-y divide-border text-sm text-left">
            <thead className="bg-slate-950/70 text-muted text-xs uppercase tracking-[0.18em]">
              <tr>
                <th className="px-4 py-3">Execution ID</th>
                <th className="px-4 py-3">Prompt</th>
                <th className="px-4 py-3">Response</th>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {currentItems.map((item) => (
                <tr key={item.id} className="hover:bg-slate-900/40">
                  <td className="px-4 py-3 text-foreground/90">{item.id}</td>
                  <td className="px-4 py-3 text-foreground/80">{item.prompt}</td>
                  <td className="px-4 py-3 text-foreground/80 truncate max-w-[260px]">{item.response}</td>
                  <td className="px-4 py-3 text-foreground/80">{item.executionTime}</td>
                  <td className="px-4 py-3 text-foreground/80">{item.createdAt}</td>
                  <td className="px-4 py-3">
                    <Button variant="ghost" size="sm" onClick={() => setSelectedId(item.id)}>
                      View
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted">Showing {currentItems.length} of {filtered.length} executions</p>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(p - 1, 1))} disabled={page === 1}>
              <ChevronLeft className="w-4 h-4" />
              Prev
            </Button>
            <span className="text-sm text-foreground/80">Page {page} / {totalPages}</span>
            <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(p + 1, totalPages))} disabled={page === totalPages}>
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {selectedId && (
          <div className="rounded-3xl border border-border/50 bg-slate-950/60 p-4">
            <div className="flex items-center justify-between gap-4 mb-3">
              <p className="text-sm font-semibold text-foreground">Execution details</p>
              <Button variant="ghost" size="sm" onClick={() => setSelectedId(null)}>
                Close
              </Button>
            </div>
            {executions.filter((item) => item.id === selectedId).map((item) => (
              <div key={item.id} className="space-y-3 text-sm text-foreground/85">
                <p><span className="font-semibold">Prompt:</span> {item.prompt}</p>
                <p><span className="font-semibold">Response:</span> {item.response}</p>
                <p><span className="font-semibold">Execution Time:</span> {item.executionTime}</p>
                <p><span className="font-semibold">Created:</span> {item.createdAt}</p>
                <p><span className="font-semibold">Status:</span> {item.status}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
