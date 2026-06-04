"use client";

import * as React from "react";
import Link from "next/link";
import { Bot, Shield, Key, Cpu, ArrowLeft, Terminal } from "lucide-react";
import { motion } from "framer-motion";

export function AuthLayoutWrapper({
  children,
  title,
  subtitle,
}: {
  children: React.ReactNode;
  title: string;
  subtitle: string;
}) {
  const [logs, setLogs] = React.useState<string[]>([
    "AUTH_SYSTEM: Standby. Ready for secure connection...",
    "HANDSHAKE: Awaiting client request parameters..."
  ]);

  React.useEffect(() => {
    const authLogs = [
      "REQUEST: Received HTTPS payload // SSL active.",
      "PARSING: Resolving login endpoints...",
      "SECURITY: JWT payload validation active.",
      "ENCRYPTION: AES-256 cypher blocks verified.",
      "TELEMETRY: Authenticating node identity...",
      "HEALTH: Nodes status OK (3 active clusters)"
    ];

    let currentIdx = 0;
    const timer = setInterval(() => {
      if (currentIdx < authLogs.length) {
        setLogs((prev) => [...prev.slice(-3), authLogs[currentIdx]]);
        currentIdx++;
      } else {
        currentIdx = 0;
        setLogs([
          "AUTH_SYSTEM: Standby. Ready for secure connection...",
          "HANDSHAKE: Awaiting client request parameters..."
        ]);
      }
    }, 4000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground flex grid grid-cols-1 lg:grid-cols-12 overflow-x-hidden relative">
      {/* Visual background accents for the entire page */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] rounded-full bg-orb-purple blur-[140px] opacity-10 pointer-events-none z-0" />
      
      {/* Left Column - Hero Side (Hidden on Mobile) */}
      <div className="hidden lg:flex lg:col-span-5 flex-col justify-between p-12 bg-slate-950/40 border-r border-border relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-accent/5 pointer-events-none" />
        <div className="absolute -top-12 -left-12 w-64 h-64 rounded-full bg-orb-purple blur-[100px] opacity-20 pointer-events-none" />

        {/* Brand Header */}
        <Link href="/" className="flex items-center gap-2 group z-10">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-slate-950 font-bold shadow-md shadow-primary/20 group-hover:scale-105 transition-transform duration-300">
            <Bot className="w-5 h-5 text-slate-950" />
          </div>
          <span className="text-2xl font-black tracking-tight text-foreground">
            Lucy <span className="text-accent">AI</span>
          </span>
        </Link>

        {/* Middle Feature Highlights */}
        <div className="flex flex-col gap-8 my-auto z-10">
          <div className="flex flex-col gap-3">
            <h2 className="text-3xl font-black tracking-tight text-gradient-purple">
              Showcase Projects. Automate Research.
            </h2>
            <p className="text-sm text-muted leading-relaxed">
              Log in to manage agent nodes, review automated recruiter analytics telemetry, and deploy full-stack worker pools.
            </p>
          </div>

          {/* Icon Features List */}
          <div className="flex flex-col gap-5">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary flex-shrink-0">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-foreground mb-1">Autonomous Telemetry</h4>
                <p className="text-xs text-muted leading-relaxed">Deploys automated code validator scripts and schedules pipeline scans.</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center text-accent flex-shrink-0">
                <Key className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-foreground mb-1">JWT-Secured Core</h4>
                <p className="text-xs text-muted leading-relaxed">Uses secure JSON Web Tokens for identity authorization endpoints.</p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 flex-shrink-0">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-foreground mb-1">AES-256 Encryption</h4>
                <p className="text-xs text-muted leading-relaxed">Applies industrial cryptography standards safeguarding data integrity.</p>
              </div>
            </div>
          </div>

          {/* Mini Security Logger Terminal */}
          <div className="glass-panel rounded-xl p-4 border border-white/5 font-mono text-[11px] h-32 flex flex-col justify-between overflow-hidden">
            <div className="flex items-center gap-1.5 border-b border-border/20 pb-2 mb-2 text-muted">
              <Terminal className="w-3.5 h-3.5 text-accent" />
              <span>security-watchdog.log</span>
            </div>
            <div className="flex-grow flex flex-col gap-1.5 justify-end">
              {logs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-1">
                  <span className="text-primary font-bold">&gt;&gt;</span>
                  <span className={idx === logs.length - 1 ? "text-accent font-medium" : "text-muted/70"}>{log}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer details */}
        <p className="text-xs text-muted/60 z-10">
          &copy; {new Date().getFullYear()} Lucy AI. Secure Session.
        </p>
      </div>

      {/* Right Column - Form Side */}
      <div className="lg:col-span-7 flex flex-col justify-between p-6 sm:p-12 md:p-16 z-10 relative">
        {/* Back Link */}
        <div className="flex justify-between items-center mb-10">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-muted hover:text-foreground transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
            Back to landing page
          </Link>

          {/* Security details */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-border text-[10px] font-mono text-muted/80">
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            <span>Secure SSL Environment</span>
          </div>
        </div>

        {/* Central Card container */}
        <div className="w-full max-w-md mx-auto my-auto py-6">
          <div className="flex flex-col gap-1.5 mb-8 text-center sm:text-left">
            <h2 className="text-3xl font-black text-foreground tracking-tight">
              {title}
            </h2>
            <p className="text-sm text-muted">
              {subtitle}
            </p>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="glass-panel rounded-2xl p-6 sm:p-8 border border-white/5 shadow-2xl relative"
          >
            {/* Glowing borders */}
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
            {children}
          </motion.div>
        </div>

        {/* Footer info (Mobile view copyright, etc) */}
        <div className="mt-12 flex items-center justify-between text-xs text-muted/50 border-t border-border/20 pt-4 lg:hidden">
          <span>&copy; {new Date().getFullYear()} Lucy AI</span>
          <span>JWT Authenticated</span>
        </div>
      </div>
    </div>
  );
}
