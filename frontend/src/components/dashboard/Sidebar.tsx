"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  Bot,
  FlaskConical,
  BarChart2,
  BookOpen,
  Calendar,
  MessageCircle,
  Settings,
  User,
  ChevronLeft,
  ChevronRight,
  UserCheck,
} from "lucide-react";

const sidebarItems = [
  { name: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
  { name: "Recruiter Portal", icon: UserCheck, href: "/recruiter" },
  { name: "Projects", icon: FileText, href: "/projects" },
  { name: "Agents", icon: Bot, href: "/agents" },
  { name: "Research", icon: FlaskConical, href: "/research" },
  { name: "Analytics", icon: BarChart2, href: "/analytics" },
  { name: "Knowledge Base", icon: BookOpen, href: "/knowledge" },
  { name: "Meetings", icon: Calendar, href: "/meetings" },
  { name: "Messages", icon: MessageCircle, href: "/messages" },
  { name: "Settings", icon: Settings, href: "/settings" },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = React.useState(false);
  const pathname = usePathname();

  return (
    <aside
      className={`flex flex-col h-screen bg-slate-950/60 backdrop-blur-lg border-r border-border transition-all duration-300 overflow-y-auto ${
        collapsed ? "w-16" : "w-64"
      }`}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between p-4 border-b border-border/30">
        {!collapsed && (
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-slate-950 font-bold shadow-md">
              <Bot className="w-3.5 h-3.5 text-slate-950" />
            </div>
            <span className="text-lg font-black tracking-tight text-foreground">
              Lucy <span className="text-accent">AI</span>
            </span>
          </Link>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg text-muted hover:text-foreground hover:bg-white/5 transition-colors"
          aria-label="Toggle sidebar"
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 pt-4 px-2">
        <ul className="space-y-1">
          {sidebarItems.map((item) => {
            const Icon = item.icon;
            // Check if active: exact match or starts with path (e.g. /agents/create is active for /agents)
            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? "text-foreground bg-primary/10 border border-primary/20"
                      : "text-muted hover:text-foreground hover:bg-white/5"
                  }`}
                >
                  <Icon className="w-4.5 h-4.5 shrink-0" />
                  {!collapsed && <span>{item.name}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Bottom Profile Section */}
      <div className="border-t border-border/30 p-4">
        <Link href="/profile" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-slate-900 shrink-0">
            <User className="w-4 h-4" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <p className="text-sm font-semibold text-foreground leading-none">Lucy AI</p>
              <p className="text-xs text-muted leading-none mt-1">Profile Hub</p>
            </div>
          )}
        </Link>
      </div>
    </aside>
  );
}