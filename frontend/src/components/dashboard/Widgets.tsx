import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, BarChart2, Bot, MapPin } from "lucide-react";

export default function Widgets() {
  return (
    <div className="grid gap-6">
      {/* Recent Activity */}
      <Card className="h-full">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="h-3 w-3 rounded-full bg-primary/20 shrink-0" />
            <div className="flex-1 space-y-1">
              <p className="text-sm font-medium text-foreground/90">Deployed new agent: Content Generator</p>
              <p className="text-xs text-muted">2 minutes ago</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="h-3 w-3 rounded-full bg-accent/20 shrink-0" />
            <div className="flex-1 space-y-1">
              <p className="text-sm font-medium text-foreground/90">Research task completed: Market trends analysis</p>
              <p className="text-xs text-muted">15 minutes ago</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="h-3 w-3 rounded-full bg-secondary/20 shrink-0" />
            <div className="flex-1 space-y-1">
              <p className="text-sm font-medium text-foreground/90">Meeting scheduled: Team sync</p>
              <p className="text-xs text-muted">1 hour ago</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Latest Reports */}
      <Card className="h-full">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold">Latest Reports</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <FileText className="h-4 w-4 text-muted shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground/90">AI Market Research Q2 2026</p>
              <p className="text-xs text-muted">Updated today</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <FileText className="h-4 w-4 text-muted shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground/90">Agent Performance Report</p>
              <p className="text-xs text-muted">Updated yesterday</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <FileText className="h-4 w-4 text-muted shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground/90">Project Milestone Tracker</p>
              <p className="text-xs text-muted">Updated 2 days ago</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Agent Status */}
      <Card className="h-full">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold">Agent Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-3">
            <Bot className="h-4 w-4 text-primary shrink-0" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground/90">Research Agent</p>
              <p className="text-xs text-muted">Online • 2 tasks running</p>
            </div>
          </div>
          <div className="w-full h-0.5 bg-border/50 my-4" />
          <div className="flex items-center gap-3">
            <Bot className="h-4 w-4 text-accent shrink-0" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground/90">Content Generator</p>
              <p className="text-xs text-muted">Online • Idle</p>
            </div>
          </div>
          <div className="w-full h-0.5 bg-border/50 my-4" />
          <div className="flex items-center gap-3">
            <Bot className="h-4 w-4 text-muted/50 shrink-0" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground/90">Data Analyst</p>
              <p className="text-xs text-muted">Offline</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Upcoming Meetings */}
      <Card className="h-full">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold">Upcoming Meetings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="border-l-2 border-primary/20 pl-3 mb-4">
            <p className="text-sm font-medium text-foreground/90">Team Sync</p>
            <p className="text-xs text-muted">Today, 2:00 PM</p>
          </div>
          <div className="border-l-2 border-accent/20 pl-3 mb-4">
            <p className="text-sm font-medium text-foreground/90">Client Review</p>
            <p className="text-xs text-muted">Tomorrow, 10:00 AM</p>
          </div>
          <div className="border-l-2 border-secondary/20 pl-3">
            <p className="text-sm font-medium text-foreground/90">Project Planning</p>
            <p className="text-xs text-muted">Thursday, 3:00 PM</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}