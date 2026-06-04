import { ActivityItem } from "@/lib/analytics-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ActivityFeedProps {
  items: ActivityItem[];
}

export default function ActivityFeed({ items }: ActivityFeedProps) {
  return (
    <Card className="rounded-3xl border border-white/10 p-5">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-semibold text-foreground">Activity feed</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {items.map((item) => (
          <div key={item.id} className="rounded-3xl border border-white/10 bg-slate-950/60 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-foreground">{item.title}</p>
                <p className="text-xs uppercase tracking-[0.3em] text-muted mt-1">{item.category}</p>
              </div>
              <Badge variant="outline">{item.badge}</Badge>
            </div>
            <p className="mt-3 text-sm text-muted">{item.detail}</p>
            <p className="mt-3 text-xs text-muted/80">{item.time}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
