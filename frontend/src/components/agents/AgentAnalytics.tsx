import { AgentMetrics } from "@/lib/agent-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface AgentAnalyticsProps {
  metrics: AgentMetrics;
}

const metricItems = [
  { label: "Total Executions", key: "totalExecutions" },
  { label: "Success Rate", key: "successRate" },
  { label: "Avg Response Time", key: "averageResponseTime" },
  { label: "Cache Hit Ratio", key: "cacheHitRatio" },
] as const;

export default function AgentAnalytics({ metrics }: AgentAnalyticsProps) {
  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-foreground">Analytics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {metricItems.map((item) => (
            <div key={item.key} className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
              <p className="text-sm uppercase tracking-[0.25em] text-muted">{item.label}</p>
              <p className="mt-3 text-3xl font-semibold text-foreground">
                {item.key === "averageResponseTime" ? `${metrics[item.key]}s` : item.key === "successRate" || item.key === "cacheHitRatio" ? `${metrics[item.key]}%` : metrics[item.key]}
              </p>
            </div>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <p className="text-sm uppercase tracking-[0.25em] text-muted mb-4">Execution Trends</p>
            <div className="flex items-end gap-3 h-44">
              {metrics.executionTrend.map((value, index) => (
                <div key={index} className="flex-1 rounded-3xl bg-gradient-to-t from-primary to-accent" style={{ height: `${Math.max(value, 8) * 3}%` }}>
                  <span className="block text-center text-xs text-foreground/80 mt-2">{value}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-5">
            <p className="text-sm uppercase tracking-[0.25em] text-muted mb-4">Usage Graph</p>
            <div className="grid gap-3">
              {metrics.usageTrend.map((value, idx) => (
                <div key={idx} className="flex items-center gap-3 text-sm text-foreground/80">
                  <span className="w-8">{`W${idx + 1}`}</span>
                  <div className="h-2 w-full rounded-full bg-slate-900/60 overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-primary to-accent" style={{ width: `${Math.min(value * 5, 100)}%` }} />
                  </div>
                  <span className="w-10 text-right">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
