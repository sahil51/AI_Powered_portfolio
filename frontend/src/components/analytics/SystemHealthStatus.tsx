import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StatusMetric } from "@/lib/analytics-data";

interface SystemHealthStatusProps {
  statuses: StatusMetric[];
}

const badgeVariants: Record<string, string> = {
  Healthy: "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20",
  Warning: "bg-amber-500/10 text-amber-300 border border-amber-500/20",
  Offline: "bg-rose-500/10 text-rose-300 border border-rose-500/20",
};

export default function SystemHealthStatus({ statuses }: SystemHealthStatusProps) {
  return (
    <Card className="rounded-3xl border border-white/10 p-5">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-semibold text-foreground">System health</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        {statuses.map((status) => (
          <div key={status.label} className="rounded-3xl border border-white/10 bg-slate-950/60 p-4 flex items-center justify-between gap-3">
            <div>
              <p className="text-sm text-muted uppercase tracking-[0.25em]">{status.label}</p>
              <p className="mt-2 text-lg font-semibold text-foreground">{status.value}</p>
            </div>
            <Badge className={badgeVariants[status.status]}>{status.status}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
