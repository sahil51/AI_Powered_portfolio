import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TopMetric } from "@/lib/analytics-data";

interface AnalyticsMetricCardsProps {
  metrics: TopMetric[];
}

const trendClasses: Record<string, string> = {
  up: "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20",
  down: "bg-rose-500/10 text-rose-300 border border-rose-500/20",
  flat: "bg-slate-700/10 text-muted border border-white/10",
};

export default function AnalyticsMetricCards({ metrics }: AnalyticsMetricCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {metrics.map((metric) => (
        <Card key={metric.label} className="rounded-3xl border border-white/10 p-5">
          <CardHeader className="pb-4">
            <p className="text-sm uppercase tracking-[0.3em] text-muted">{metric.label}</p>
            <CardTitle className="text-3xl mt-3 text-foreground">{metric.value}</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex items-center justify-between gap-4">
              <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${trendClasses[metric.trend]}`}>
                {metric.delta}
              </span>
              <p className="text-sm text-muted">{metric.detail}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
