import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bell, Bot, Check } from "lucide-react";

export default function NotificationsPanel() {
  const notifications = [
    {
      icon: Bot,
      iconBg: "bg-primary/20",
      iconColor: "text-primary",
      title: "Agent Deployed",
      description: "Content Generator agent has been successfully deployed.",
      time: "2 minutes ago",
    },
    {
      icon: Check,
      iconBg: "bg-accent/20",
      iconColor: "text-accent",
      title: "Task Completed",
      description: "Research task on AI market trends finished.",
      time: "15 minutes ago",
    },
    {
      icon: Bot,
      iconBg: "bg-secondary/20",
      iconColor: "text-secondary",
      title: "Agent Status",
      description: "Data Analyst agent went offline due to inactivity.",
      time: "1 hour ago",
    },
    {
      icon: Bell,
      iconBg: "bg-muted/20",
      iconColor: "text-muted",
      title: "System Update",
      description: "New version of the platform is available.",
      time: "3 hours ago",
    },
  ];

  return (
    <Card className="h-full">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-semibold">Notifications Panel</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {notifications.map((notif, index) => (
          <div key={index} className="flex items-start gap-3 p-3 rounded-lg border border-background/50 hover:bg-background/30 transition-colors">
            <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${notif.iconBg} shrink-0`}>
              {notif.icon && <notif.icon className={`h-4 w-4 ${notif.iconColor}`} />}
            </div>
            <div className="flex-1 space-y-1">
              <p className="text-sm font-medium text-foreground/90">{notif.title}</p>
              <p className="text-xs text-muted">{notif.description}</p>
              <p className="text-xs text-muted/60">{notif.time}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}