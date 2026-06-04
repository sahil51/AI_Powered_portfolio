import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AnalyticsChartCardProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

export default function AnalyticsChartCard({ title, subtitle, children }: AnalyticsChartCardProps) {
  return (
    <Card className="rounded-3xl border border-white/10 p-5 h-full">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <CardTitle className="text-lg font-semibold text-foreground">{title}</CardTitle>
            {subtitle && <p className="text-sm text-muted mt-1">{subtitle}</p>}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-2">{children}</CardContent>
    </Card>
  );
}
