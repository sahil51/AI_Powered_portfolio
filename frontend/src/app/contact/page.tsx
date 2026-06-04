"use client";

import * as React from "react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { motion } from "framer-motion";
import { 
  Send, 
  Mail, 
  MessageSquare, 
  MapPin, 
  ArrowLeft, 
  Sparkles,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import Link from "next/link";

const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
  </svg>
);

const LinkedinIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

const TwitterIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" {...props}>
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
);

export default function ContactPage() {
  const [chatOpen, setChatOpen] = React.useState(false);
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [message, setMessage] = React.useState("");
  
  // validation / status states
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [success, setSuccess] = React.useState(false);
  const [error, setError] = React.useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    if (!name.trim() || !email.trim() || !message.trim()) {
      setError("Please fill out all fields.");
      return;
    }

    if (!/\S+@\S+\.\S+/.test(email)) {
      setError("Please enter a valid email address.");
      return;
    }

    setIsSubmitting(true);

    // Simulate sending message API
    setTimeout(() => {
      setIsSubmitting(false);
      setSuccess(true);
      setName("");
      setEmail("");
      setMessage("");
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col relative overflow-hidden">
      {/* Glow Orbs */}
      <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-orb-purple blur-[140px] opacity-15 pointer-events-none z-0" />
      <div className="absolute bottom-[10%] left-[-15%] w-[550px] h-[550px] rounded-full bg-orb-cyan blur-[130px] opacity-10 pointer-events-none z-0" />

      <Navbar onTalkToAI={() => setChatOpen(true)} />

      <main className="flex-grow pt-28 pb-20 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 w-full flex flex-col justify-center">
        {/* Header Breadcrumb */}
        <div className="mb-8 flex items-center gap-3">
          <Link href="/" className="p-2 rounded-xl bg-slate-900 border border-border text-muted hover:text-foreground transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <span className="text-sm font-mono text-muted">/contact</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          {/* Left Panel: Contact info */}
          <div className="lg:col-span-5 space-y-6">
            <div className="space-y-4">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-xs font-semibold text-accent">
                <Sparkles className="w-3 h-3 animate-pulse" />
                <span>Let's Connect</span>
              </span>
              
              <h1 className="text-3xl md:text-5xl font-black text-gradient-cyan tracking-tight">
                Get in Touch
              </h1>
              
              <p className="text-sm text-muted leading-relaxed">
                Have questions about AI integrations, microservice performance, or want to schedule an interview? Drop a message and let's coordinate!
              </p>
            </div>

            {/* Availability details */}
            <div className="p-5 rounded-2xl bg-slate-950/60 border border-white/5 space-y-4">
              <div className="flex items-center gap-2.5">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <span className="text-sm font-semibold text-foreground">Availability Status</span>
              </div>
              <p className="text-xs text-muted leading-relaxed">
                Currently open to select technical roles, consultancies, or contract projects in AI backend engineering.
              </p>
            </div>

            {/* Communication Detail blocks */}
            <div className="space-y-4 pt-2">
              <div className="flex items-center gap-3 text-sm">
                <div className="w-9 h-9 rounded-lg bg-slate-900 border border-white/5 flex items-center justify-center text-primary">
                  <Mail className="w-4.5 h-4.5" />
                </div>
                <div>
                  <p className="text-xs text-muted">Email address</p>
                  <p className="font-semibold text-foreground">lucy@agentplatform.ai</p>
                </div>
              </div>

              <div className="flex items-center gap-3 text-sm">
                <div className="w-9 h-9 rounded-lg bg-slate-900 border border-white/5 flex items-center justify-center text-accent">
                  <MapPin className="w-4.5 h-4.5" />
                </div>
                <div>
                  <p className="text-xs text-muted">Location</p>
                  <p className="font-semibold text-foreground">San Francisco, CA (Remote)</p>
                </div>
              </div>
            </div>

            {/* Social Grid */}
            <div className="space-y-3">
              <p className="text-xs uppercase tracking-widest text-muted">Network profiles</p>
              <div className="flex items-center gap-3">
                <a href="https://github.com" target="_blank" rel="noreferrer" className="w-10 h-10 rounded-xl bg-slate-900 border border-white/5 hover:border-primary/40 hover:text-primary flex items-center justify-center transition-all duration-300 text-muted">
                  <GithubIcon />
                </a>
                <a href="https://linkedin.com" target="_blank" rel="noreferrer" className="w-10 h-10 rounded-xl bg-slate-900 border border-white/5 hover:border-accent/40 hover:text-accent flex items-center justify-center transition-all duration-300 text-muted">
                  <LinkedinIcon />
                </a>
                <a href="https://x.com" target="_blank" rel="noreferrer" className="w-10 h-10 rounded-xl bg-slate-900 border border-white/5 hover:border-secondary/40 hover:text-secondary flex items-center justify-center transition-all duration-300 text-muted">
                  <TwitterIcon />
                </a>
              </div>
            </div>
          </div>

          {/* Right Panel: Interactive Form */}
          <div className="lg:col-span-7">
            <div className="glass-panel rounded-3xl border border-white/10 p-6 sm:p-8 relative overflow-hidden">
              {/* Glowing header bar */}
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
              
              <form onSubmit={handleSubmit} className="space-y-5">
                {/* Form header */}
                <div>
                  <h3 className="text-lg font-bold text-foreground">Send Message</h3>
                  <p className="text-xs text-muted">Usually responds within 24 hours.</p>
                </div>

                {/* Error Banner */}
                {error && (
                  <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 text-xs">
                    <AlertCircle className="w-4.5 h-4.5 flex-shrink-0 text-red-400" />
                    <span>{error}</span>
                  </div>
                )}

                {/* Success Banner */}
                {success && (
                  <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-200 text-xs">
                    <CheckCircle2 className="w-4.5 h-4.5 flex-shrink-0 text-emerald-400" />
                    <span>Your message has been dispatched successfully! Thank you.</span>
                  </div>
                )}

                {/* Name Input */}
                <Input
                  label="Full Name"
                  type="text"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (error) setError("");
                  }}
                  disabled={isSubmitting}
                  required
                />

                {/* Email Input */}
                <Input
                  label="Email Address"
                  type="email"
                  placeholder="john@company.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError("");
                  }}
                  disabled={isSubmitting}
                  required
                />

                {/* Message Input */}
                <div className="space-y-1.5">
                  <label className="text-sm font-semibold text-foreground/80 tracking-wide block">
                    Message Detail
                  </label>
                  <textarea
                    rows={4}
                    placeholder="Describe your backend requirement or job opportunity here..."
                    value={message}
                    onChange={(e) => {
                      setMessage(e.target.value);
                      if (error) setError("");
                    }}
                    disabled={isSubmitting}
                    required
                    className="w-full rounded-2xl bg-slate-950/70 border border-white/10 p-3 text-sm text-foreground placeholder:text-muted focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-all duration-300 resize-none"
                  />
                </div>

                {/* Submit button */}
                <Button type="submit" variant="primary" className="w-full py-3" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Sending Message...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Send className="w-4 h-4" />
                      Send Message
                    </span>
                  )}
                </Button>
              </form>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
