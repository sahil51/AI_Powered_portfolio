"use client";

import * as React from "react";
import { Modal } from "@/components/ui/modal";
import { CheckCircle2, Server, Database, ArrowRight, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
  </svg>
);

export interface ProjectDetail {
  id: number;
  title: string;
  subtitle: string;
  description: string;
  fullDetails: string;
  tech: string[];
  features: string[];
  architecture: {
    client: string;
    server: string;
    database: string;
    cacheOrQueue?: string;
  };
  githubUrl: string;
  liveUrl?: string;
}

export function ProjectModal({
  isOpen,
  onClose,
  project,
}: {
  isOpen: boolean;
  onClose: () => void;
  project: ProjectDetail | null;
}) {
  if (!project) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={project.title} size="lg">
      <div className="flex flex-col gap-6">
        {/* Banner details */}
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-accent mb-1.5 block">
            Featured Project Detailed Review
          </span>
          <p className="text-sm text-muted leading-relaxed">
            {project.fullDetails}
          </p>
        </div>

        {/* Tech Stack Row */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-foreground mb-3">
            Technology Stack
          </h4>
          <div className="flex flex-wrap gap-2">
            {project.tech.map((t) => (
              <span
                key={t}
                className="text-xs px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary font-semibold shadow-sm"
              >
                {t}
              </span>
            ))}
          </div>
        </div>

        {/* Architectural Layout */}
        <div className="bg-slate-950/60 border border-border rounded-xl p-5 relative overflow-hidden backdrop-blur-md">
          <div className="absolute -top-10 -right-10 w-24 h-24 rounded-full bg-accent/5 blur-xl pointer-events-none" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-foreground mb-4 flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5 text-accent" />
            Backend Architecture Diagram
          </h4>
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-2">
            <div className="w-full sm:w-1/3 flex flex-col items-center p-3 rounded-lg bg-slate-900/60 border border-border text-center shadow-inner">
              <span className="text-xs text-muted font-bold uppercase mb-1">Entry Layer</span>
              <span className="text-sm font-semibold text-foreground">{project.architecture.client}</span>
            </div>
            <ArrowRight className="w-5 h-5 text-muted rotate-90 sm:rotate-0" />
            <div className="w-full sm:w-1/3 flex flex-col items-center p-3 rounded-lg bg-primary/10 border border-primary/20 text-center shadow-md">
              <span className="text-xs text-primary font-bold uppercase mb-1">Execution Engine</span>
              <span className="text-sm font-semibold text-foreground">{project.architecture.server}</span>
              {project.architecture.cacheOrQueue && (
                <span className="text-[10px] text-accent mt-1 bg-accent/10 px-2 py-0.5 rounded font-mono border border-accent/20">
                  {project.architecture.cacheOrQueue}
                </span>
              )}
            </div>
            <ArrowRight className="w-5 h-5 text-muted rotate-90 sm:rotate-0" />
            <div className="w-full sm:w-1/3 flex flex-col items-center p-3 rounded-lg bg-slate-900/60 border border-border text-center shadow-inner">
              <span className="text-xs text-muted font-bold uppercase mb-1">Persistence</span>
              <span className="text-sm font-semibold text-foreground flex items-center gap-1">
                <Database className="w-3.5 h-3.5 text-accent" />
                {project.architecture.database}
              </span>
            </div>
          </div>
        </div>

        {/* Feature Checklists */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-foreground mb-3">
            Core Features & Implementation
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {project.features.map((feature, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm text-foreground/95">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 border-t border-border pt-4 mt-2">
          <a
            href={project.githubUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex"
          >
            <Button variant="secondary" className="gap-2">
              <GithubIcon className="w-4 h-4" />
              Source Code
            </Button>
          </a>
          {project.liveUrl && (
            <a
              href={project.liveUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex"
            >
              <Button variant="primary" className="gap-2">
                <ExternalLink className="w-4 h-4" />
                Live Demo
              </Button>
            </a>
          )}
        </div>
      </div>
    </Modal>
  );
}
