"use client";

import * as React from "react";
import {
  Activity,
  BarChart3,
  Database,
  LineChart,
  PieChart,
  Server,
  Sparkles,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import AnalyticsMetricCards from "@/components/analytics/AnalyticsMetricCards";
import AnalyticsChartCard from "@/components/analytics/AnalyticsChartCard";
import SystemHealthStatus from "@/components/analytics/SystemHealthStatus";
import ActivityFeed from "@/components/analytics/ActivityFeed";
import {
  TOP_METRICS,
  AGENT_USAGE,
  EXECUTION_TRENDS,
  TOP_AGENTS,
  TASK_METRICS,
  TASK_COMPLETION_RATE,
  TASK_GROWTH,
  CACHE_METRICS,
  CACHE_PERFORMANCE,
  RESPONSE_TIME_IMPROVEMENT,
  GEMINI_METRICS,
  SYSTEM_STATUS,
  ACTIVITY_FEED,
} from "@/lib/analytics-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const pieGradient = () => {
  const total = AGENT_USAGE.reduce((sum, item) => sum + item.value, 0);
  let current = 0;
  const segments = AGENT_USAGE.map((item) => {
    const next = current + (item.value / total) * 360;
    const segment = `${item.color} ${current}deg ${next}deg`;
    current = next;
    return segment;
  });
  return `conic-gradient(${segments.join(", ")})`;
};

const completionGradient = () => {
  const total = TASK_COMPLETION_RATE.reduce((sum, item) => sum + item.value, 0);
  let current = 0;
  const palette = ["#8b5cf6", "#38bdf8", "#34d399", "#fb7185"];
  const segments = TASK_COMPLETION_RATE.map((item, index) => {
    const next = current + (item.value / total) * 360;
    const segment = `${palette[index]} ${current}deg ${next}deg`;
    current = next;
    return segment;
  });
  return `conic-gradient(${segments.join(", ")})`;
};

const AnalyticsPage = () => {
  return (
    <div className="space-y-8 pb-16">
      <div className="glass-panel rounded-3xl border border-white/10 p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <p className="text-sm uppercase tracking-[0.3em] text-primary/80">AI Analytics Center</p>
            <h1 className="text-3xl sm:text-4xl font-bold text-foreground">Lucy AI analytics dashboard</h1>
            <p className="max-w-2xl text-sm leading-7 text-muted">
              Explore enterprise-grade performance insights across your multi-agent platform, cache efficiency, system health, and task operations.
            </p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-4 shadow-lg shadow-black/20">
            <div className="flex items-center gap-3 text-sm text-muted">
              <Database className="w-5 h-5 text-primary" />
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-muted">Snapshot</p>
                <p className="text-base font-semibold text-foreground">Real-time enterprise insights</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <section className="space-y-6">
        <AnalyticsMetricCards metrics={TOP_METRICS} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="grid gap-6">
          <div className="grid gap-6 lg:grid-cols-3">
            <AnalyticsChartCard title="Agent Usage Distribution" subtitle="Active agent share by category">
              <div className="flex items-center gap-6">
                <div
                  className="relative h-48 w-48 rounded-full border border-white/10"
                  style={{ backgroundImage: pieGradient() }}
                >
                  <div className="absolute inset-10 rounded-full bg-slate-950/95" />
                </div>
                <div className="grid gap-3">
                  {AGENT_USAGE.map((agent) => (
                    <div key={agent.label} className="flex items-center gap-3">
                      <span className="h-3 w-3 rounded-full" style={{ backgroundColor: agent.color }} />
                      <div>
                        <p className="text-sm text-foreground">{agent.label}</p>
                        <p className="text-xs text-muted">{agent.value}% of usage</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </AnalyticsChartCard>

            <AnalyticsChartCard title="Agent Execution Trends" subtitle="Weekly agent throughput">
              <div className="space-y-4">
                <div className="h-48 relative overflow-hidden rounded-3xl bg-slate-950/80 p-4">
                  <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-slate-950/90" />
                  <div className="absolute inset-x-0 bottom-0 h-px bg-white/10" />
                  <div className="absolute inset-y-0 right-0 w-px bg-white/10" />
                  <div className="relative flex h-full items-end justify-between gap-3">
                    {EXECUTION_TRENDS.map((point, index) => (
                      <div key={point.label} className="flex flex-col items-center gap-2">
                        <span className="text-xs text-muted">{point.label}</span>
                        <div className="h-full w-1/2 bg-gradient-to-t from-primary to-accent rounded-full" style={{ height: `${(point.value / 1600) * 100}%` }} />
                      </div>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3 text-sm text-muted">
                  <span>Mon - Sun execution volume</span>
                  <span className="col-span-2 text-right">Performance is stable across the week</span>
                </div>
              </div>
            </AnalyticsChartCard>

            <AnalyticsChartCard title="Most Active Agents" subtitle="Execution intensity ranking">
              <div className="space-y-4">
                {TOP_AGENTS.map((agent) => (
                  <div key={agent.label} className="grid grid-cols-[1fr_auto] items-center gap-4">
                    <div>
                      <p className="text-sm text-foreground">{agent.label}</p>
                      <div className="mt-2 h-2 rounded-full bg-slate-900/70">
                        <div className="h-full rounded-full bg-gradient-to-r from-primary to-accent" style={{ width: `${(agent.value / 28) * 100}%` }} />
                      </div>
                    </div>
                    <span className="text-sm font-semibold text-foreground">{agent.value}</span>
                  </div>
                ))}
              </div>
            </AnalyticsChartCard>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                {TASK_METRICS.map((metric) => (
                  <div key={metric.label} className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                    <p className="text-sm uppercase tracking-[0.3em] text-muted">{metric.label}</p>
                    <p className="mt-3 text-2xl font-semibold text-foreground">{metric.value}</p>
                  </div>
                ))}
              </div>
            </div>

            <AnalyticsChartCard title="Task Completion Rate" subtitle="Task state distribution">
              <div className="flex items-center gap-5">
                <div
                  className="relative h-40 w-40 rounded-full border border-white/10"
                  style={{ backgroundImage: completionGradient() }}
                >
                  <div className="absolute inset-12 rounded-full bg-slate-950/95" />
                </div>
                <div className="space-y-3">
                  {TASK_COMPLETION_RATE.map((item, index) => (
                    <div key={item.label} className="flex items-center justify-between gap-3">
                      <span className="text-sm text-muted">{item.label}</span>
                      <span className="text-sm font-semibold text-foreground">{item.value}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </AnalyticsChartCard>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <AnalyticsChartCard title="Task Growth" subtitle="Weekly growth curve">
              <div className="space-y-4">
                <div className="h-44 grid grid-cols-4 gap-3 items-end">
                  {TASK_GROWTH.map((point) => (
                    <div key={point.label} className="space-y-2">
                      <div className="h-full rounded-3xl bg-gradient-to-t from-violet-500 to-fuchsia-500" style={{ height: `${(point.value / 1050) * 100}%` }} />
                      <p className="text-xs text-muted text-center">{point.label}</p>
                    </div>
                  ))}
                </div>
                <div className="text-sm text-muted">Strong task growth shows adoption across your multi-agent workflows.</div>
              </div>
            </AnalyticsChartCard>

            <AnalyticsChartCard title="Task Status Distribution" subtitle="Current task backlog">
              <div className="space-y-4">
                {TASK_COMPLETION_RATE.map((item) => (
                  <div key={item.label}>
                    <div className="flex items-center justify-between text-sm text-muted">
                      <span>{item.label}</span>
                      <span>{item.value}%</span>
                    </div>
                    <div className="mt-2 h-3 rounded-full bg-slate-900/70">
                      <div className="h-full rounded-full bg-gradient-to-r from-primary to-accent" style={{ width: `${item.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </AnalyticsChartCard>
          </div>
        </div>

        <aside className="space-y-6">
          <AnalyticsChartCard title="Cache analytics" subtitle="Redis and response time insights">
            <div className="grid gap-4">
              {CACHE_METRICS.map((metric) => (
                <div key={metric.label} className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
                  <p className="text-sm text-muted">{metric.label}</p>
                  <p className="mt-3 text-2xl font-semibold text-foreground">{metric.value}</p>
                </div>
              ))}
            </div>
          </AnalyticsChartCard>

          <AnalyticsChartCard title="Cache performance" subtitle="Average hit and miss timings">
            <div className="space-y-4">
              {CACHE_PERFORMANCE.map((metric) => (
                <div key={metric.label} className="space-y-2">
                  <div className="flex items-center justify-between text-sm text-muted">
                    <span>{metric.label}</span>
                    <span className="font-semibold text-foreground">{metric.value}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-900/70">
                    <div className="h-full rounded-full bg-gradient-to-r from-primary to-accent" style={{ width: `${Math.min((metric.value / 700) * 100, 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </AnalyticsChartCard>

          <AnalyticsChartCard title="Response time improvement" subtitle="Average latency trend">
            <div className="space-y-4">
              <div className="h-44 grid grid-cols-6 gap-2 items-end">
                {RESPONSE_TIME_IMPROVEMENT.map((point) => (
                  <div key={point.label} className="space-y-2">
                    <div className="h-full rounded-3xl bg-gradient-to-t from-primary to-violet-500" style={{ height: `${(point.value / 540) * 100}%` }} />
                    <p className="text-[10px] uppercase tracking-[0.2em] text-muted text-center">{point.label}</p>
                  </div>
                ))}
              </div>
              <div className="text-sm text-muted">Latency improvements driven by cache, model batching, and execution optimizations.</div>
            </div>
          </AnalyticsChartCard>
        </aside>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="grid gap-6 lg:grid-cols-2">
          {GEMINI_METRICS.map((metric) => (
            <Card key={metric.label} className="rounded-3xl border border-white/10 p-5">
              <CardHeader className="pb-4">
                <p className="text-sm uppercase tracking-[0.3em] text-muted">{metric.label}</p>
                <CardTitle className="mt-3 text-3xl text-foreground">{metric.value}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted">Gemini analytics across AI consumption and cost management.</p>
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="space-y-6">
          <SystemHealthStatus statuses={SYSTEM_STATUS} />
          <ActivityFeed items={ACTIVITY_FEED} />
        </div>
      </section>
    </div>
  );
};

export default AnalyticsPage;
