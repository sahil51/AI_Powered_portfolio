"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ResearchStats as ResearchStatsType } from "@/lib/research-data";

export interface ResearchStatsProps {
  stats: ResearchStatsType;
}

const statClasses = [
  "from-primary via-violet-500 to-fuchsia-500",
  "from-indigo-500 via-violet-500 to-fuchsia-500",
  "from-emerald-500 via-cyan-500 to-primary",
  "from-red-500 via-orange-500 to-yellow-500",
];

export default function ResearchStats({ stats }: ResearchStatsProps) {
  const items = [
    { label: "Total Tasks", value: stats.totalTasks },
    { label: "Running Tasks", value: stats.runningTasks },
    { label: "Completed Tasks", value: stats.completedTasks },
    { label: "Failed Tasks", value: stats.failedTasks },
  ];

  return (
    <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item, index) => (
        <Card key={item.label} className="glass-panel rounded-3xl border border-white/10 p-5 overflow-hidden">
          <div className={`absolute -right-12 -top-12 h-32 w-32 rounded-full bg-gradient-to-br ${statClasses[index]} opacity-20`} />
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold text-foreground">{item.label}</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-4xl font-bold text-foreground">{item.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
