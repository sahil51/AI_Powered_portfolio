import { ResearchTask } from "@/lib/research-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Share2 } from "lucide-react";

export interface ResearchResultProps {
  task: ResearchTask;
}

export default function ResearchResult({ task }: ResearchResultProps) {
  const handleDownload = () => {
    alert(`Downloading PDF report: research_report_${task.id}.pdf`);
  };

  const handleShare = () => {
    alert(`Generating secure share link for report ${task.id}...`);
  };

  return (
    <Card className="glass-panel rounded-3xl border border-white/10">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4">
        <div>
          <CardTitle className="text-xl font-semibold text-foreground">Generated Result</CardTitle>
        </div>
        <div className="flex items-center gap-2 mt-2 sm:mt-0">
          <Button variant="outline" size="sm" onClick={handleDownload} className="gap-2">
            <Download className="w-4 h-4" /> Download PDF
          </Button>
          <Button variant="primary" size="sm" onClick={handleShare} className="gap-2">
            <Share2 className="w-4 h-4" /> Share Report
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-3xl border border-border/50 bg-slate-950/50 p-6 text-foreground">
          <p className="whitespace-pre-line text-sm leading-7">{task.result}</p>
        </div>
      </CardContent>
    </Card>
  );
}
