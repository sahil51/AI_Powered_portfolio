"use client";

import { SavedReport } from "@/lib/knowledge-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface SavedReportsProps {
  reports: SavedReport[];
}

export default function SavedReports({ reports }: SavedReportsProps) {
  return (
    <Card className="rounded-3xl border border-white/10 p-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Saved Reports</CardTitle>
        <p className="text-sm text-muted">Access generated research and recruiter reports</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {reports.map((r) => (
          <div key={r.id} className="rounded-2xl border border-white/5 p-3 flex items-center justify-between">
            <div>
              <p className="font-semibold text-foreground">{r.title}</p>
              <p className="text-xs text-muted">{r.createdAt}</p>
            </div>
            <div className="flex gap-2">
              <Button variant="ghost">Open</Button>
              <Button variant="outline">Download</Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}