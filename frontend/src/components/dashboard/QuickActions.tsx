import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Bot, FileText, Cpu, BarChart2 } from "lucide-react";

export default function QuickActions() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-semibold">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button
          variant="outline"
          className="w-full flex items-center justify-start gap-3"
          onClick={() => alert("Create Agent")}
        >
          <Bot className="h-4 w-4" />
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground/90">Create Agent</p>
            <p className="text-xs text-muted">Build a new AI agent</p>
          </div>
        </Button>

        <Button
          variant="outline"
          className="w-full flex items-center justify-start gap-3"
          onClick={() => alert("Create Research Task")}
        >
          <FileText className="h-4 w-4" />
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground/90">Create Research Task</p>
            <p className="text-xs text-muted">Start a new research project</p>
          </div>
        </Button>

        <Button
          variant="outline"
          className="w-full flex items-center justify-start gap-3"
          onClick={() => alert("Open AI Assistant")}
        >
          <Cpu className="h-4 w-4" />
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground/90">Open AI Assistant</p>
            <p className="text-xs text-muted">Chat with Lucy AI</p>
          </div>
        </Button>

        <Button
          variant="outline"
          className="w-full flex items-center justify-start gap-3"
          onClick={() => alert("Generate Report")}
        >
          <BarChart2 className="h-4 w-4" />
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground/90">Generate Report</p>
            <p className="text-xs text-muted">Create analytics report</p>
          </div>
        </Button>
      </CardContent>
    </Card>
  );
}