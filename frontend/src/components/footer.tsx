"use client";

import Link from "next/link";
import { Bot, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
  </svg>
);

const LinkedinIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect x="2" y="9" width="4" height="12" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

const TwitterIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z" />
  </svg>
);

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-950/40 border-t border-border pt-16 pb-8 relative overflow-hidden">
      {/* Visual background accents */}
      <div className="absolute bottom-0 left-1/4 w-80 h-80 rounded-full bg-primary/5 blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 md:gap-12 pb-12">
          {/* Brand Column */}
          <div className="md:col-span-4 flex flex-col gap-4">
            <Link href="#home" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-slate-900 font-bold">
                <Bot className="w-4 h-4 text-slate-950" />
              </div>
              <span className="text-xl font-black tracking-tight text-foreground">
                Lucy <span className="text-accent">AI</span>
              </span>
            </Link>
            <p className="text-sm text-muted leading-relaxed max-w-sm">
              Showcase Projects. Automate Research. Impress Recruiters. The leading multi-agent portfolio hub for next-gen backend and AI engineers.
            </p>
            {/* Social Links */}
            <div className="flex items-center gap-3 mt-2">
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="w-9 h-9 rounded-lg bg-slate-900 border border-border flex items-center justify-center text-muted hover:text-foreground hover:border-primary/50 transition-colors"
                aria-label="GitHub"
              >
                <GithubIcon className="w-4 h-4" />
              </a>
              <a
                href="https://linkedin.com"
                target="_blank"
                rel="noreferrer"
                className="w-9 h-9 rounded-lg bg-slate-900 border border-border flex items-center justify-center text-muted hover:text-foreground hover:border-primary/50 transition-colors"
                aria-label="LinkedIn"
              >
                <LinkedinIcon className="w-4 h-4" />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noreferrer"
                className="w-9 h-9 rounded-lg bg-slate-900 border border-border flex items-center justify-center text-muted hover:text-foreground hover:border-primary/50 transition-colors"
                aria-label="Twitter"
              >
                <TwitterIcon className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Quick Links Column */}
          <div className="md:col-span-2 col-span-6 flex flex-col gap-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
              Platform
            </h4>
            <ul className="flex flex-col gap-2">
              {["Features", "Design System", "AI Agent", "Pricing"].map((item) => (
                <li key={item}>
                  <Link
                    href={item === "Design System" ? "/design-system" : "#"}
                    className="text-sm text-muted hover:text-foreground hover:translate-x-0.5 transition-all inline-flex items-center gap-1 group"
                  >
                    {item}
                    {item === "Design System" && <ArrowUpRight className="w-3 h-3 text-accent opacity-0 group-hover:opacity-100 transition-opacity" />}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Column */}
          <div className="md:col-span-2 col-span-6 flex flex-col gap-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
              Resources
            </h4>
            <ul className="flex flex-col gap-2">
              {["Documentation", "API Reference", "Status", "Contact"].map((item) => (
                <li key={item}>
                  <a
                    href="#"
                    className="text-sm text-muted hover:text-foreground hover:translate-x-0.5 transition-all inline-block"
                  >
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter Subscription Column */}
          <div className="md:col-span-4 flex flex-col gap-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
              Subscribe to Updates
            </h4>
            <p className="text-sm text-muted">
              Get the latest updates on backend engineering & AI multi-agent systems.
            </p>
            <form onSubmit={(e) => e.preventDefault()} className="flex gap-2 mt-1">
              <Input
                placeholder="you@domain.com"
                className="bg-slate-900 border-border"
                required
              />
              <Button type="submit" variant="primary" className="whitespace-nowrap px-4 py-2">
                Subscribe
              </Button>
            </form>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-border mt-8 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted">
            &copy; {currentYear} Lucy AI. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <a href="#" className="text-xs text-muted hover:text-foreground transition-colors">
              Privacy Policy
            </a>
            <a href="#" className="text-xs text-muted hover:text-foreground transition-colors">
              Terms of Service
            </a>
            <a href="#" className="text-xs text-muted hover:text-foreground transition-colors">
              Cookie Settings
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
