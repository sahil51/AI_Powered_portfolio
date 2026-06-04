"use client";

import * as React from "react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { 
  User, 
  Code2, 
  Cpu, 
  Database, 
  Terminal, 
  ArrowLeft, 
  Download, 
  Award, 
  Briefcase, 
  GraduationCap,
  Sparkles,
  Link as LinkIcon
} from "lucide-react";
import Link from "next/link";

const EXPERIENCES = [
  {
    role: "Senior AI & Backend Systems Engineer",
    company: "Autonomous Agent Tech",
    period: "2024 - Present",
    desc: "Spearheaded celery priority queue migration, reducing async processing bottlenecks by 80%. Designed multi-agent orchestrator workflows processing 10k+ daily developer queries.",
    tech: ["Python", "Django", "Celery", "Redis", "Gemini Pro", "Docker"]
  },
  {
    role: "Backend Architect",
    company: "Velo Cart & Co",
    period: "2022 - 2024",
    desc: "Implemented Stripe Checkout webhook pipelines handling $4M+ transactions. Developed pessimistic locking layers in PostgreSQL to eliminate concurrency purchase failures during holiday spikes.",
    tech: ["Django Rest Framework", "PostgreSQL", "Stripe", "Redis", "Docker"]
  },
  {
    role: "Software Developer",
    company: "Nexus Integrations",
    period: "2021 - 2022",
    desc: "Co-authored real-time dashboard socket layers using Django Channels. Created automatic document RAG vector search pipelines using PgVector.",
    tech: ["Python", "WebSockets", "Django Channels", "PostgreSQL", "React"]
  }
];

const SKILLS = [
  { name: "Python / Django / DRF", category: "Backend", level: "Expert" },
  { name: "PostgreSQL / PgVector", category: "Database", level: "Expert" },
  { name: "Redis Cache & Queue Broker", category: "Infrastructure", level: "Advanced" },
  { name: "Celery Task Scheduler", category: "Infrastructure", level: "Expert" },
  { name: "Docker & Containerization", category: "DevOps", level: "Advanced" },
  { name: "WebSockets & Event Streams", category: "Real-time", level: "Advanced" },
  { name: "Gemini AI & Semantic Search", category: "AI Systems", level: "Advanced" },
  { name: "Next.js / TypeScript / CSS", category: "Frontend", level: "Intermediate" }
];

const ACHIEVEMENTS = [
  "Optimized processing speed of backend worker agents by 40% using batched Redis pipelines.",
  "Designed a secure sandbox Docker executor environment for evaluating generated Python code scripts.",
  "Built an automated recruiter intelligence dashboard evaluated by 50+ hiring managers.",
  "Contributor to open-source Python telemetry and distributed messaging tools."
];

export default function AboutPage() {
  const [chatOpen, setChatOpen] = React.useState(false);

  const handleDownload = () => {
    alert("Downloading Resume... (Mock Integration: resume_lucy_backend_engineer.pdf)");
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col relative overflow-hidden">
      {/* Background neon orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-orb-purple blur-[130px] opacity-15 pointer-events-none z-0" />
      <div className="absolute bottom-[20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-orb-cyan blur-[130px] opacity-10 pointer-events-none z-0" />

      <Navbar onTalkToAI={() => setChatOpen(true)} />

      <main className="flex-grow pt-28 pb-20 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 w-full">
        {/* Header Breadcrumb */}
        <div className="mb-8 flex items-center gap-3">
          <Link href="/" className="p-2 rounded-xl bg-slate-900 border border-border text-muted hover:text-foreground transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <span className="text-sm font-mono text-muted">/about</span>
        </div>

        {/* Top Split Section: Profile Card & Quick Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-12">
          {/* Profile card */}
          <div className="lg:col-span-8">
            <div className="glass-panel rounded-3xl border border-white/10 p-6 sm:p-8 relative overflow-hidden h-full flex flex-col justify-between">
              <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 blur-2xl rounded-full" />
              
              <div className="space-y-6">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-slate-950 font-bold shadow-lg">
                    <User className="w-8 h-8" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-black tracking-tight text-foreground">Lucy AI</h1>
                    <p className="text-sm font-mono text-accent">Distributed Systems & AI Architect</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-bold text-foreground">Bio Overview</h3>
                  <p className="text-sm text-muted leading-relaxed">
                    I am a backend specialist focused on high-throughput asynchronous architectures, transactional database locks, and generative agent pipelines. By bridging standard web systems (Django, Celery, Postgres) with LLM frameworks, I build solutions that research, self-correct, and scale in sandboxed environments.
                  </p>
                  <p className="text-sm text-muted leading-relaxed">
                    Based on a core philosophy of modular design, I believe in writing robust telemetry logs, maintaining strict clean-code principles, and avoiding resource leaks.
                  </p>
                </div>
              </div>

              <div className="mt-8 flex flex-wrap gap-4 items-center">
                <Button variant="primary" size="md" onClick={handleDownload} className="gap-2 shadow-lg shadow-primary/20">
                  <Download className="w-4 h-4" />
                  Download Resume
                </Button>
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[11px] font-semibold text-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Available for Remote Projects
                </div>
              </div>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="lg:col-span-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4">
            <div className="glass-panel rounded-3xl border border-white/10 p-6 flex flex-col justify-between">
              <span className="text-xs uppercase tracking-[0.2em] text-muted">Core Experience</span>
              <div>
                <p className="text-4xl font-black text-gradient mt-2">3+ Years</p>
                <p className="text-xs text-muted mt-1">Enterprise async development</p>
              </div>
            </div>

            <div className="glass-panel rounded-3xl border border-white/10 p-6 flex flex-col justify-between">
              <span className="text-xs uppercase tracking-[0.2em] text-muted">AI Orchestrations</span>
              <div>
                <p className="text-4xl font-black text-gradient-cyan mt-2">50,000+</p>
                <p className="text-xs text-muted mt-1">LLM token-verified iterations</p>
              </div>
            </div>
          </div>
        </div>

        {/* Mid Section: Skills Matrix */}
        <div className="mb-12">
          <div className="glass-panel rounded-3xl border border-white/10 p-6 sm:p-8">
            <div className="flex items-center gap-2 mb-6">
              <Code2 className="w-5 h-5 text-primary" />
              <h2 className="text-2xl font-bold text-foreground">Interactive Skills Matrix</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {SKILLS.map((skill) => (
                <div key={skill.name} className="p-4 rounded-2xl bg-slate-950/50 border border-white/5 hover:border-primary/30 transition-colors">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-xs text-muted uppercase tracking-wider">{skill.category}</span>
                    <Badge className="bg-primary/10 text-primary border border-primary/20 text-[10px] rounded-full px-2 py-0">
                      {skill.level}
                    </Badge>
                  </div>
                  <p className="text-sm font-semibold text-foreground">{skill.name}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom split: Experience timeline & Achievements */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Work experience */}
          <div className="lg:col-span-7 space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <Briefcase className="w-5 h-5 text-accent" />
              <h2 className="text-2xl font-bold text-foreground">Career Milestones</h2>
            </div>

            <div className="space-y-6 relative border-l border-border pl-6 ml-3">
              {EXPERIENCES.map((exp, idx) => (
                <div key={idx} className="relative">
                  {/* Timeline point */}
                  <span className="absolute -left-[31px] top-1.5 w-4.5 h-4.5 rounded-full bg-slate-950 border-2 border-accent flex items-center justify-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                  </span>
                  
                  <div className="glass-panel rounded-2xl border border-white/5 p-5 space-y-3 hover:border-accent/40 transition-colors">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <h4 className="text-base font-bold text-foreground">{exp.role}</h4>
                        <p className="text-xs text-muted">{exp.company}</p>
                      </div>
                      <Badge className="bg-slate-900 border border-white/10 text-accent text-xs rounded-full">
                        {exp.period}
                      </Badge>
                    </div>
                    <p className="text-xs sm:text-sm text-muted leading-relaxed">{exp.desc}</p>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {exp.tech.map((t) => (
                        <span key={t} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 text-muted/80 border border-white/5">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Key Achievements */}
          <div className="lg:col-span-5 space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <Award className="w-5 h-5 text-primary" />
              <h2 className="text-2xl font-bold text-foreground">Key Accomplishments</h2>
            </div>

            <div className="glass-panel rounded-3xl border border-white/10 p-6 sm:p-8 space-y-6 h-fit">
              {ACHIEVEMENTS.map((ach, idx) => (
                <div key={idx} className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <p className="text-sm text-muted leading-relaxed pt-1">{ach}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
