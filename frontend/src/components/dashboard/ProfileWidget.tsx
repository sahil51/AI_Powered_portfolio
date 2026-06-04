import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { User, Bot, Flame, Briefcase } from "lucide-react";

export default function ProfileWidget() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-semibold">Profile Widget</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* User Info */}
        <div className="flex items-center gap-4">
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-slate-900">
            <User className="h-4 w-4" />
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-foreground/90">Lucy AI</p>
            <p className="text-xs text-muted">Backend AI Engineer</p>
          </div>
        </div>

        {/* Skills */}
        <div className="space-y-3">
          <p className="text-sm font-medium text-foreground/90">Skills</p>
          <div className="flex flex-wrap gap-2">
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-primary/20 text-primary">Django</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-accent/20 text-accent">Python</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-secondary/20 text-secondary">Redis</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-muted/20 text-muted">Celery</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-primary/20 text-primary">PostgreSQL</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-accent/20 text-accent">AI Agents</span>
          </div>
        </div>

        {/* Experience */}
        <div className="space-y-3">
          <p className="text-sm font-medium text-foreground/90">Experience</p>
          <div className="space-y-2">
            <div className="flex items-start gap-3">
              <Briefcase className="h-4 w-4 text-muted shrink-0" />
              <div className="space-y-1">
                <p className="text-xs font-medium text-foreground/90">Senior AI Engineer</p>
                <p className="text-xs text-muted">Tech Corp • 2022 - Present</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Flame className="h-4 w-4 text-muted shrink-0" />
              <div className="space-y-1">
                <p className="text-xs font-medium text-foreground/90">AI Research Intern</p>
                <p className="text-xs text-muted">University Labs • 2020 - 2022</p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}