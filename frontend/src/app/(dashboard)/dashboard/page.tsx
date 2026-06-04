"use client";

import * as React from "react";
import { Search, Bell, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

import StatsCards from "@/components/dashboard/StatsCards";
import Charts from "@/components/dashboard/Charts";
import Widgets from "@/components/dashboard/Widgets";
import QuickActions from "@/components/dashboard/QuickActions";
import NotificationsPanel from "@/components/dashboard/NotificationsPanel";
import ProfileWidget from "@/components/dashboard/ProfileWidget";

export default function DashboardPage() {
  const [searchQuery, setSearchQuery] = React.useState("");

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-col gap-4 mb-6">
        <div className="glass-panel rounded-3xl border border-white/10 p-6">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge className="rounded-full bg-violet-500/10 text-violet-200 border border-violet-500/20">Premium AI SaaS</Badge>
                <Badge className="rounded-full bg-white/5 text-slate-200 border border-white/10">Realtime-ready</Badge>
              </div>
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-primary/80">Command Center</p>
                <h1 className="mt-2 text-3xl sm:text-4xl font-bold text-foreground">Welcome back, Lucy AI</h1>
              </div>
              <p className="max-w-2xl text-sm leading-6 text-muted">
                Monitor your projects, agents, analytics, and research workflows with a premium glassmorphism dashboard built for AI teams.
              </p>
            </div>

            <div className="grid w-full gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="glass-panel rounded-3xl border border-white/10 p-4 text-center">
                <p className="text-sm uppercase tracking-[0.3em] text-muted">Live Agents</p>
                <p className="mt-3 text-3xl font-bold text-foreground">5</p>
              </div>
              <div className="glass-panel rounded-3xl border border-white/10 p-4 text-center">
                <p className="text-sm uppercase tracking-[0.3em] text-muted">Tasks Today</p>
                <p className="mt-3 text-3xl font-bold text-foreground">12</p>
              </div>
              <div className="glass-panel rounded-3xl border border-white/10 p-4 text-center">
                <p className="text-sm uppercase tracking-[0.3em] text-muted">AI Score</p>
                <p className="mt-3 text-3xl font-bold text-foreground">98%</p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="glass-panel rounded-3xl border border-white/10 p-4 flex-1 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2">
              <p className="text-sm uppercase tracking-[0.3em] text-muted">Dashboard home</p>
              <h2 className="text-xl font-semibold text-foreground">Overview and quick access</h2>
            </div>
            <div className="w-full sm:w-80">
              <Input
                type="text"
                placeholder="Search projects, agents, research..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full"
                icon={<Search className="w-4 h-4" />}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="relative">
              <Bell className="h-4 w-4" />
              <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-primary text-[10px] font-bold flex items-center justify-center text-white">
                3
              </span>
            </Button>
            <Button variant="ghost" size="sm">
              <User className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 lg:col-span-8">
            <div className="grid gap-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <StatsCards />
              </div>
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                <Charts />
              </div>
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <Widgets />
              </div>
            </div>
          </div>

          <div className="col-span-12 lg:col-span-4">
            <div className="grid gap-6">
              <QuickActions />
              <NotificationsPanel />
              <ProfileWidget />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
