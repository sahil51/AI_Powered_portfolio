"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  Settings, 
  ShieldCheck, 
  Bell, 
  Cpu, 
  CreditCard, 
  Eye, 
  EyeOff, 
  Plus, 
  Trash2,
  AlertTriangle
} from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = React.useState<"general" | "security" | "notifications" | "integrations" | "billing">("general");

  // General Settings
  const [theme, setTheme] = React.useState("dark");
  const [analyticsInterval, setAnalyticsInterval] = React.useState("7d");

  // Security Settings
  const [apiKey, setApiKey] = React.useState("sk-gemini-xxxx-xxxx-xxxx-431a");
  const [showApiKey, setShowApiKey] = React.useState(false);
  const [currentPassword, setCurrentPassword] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");

  // Notification Settings
  const [notifyOnTaskComplete, setNotifyOnTaskComplete] = React.useState(true);
  const [notifyOnAgentStart, setNotifyOnAgentStart] = React.useState(true);
  const [notifyOnWarning, setNotifyOnWarning] = React.useState(false);
  const [emailDigest, setEmailDigest] = React.useState(true);

  // Integrations Settings
  const [redisUrl, setRedisUrl] = React.useState("redis://127.0.0.1:6379/0");
  const [celeryBroker, setCeleryBroker] = React.useState("redis://127.0.0.1:6379/1");
  const [geminiModel, setGeminiModel] = React.useState("gemini-1.5-pro");

  // Billing Settings
  const currentPlan = {
    name: "Enterprise Agent Pool",
    price: "$99/mo",
    renewal: "July 12, 2026",
    usage: {
      tokens: "85,420 / 500,000",
      agents: "6 / 15",
      tasks: "142 / Unlimited"
    }
  };

  const invoices = [
    { id: "INV-902", date: "May 12, 2026", amount: "$99.00", status: "Paid" },
    { id: "INV-841", date: "Apr 12, 2026", amount: "$99.00", status: "Paid" },
    { id: "INV-780", date: "Mar 12, 2026", amount: "$99.00", status: "Paid" }
  ];

  const handleSave = () => {
    alert("Configuration parameters saved successfully!");
  };

  const handleGenerateKey = () => {
    setApiKey("sk-gemini-" + Math.random().toString(36).substring(2, 8) + "-" + Math.random().toString(36).substring(2, 8) + "-431a");
    alert("New custom API Auth token generated successfully!");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel rounded-3xl border border-white/10 p-6">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-primary/80">Settings Core</p>
          <h1 className="text-3xl font-bold text-foreground">Global Settings</h1>
          <p className="max-w-2xl text-sm text-muted mt-2">
            Configure system integrations, API tokens, notification triggers, and active billing subscription tiers.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-6 items-start">
        {/* Navigation Sidebar Tabs */}
        <aside className="flex flex-col gap-1 p-2 rounded-2xl bg-slate-950/60 border border-white/5">
          <button
            onClick={() => setActiveTab("general")}
            className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold rounded-xl text-left transition ${
              activeTab === "general" ? "bg-primary/10 text-primary border border-primary/20" : "text-muted hover:text-foreground hover:bg-white/5"
            }`}
          >
            <Settings className="w-4 h-4" />
            General Config
          </button>
          <button
            onClick={() => setActiveTab("security")}
            className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold rounded-xl text-left transition ${
              activeTab === "security" ? "bg-primary/10 text-primary border border-primary/20" : "text-muted hover:text-foreground hover:bg-white/5"
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            Security & Keys
          </button>
          <button
            onClick={() => setActiveTab("notifications")}
            className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold rounded-xl text-left transition ${
              activeTab === "notifications" ? "bg-primary/10 text-primary border border-primary/20" : "text-muted hover:text-foreground hover:bg-white/5"
            }`}
          >
            <Bell className="w-4 h-4" />
            Notification Toggles
          </button>
          <button
            onClick={() => setActiveTab("integrations")}
            className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold rounded-xl text-left transition ${
              activeTab === "integrations" ? "bg-primary/10 text-primary border border-primary/20" : "text-muted hover:text-foreground hover:bg-white/5"
            }`}
          >
            <Cpu className="w-4 h-4" />
            AI & Infrastructure
          </button>
          <button
            onClick={() => setActiveTab("billing")}
            className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold rounded-xl text-left transition ${
              activeTab === "billing" ? "bg-primary/10 text-primary border border-primary/20" : "text-muted hover:text-foreground hover:bg-white/5"
            }`}
          >
            <CreditCard className="w-4 h-4" />
            Billing & Invoices
          </button>
        </aside>

        {/* Tab content */}
        <main className="space-y-6">
          
          {/* TAB: GENERAL */}
          {activeTab === "general" && (
            <Card className="glass-panel rounded-3xl border border-white/10">
              <CardHeader>
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                  <Settings className="w-5 h-5 text-primary" />
                  General Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-foreground/80 block">Active UI Theme</label>
                    <select
                      value={theme}
                      onChange={(e) => setTheme(e.target.value)}
                      className="w-full rounded-2xl bg-slate-950 border border-white/10 p-3 text-sm text-foreground focus:outline-none focus:border-primary/50"
                    >
                      <option value="dark">Premium Dark (Default)</option>
                      <option value="navy">Deep Space Navy</option>
                      <option value="light">Classic Light (Not Recommended)</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-foreground/80 block">Dashboard Telemetry Range</label>
                    <select
                      value={analyticsInterval}
                      onChange={(e) => setAnalyticsInterval(e.target.value)}
                      className="w-full rounded-2xl bg-slate-950 border border-white/10 p-3 text-sm text-foreground focus:outline-none focus:border-primary/50"
                    >
                      <option value="24h">Last 24 Hours</option>
                      <option value="7d">Last 7 Days (Stable)</option>
                      <option value="30d">Last 30 Days</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end pt-4 border-t border-white/5">
                  <Button variant="primary" onClick={handleSave}>
                    Save General Settings
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* TAB: SECURITY */}
          {activeTab === "security" && (
            <Card className="glass-panel rounded-3xl border border-white/10">
              <CardHeader>
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-accent" />
                  Security credentials & API key auth
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                
                {/* API Key */}
                <div className="space-y-3">
                  <div>
                    <h4 className="text-sm font-semibold text-foreground">Custom API Access Key</h4>
                    <p className="text-xs text-muted">Use this key to trigger agent pipelines programmatically via REST API requests.</p>
                  </div>
                  
                  <div className="relative">
                    <input
                      type={showApiKey ? "text" : "password"}
                      value={apiKey}
                      readOnly
                      className="w-full rounded-2xl bg-slate-950 border border-white/10 p-3.5 pr-24 font-mono text-sm text-accent focus:outline-none"
                    />
                    <div className="absolute right-2.5 top-2.5 flex items-center gap-1.5">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="py-1 px-2.5"
                      >
                        {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        onClick={handleGenerateKey}
                        className="py-1 px-2.5"
                      >
                        Rotate
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Password reset mock */}
                <div className="space-y-4 pt-4 border-t border-white/5">
                  <h4 className="text-sm font-semibold text-foreground">Modify Account Password</h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Input
                      label="Current Password"
                      type="password"
                      placeholder="••••••••"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                    />
                    <Input
                      label="New Password"
                      type="password"
                      placeholder="••••••••"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                    />
                  </div>
                  
                  <div className="flex justify-end pt-2">
                    <Button variant="outline" onClick={() => {
                      if (!currentPassword || !newPassword) {
                        alert("Please fill in current and new password fields.");
                        return;
                      }
                      alert("Password updated successfully!");
                      setCurrentPassword("");
                      setNewPassword("");
                    }}>
                      Update Password
                    </Button>
                  </div>
                </div>

              </CardContent>
            </Card>
          )}

          {/* TAB: NOTIFICATIONS */}
          {activeTab === "notifications" && (
            <Card className="glass-panel rounded-3xl border border-white/10">
              <CardHeader>
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                  <Bell className="w-5 h-5 text-primary" />
                  Telemetry notifications alerts
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="space-y-4">
                  <label className="flex items-start gap-3 p-3 rounded-2xl bg-slate-950/40 border border-white/5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifyOnTaskComplete}
                      onChange={(e) => setNotifyOnTaskComplete(e.target.checked)}
                      className="mt-1 w-4 h-4 text-primary bg-slate-900 border-white/10 focus:ring-primary rounded"
                    />
                    <div>
                      <span className="text-sm font-semibold text-foreground block">Research Task Completions</span>
                      <span className="text-xs text-muted">Receive a browser/dashboard toast popup when an active research task has generated its final PDF report.</span>
                    </div>
                  </label>

                  <label className="flex items-start gap-3 p-3 rounded-2xl bg-slate-950/40 border border-white/5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifyOnAgentStart}
                      onChange={(e) => setNotifyOnAgentStart(e.target.checked)}
                      className="mt-1 w-4 h-4 text-primary bg-slate-900 border-white/10 focus:ring-primary rounded"
                    />
                    <div>
                      <span className="text-sm font-semibold text-foreground block">Agent Execution Starts</span>
                      <span className="text-xs text-muted">Show indicator signals inside the dashboard immediately when an agent node triggers.</span>
                    </div>
                  </label>

                  <label className="flex items-start gap-3 p-3 rounded-2xl bg-slate-950/40 border border-white/5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={notifyOnWarning}
                      onChange={(e) => setNotifyOnWarning(e.target.checked)}
                      className="mt-1 w-4 h-4 text-primary bg-slate-900 border-white/10 focus:ring-primary rounded"
                    />
                    <div>
                      <span className="text-sm font-semibold text-foreground block">Token Limit Warnings</span>
                      <span className="text-xs text-muted">Trigger warnings when LLM token usage consumes 80% or more of the monthly quota.</span>
                    </div>
                  </label>

                  <label className="flex items-start gap-3 p-3 rounded-2xl bg-slate-950/40 border border-white/5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={emailDigest}
                      onChange={(e) => setEmailDigest(e.target.checked)}
                      className="mt-1 w-4 h-4 text-primary bg-slate-900 border-white/10 focus:ring-primary rounded"
                    />
                    <div>
                      <span className="text-sm font-semibold text-foreground block">Weekly Performance Digest</span>
                      <span className="text-xs text-muted">Email a weekly summary report highlighting recruiter visits and search token analytics.</span>
                    </div>
                  </label>
                </div>

                <div className="flex justify-end pt-4 border-t border-white/5">
                  <Button variant="primary" onClick={handleSave}>
                    Save Alerts Config
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* TAB: INTEGRATIONS */}
          {activeTab === "integrations" && (
            <Card className="glass-panel rounded-3xl border border-white/10">
              <CardHeader>
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-accent" />
                  AI Model & Broker Integrations
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Redis Cache Node URL"
                    value={redisUrl}
                    onChange={(e) => setRedisUrl(e.target.value)}
                  />
                  <Input
                    label="Celery Broker URL"
                    value={celeryBroker}
                    onChange={(e) => setCeleryBroker(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold text-foreground/80 block">Default LLM Model Core</label>
                  <select
                    value={geminiModel}
                    onChange={(e) => setGeminiModel(e.target.value)}
                    className="w-full rounded-2xl bg-slate-950 border border-white/10 p-3.5 text-sm text-foreground focus:outline-none focus:border-primary/50"
                  >
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro (Enterprise)</option>
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash (Low Latency)</option>
                    <option value="custom-tuned">Lucy-Fine-Tuned-v2</option>
                  </select>
                </div>

                <div className="flex items-center gap-2.5 p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs">
                  <AlertTriangle className="w-4.5 h-4.5 flex-shrink-0 text-amber-400" />
                  <span>Integrating custom model weights or altering Broker URL endpoints may cause active execution tasks to reset.</span>
                </div>

                <div className="flex justify-end pt-2 border-t border-white/5">
                  <Button variant="primary" onClick={handleSave}>
                    Save System Config
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* TAB: BILLING */}
          {activeTab === "billing" && (
            <div className="space-y-6">
              {/* Active Plan details */}
              <Card className="glass-panel rounded-3xl border border-white/10">
                <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4">
                  <div>
                    <span className="text-xs uppercase tracking-[0.2em] text-muted">Current Plan</span>
                    <CardTitle className="text-2xl mt-1">{currentPlan.name}</CardTitle>
                  </div>
                  <Badge className="bg-primary/20 text-primary border border-primary/30 text-sm font-bold rounded-full px-3 py-1 mt-2 sm:mt-0">
                    {currentPlan.price}
                  </Badge>
                </CardHeader>
                <CardContent className="space-y-5 pt-0">
                  <p className="text-xs text-muted">
                    Your subscription renewal date is scheduled on <span className="font-semibold text-foreground">{currentPlan.renewal}</span>.
                  </p>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                    <div className="p-4 rounded-2xl bg-slate-950/60 border border-white/5">
                      <span className="text-[10px] uppercase text-muted">Gemini Tokens</span>
                      <p className="text-lg font-bold text-foreground mt-1">{currentPlan.usage.tokens}</p>
                    </div>
                    <div className="p-4 rounded-2xl bg-slate-950/60 border border-white/5">
                      <span className="text-[10px] uppercase text-muted">Worker Agents</span>
                      <p className="text-lg font-bold text-foreground mt-1">{currentPlan.usage.agents}</p>
                    </div>
                    <div className="p-4 rounded-2xl bg-slate-950/60 border border-white/5">
                      <span className="text-[10px] uppercase text-muted">Research Tasks</span>
                      <p className="text-lg font-bold text-foreground mt-1">{currentPlan.usage.tasks}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Invoices list */}
              <Card className="glass-panel rounded-3xl border border-white/10">
                <CardHeader>
                  <CardTitle className="text-xl font-bold flex items-center gap-2">
                    <CreditCard className="w-5 h-5 text-accent" />
                    Invoice Transaction Log
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="overflow-x-auto rounded-2xl border border-white/5 bg-slate-950/30">
                    <table className="min-w-full text-sm text-left divide-y divide-white/5">
                      <thead className="bg-slate-950/60 text-muted text-xs uppercase tracking-wider">
                        <tr>
                          <th className="px-4 py-3">Invoice ID</th>
                          <th className="px-4 py-3">Billing Date</th>
                          <th className="px-4 py-3">Invoice Amount</th>
                          <th className="px-4 py-3">Payment Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {invoices.map((inv) => (
                          <tr key={inv.id} className="hover:bg-slate-900/40">
                            <td className="px-4 py-3 font-mono text-accent">{inv.id}</td>
                            <td className="px-4 py-3 text-foreground/80">{inv.date}</td>
                            <td className="px-4 py-3 text-foreground/80">{inv.amount}</td>
                            <td className="px-4 py-3">
                              <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] rounded-full">
                                {inv.status}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}
