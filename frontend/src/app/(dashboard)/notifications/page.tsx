"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Bell, 
  Trash2, 
  Check, 
  Cpu, 
  FlaskConical, 
  Calendar, 
  AlertCircle 
} from "lucide-react";

interface NotificationItem {
  id: string;
  title: string;
  description: string;
  type: "task" | "agent" | "system" | "meeting";
  time: string;
  unread: boolean;
  mention: boolean;
}

const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "notif-1",
    title: "Research Task 'AI Trends 2026' Completed",
    description: "The Research Agent generated the final PDF intelligence analysis report. Token cost: 1,240.",
    type: "task",
    time: "2m ago",
    unread: true,
    mention: false
  },
  {
    id: "notif-2",
    title: "New Agent 'Client Assist' Registered",
    description: "Custom system agent created and activated using Gemini-1.5-pro core settings.",
    type: "agent",
    time: "1h ago",
    unread: true,
    mention: true
  },
  {
    id: "notif-3",
    title: "System Warning: Token Threshold Alert",
    description: "Gemini monthly consumption tier reached 85% capacity limits. Consider upgrading tier.",
    type: "system",
    time: "4h ago",
    unread: false,
    mention: false
  },
  {
    id: "notif-4",
    title: "Interview Meeting Scheduled",
    description: "Scheduled introductory video conference with Recruiter Alexander Mercer.",
    type: "meeting",
    time: "Yesterday",
    unread: false,
    mention: true
  }
];

export default function NotificationsPage() {
  const [notifications, setNotifications] = React.useState<NotificationItem[]>(INITIAL_NOTIFICATIONS);
  const [filterTab, setFilterTab] = React.useState<"all" | "unread" | "mentions">("all");

  const filteredItems = React.useMemo(() => {
    return notifications.filter((item) => {
      if (filterTab === "unread") return item.unread;
      if (filterTab === "mentions") return item.mention;
      return true;
    });
  }, [notifications, filterTab]);

  const unreadCount = notifications.filter((x) => x.unread).length;

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((item) => ({ ...item, unread: false })));
  };

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((item) => (item.id === id ? { ...item, unread: false } : item))
    );
  };

  const deleteNotification = (id: string) => {
    setNotifications((prev) => prev.filter((item) => item.id !== id));
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "task":
        return <FlaskConical className="w-4 h-4 text-primary" />;
      case "agent":
        return <Cpu className="w-4 h-4 text-accent" />;
      case "meeting":
        return <Calendar className="w-4 h-4 text-emerald-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-rose-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel rounded-3xl border border-white/10 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-primary/80">Alerts System</p>
          <h1 className="text-3xl font-bold text-foreground">Notifications</h1>
          <p className="max-w-2xl text-sm text-muted mt-2">
            Review live agent task updates, scheduled meetings telemetry, and system limit alert flags.
          </p>
        </div>

        {unreadCount > 0 && (
          <Button variant="outline" size="sm" onClick={markAllAsRead} className="gap-2 shrink-0">
            <Check className="w-4 h-4" />
            Mark all as read
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/5 pb-2">
        <button
          onClick={() => setFilterTab("all")}
          className={`text-sm font-semibold px-4 py-2 border-b-2 transition-all ${
            filterTab === "all" ? "border-primary text-primary" : "border-transparent text-muted hover:text-foreground"
          }`}
        >
          All Notifications ({notifications.length})
        </button>
        <button
          onClick={() => setFilterTab("unread")}
          className={`text-sm font-semibold px-4 py-2 border-b-2 transition-all ${
            filterTab === "unread" ? "border-primary text-primary" : "border-transparent text-muted hover:text-foreground"
          }`}
        >
          Unread ({unreadCount})
        </button>
        <button
          onClick={() => setFilterTab("mentions")}
          className={`text-sm font-semibold px-4 py-2 border-b-2 transition-all ${
            filterTab === "mentions" ? "border-primary text-primary" : "border-transparent text-muted hover:text-foreground"
          }`}
        >
          Mentions
        </button>
      </div>

      {/* List */}
      <Card className="glass-panel rounded-3xl border border-white/10 overflow-hidden">
        <CardContent className="divide-y divide-white/5 p-0">
          {filteredItems.length > 0 ? (
            filteredItems.map((item) => (
              <div
                key={item.id}
                className={`p-5 flex gap-4 transition-colors items-start hover:bg-slate-900/20 ${
                  item.unread ? "bg-slate-950/20" : ""
                }`}
              >
                {/* Icon wrapper */}
                <div className={`p-2.5 rounded-xl border shrink-0 ${
                  item.unread ? "bg-primary/10 border-primary/20" : "bg-slate-900 border-white/5"
                }`}>
                  {getIcon(item.type)}
                </div>

                {/* Details */}
                <div className="flex-grow min-w-0 space-y-1">
                  <div className="flex items-center justify-between gap-4">
                    <h3 className={`text-sm text-foreground truncate ${item.unread ? "font-bold" : "font-semibold"}`}>
                      {item.title}
                    </h3>
                    <span className="text-xs text-muted font-mono shrink-0">{item.time}</span>
                  </div>
                  <p className="text-xs text-muted leading-relaxed max-w-3xl">{item.description}</p>
                  
                  {/* Indicators row */}
                  <div className="flex flex-wrap gap-2 pt-1">
                    {item.unread && (
                      <Badge className="bg-primary/20 text-primary border border-primary/30 text-[9px] rounded-full">
                        New
                      </Badge>
                    )}
                    {item.mention && (
                      <Badge className="bg-accent/20 text-accent border border-accent/30 text-[9px] rounded-full">
                        Mention
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Quick controls */}
                <div className="flex items-center gap-1 shrink-0 ml-2">
                  {item.unread && (
                    <button
                      onClick={() => markAsRead(item.id)}
                      className="p-1.5 rounded-lg text-muted hover:text-foreground hover:bg-white/5"
                      title="Mark as read"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => deleteNotification(item.id)}
                    className="p-1.5 rounded-lg text-muted hover:text-rose-400 hover:bg-white/5"
                    title="Dismiss"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="p-12 text-center">
              <Bell className="w-10 h-10 text-muted mx-auto mb-3" />
              <p className="text-sm font-semibold text-foreground">All clear</p>
              <p className="text-xs text-muted mt-0.5">No notifications match the active filter criteria.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
