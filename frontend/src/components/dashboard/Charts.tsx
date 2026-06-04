import * as React from "react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";

export default function Charts() {
  const chartData = [
    {
      title: "Task Completion Analytics",
      data: [30, 45, 25, 50, 35, 60],
    },
    {
      title: "Agent Usage Analytics",
      data: [20, 35, 30, 40, 25, 45],
    },
    {
      title: "AI Activity Analytics",
      data: [10, 20, 15, 25, 20, 30],
    },
  ];

  const labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];

  return (
    <div className="grid gap-6">
      {chartData.map((chart, index) => {
        const maxValue = Math.max(...chart.data);
        return (
          <Card key={index} className="h-full">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg font-semibold">{chart.title}</CardTitle>
            </CardHeader>
            <div className="flex flex-col gap-4 px-4 pb-4">
              <div className="flex items-end gap-3 h-44">
                {chart.data.map((value, idx) => (
                  <div key={idx} className="relative flex-1 flex flex-col items-center gap-2">
                    <span className="text-[11px] text-muted">{value}</span>
                    <div className="relative w-full h-full rounded-3xl bg-slate-900/50 overflow-hidden flex items-end">
                      <div
                        className="w-full rounded-t-3xl bg-gradient-to-t from-primary to-accent transition-all duration-300"
                        style={{ height: `${(value / maxValue) * 100}%` }}
                      />
                    </div>
                    <span className="text-[10px] uppercase tracking-[0.2em] text-muted/70">
                      {labels[idx]}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
