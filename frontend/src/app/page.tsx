"use client";

import * as React from "react";
import { motion } from "framer-motion";
import {
  Sparkles,
  Layers,
  MessageSquare,
  ShoppingBag,
  Cpu,
  ArrowRight,
  Send,
  Zap,
  Globe,
  Database,
  Terminal,
  Bookmark
} from "lucide-react";

import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import { Card, StatsCard, FeatureCard, TestimonialCard } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ChatModal } from "@/components/chat-modal";
import { ProjectModal, ProjectDetail } from "@/components/project-modal";

// Projects Data conforming to ProjectDetail format
const PROJECTS_DATA: ProjectDetail[] = [
  {
    id: 1,
    title: "AI Multi-Agent Platform",
    subtitle: "Distributed Task Processing Network",
    description: "An orchestration engine that deploys autonomous agents to perform sequential web research and repository code generation tasks.",
    fullDetails: "Lucy AI Multi-Agent Platform is built to automate tedious research and software development processes. Recruiter and code auditing agents collaborate to test, build, and deploy sandbox Python environments based on simple user goals. The backend dynamically scaling with celery queues guarantees zero bottleneck delays.",
    tech: ["Django", "Redis", "Celery", "Gemini AI", "Docker"],
    features: [
      "Dynamic Agent workflow graphs",
      "Celery-broker priority queues",
      "Sandboxed Docker runtime environments",
      "Real-time event stream logging via SSE"
    ],
    architecture: {
      client: "NextJS Console",
      server: "Django Core API",
      database: "PostgreSQL",
      cacheOrQueue: "Redis + Celery"
    },
    githubUrl: "https://github.com",
    liveUrl: "https://lucy.ai"
  },
  {
    id: 2,
    title: "Real-Time Chat App",
    subtitle: "High-Concurrence Messaging Gateway",
    description: "A secure WebSockets communication server featuring channel subscriptions, online indicators, and cached message queues.",
    fullDetails: "This messaging application scales to thousands of concurrent connections using Django Channels. It uses Redis Pub/Sub channels to sync client instances instantly and caches recent room messages inside Redis memory before syncing them sequentially to the PostgreSQL database.",
    tech: ["WebSockets", "Redis", "PostgreSQL", "Django Channels"],
    features: [
      "Sub-millisecond broadcast latency",
      "Online/Offline presence counters",
      "JSON Web Token socket handshake guards",
      "Persistent state offline queueing"
    ],
    architecture: {
      client: "Web Client (WS)",
      server: "Django Channels",
      database: "PostgreSQL",
      cacheOrQueue: "Redis Pub/Sub"
    },
    githubUrl: "https://github.com",
    liveUrl: "https://chat.lucy.ai"
  },
  {
    id: 3,
    title: "E-Commerce Backend",
    subtitle: "Secure Payment & Checkout API Gateway",
    description: "A production-grade transactional store backend implementing tokenized Stripe payments, inventory locking, and order receipt dispatch.",
    fullDetails: "A robust backend system designed for high-concurrence holiday traffic. It implements database transactional level locking (SELECT FOR UPDATE) to avoid double-ordering products, integrates Stripe Webhooks securely with SHA-256 signatures, and processes asynchronous PDF invoicing.",
    tech: ["Django", "DRF", "Stripe", "PostgreSQL", "Celery"],
    features: [
      "Stripe Webhook signature authentication",
      "Pessimistic DB inventory locking",
      "Asynchronous PDF invoicing via Celery",
      "Automated email receipt delivery"
    ],
    architecture: {
      client: "Mobile / Web App",
      server: "Django Rest Framework",
      database: "PostgreSQL (PostGIS)",
      cacheOrQueue: "Redis Cache"
    },
    githubUrl: "https://github.com"
  }
];

// Testimonials Data
const TESTIMONIALS = [
  {
    quote: "Lucy's grasp of scalable backend patterns is outstanding. She restructured our Celery queues, immediately reducing processing backlogs by 80%. Her agent integrations are clean and production-ready.",
    author: "Alexander Mercer",
    role: "Director of Engineering",
    company: "Synapse Technologies"
  },
  {
    quote: "Working with Lucy was a breeze. She designed an e-commerce gateway with Stripe that processed 10,000 orders on day one without a single concurrency issue. A top-tier backend professional.",
    author: "Elena Rostova",
    role: "Technical Co-Founder",
    company: "Velo Cart"
  },
  {
    quote: "The multi-agent platform Lucy built for our research team has automated 70% of our market data scraping tasks. Her architecture is extremely well documented, modular, and maintainable.",
    author: "Marcus Vance",
    role: "VP of Product",
    company: "OmniAI Labs"
  }
];

// Tech Stack Data
const TECH_STACK = [
  { name: "Python", category: "Languages", desc: "Core backend language for high-performance scripting." },
  { name: "Django", category: "Frameworks", desc: "Monolithic & API design with secure default configurations." },
  { name: "DRF", category: "Frameworks", desc: "Django REST Framework for building clean, serializable APIs." },
  { name: "PostgreSQL", category: "Databases", desc: "Relational persistence with transaction isolation and indexing." },
  { name: "Redis", category: "Infrastructure", desc: "In-memory key-value cache and message broker." },
  { name: "Celery", category: "Infrastructure", desc: "Asynchronous task scheduler and workers orchestration." },
  { name: "Docker", category: "DevOps", desc: "Containerized deployments for reproducible production runtimes." },
  { name: "JWT", category: "Security", desc: "JSON Web Tokens for stateless and secure cross-domain auth." },
  { name: "Gemini AI", category: "AI Integration", desc: "Advanced LLM integration for semantic research & code synthesis." }
];

export default function Home() {
  const [chatOpen, setChatOpen] = React.useState(false);
  const [activeProject, setActiveProject] = React.useState<ProjectDetail | null>(null);
  const [projectModalOpen, setProjectModalOpen] = React.useState(false);

  // Terminal log simulation in Hero
  const [logs, setLogs] = React.useState<string[]>([
    "Initializing agent pipeline...",
    "Node setup: OK (3 active clusters)",
  ]);

  React.useEffect(() => {
    const logIntervals = [
      "Broker: Listening on redis://127.0.0.1:6379/0",
      "Worker core-1 spawned successfully.",
      "Agent 'Researcher' fetching query parameters...",
      "Agent 'Validator' pipeline: STANDBY",
      "LLM connection established: Gemini-Pro",
      "Process 43A2 task completed in 412ms.",
      "Syncing schema with database cache...",
      "System health: 100% // CPU load 2%"
    ];

    let currentIdx = 0;
    const timer = setInterval(() => {
      if (currentIdx < logIntervals.length) {
        setLogs((prev) => [...prev.slice(-4), logIntervals[currentIdx]]);
        currentIdx++;
      } else {
        currentIdx = 0;
        setLogs([
          "Initializing agent pipeline...",
          "Node setup: OK (3 active clusters)",
        ]);
      }
    }, 3500);

    return () => clearInterval(timer);
  }, []);

  const openProjectDetails = (project: ProjectDetail) => {
    setActiveProject(project);
    setProjectModalOpen(true);
  };

  return (
    <>
      <Navbar onTalkToAI={() => setChatOpen(true)} />

      <main className="flex-grow pt-20">
        {/* Background glow meshes */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] overflow-hidden pointer-events-none z-0">
          <div className="absolute top-[-10%] left-[10%] w-[500px] h-[500px] rounded-full bg-orb-purple blur-[120px] animate-pulse-slow" />
          <div className="absolute top-[20%] right-[10%] w-[450px] h-[450px] rounded-full bg-orb-cyan blur-[120px] animate-pulse-slow" />
        </div>

        {/* SECTION 2: HERO SECTION */}
        <section id="home" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Text details */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-semibold text-primary max-w-fit"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Lucy AI Multi-Agent Console</span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl sm:text-5xl md:text-6xl font-black tracking-tight leading-[1.1] text-gradient"
            >
              I Build AI-Powered Systems That Solve Real World Problems
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg md:text-xl text-muted leading-relaxed max-w-2xl"
            >
              AI backend engineer focused on Django, AI Agents, Redis, Celery, PostgreSQL and scalable systems.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-wrap items-center gap-4 mt-2"
            >
              <a href="#projects">
                <Button variant="primary" size="lg" className="shadow-lg shadow-primary/25">
                  View My Work
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </a>
              <Button
                variant="outline"
                size="lg"
                onClick={() => setChatOpen(true)}
                className="gap-2 border-accent/40 text-accent hover:bg-accent/10"
              >
                <Cpu className="w-4 h-4" />
                Talk With AI
              </Button>
            </motion.div>
          </div>

          {/* Right AI Visual Console */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:col-span-5 w-full relative"
          >
            {/* Visual Glassmorphic Console Panel */}
            <div className="glass-panel rounded-2xl border border-white/10 shadow-2xl relative overflow-hidden flex flex-col h-[380px] w-full">
              {/* Top border bar */}
              <div className="px-4 py-3 border-b border-border bg-slate-900/60 flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-red-500/80" />
                  <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
                  <span className="w-3 h-3 rounded-full bg-green-500/80" />
                </div>
                <span className="text-[11px] font-mono text-muted/80">lucy-agent-daemon.sh</span>
                <span className="w-4 h-4 rounded bg-primary/20 flex items-center justify-center text-[10px] text-primary font-bold">
                  v1
                </span>
              </div>

              {/* Console Body */}
              <div className="flex-grow p-4 flex flex-col justify-between font-mono text-xs text-foreground/90 overflow-hidden bg-slate-950/20">
                {/* Node diagram animation simulation */}
                <div className="border-b border-border/30 pb-4 mb-4 flex items-center justify-around">
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-9 h-9 rounded-lg bg-primary/10 border border-primary/40 flex items-center justify-center text-primary relative">
                      <Cpu className="w-4.5 h-4.5" />
                      <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-500 border border-background animate-pulse" />
                    </div>
                    <span className="text-[10px] text-muted">Researcher</span>
                  </div>
                  <div className="w-8 border-t border-dashed border-border/60 animate-pulse" />
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-9 h-9 rounded-lg bg-accent/10 border border-accent/40 flex items-center justify-center text-accent relative">
                      <Layers className="w-4.5 h-4.5 animate-float" />
                    </div>
                    <span className="text-[10px] text-muted">Planner</span>
                  </div>
                  <div className="w-8 border-t border-dashed border-border/60 animate-pulse" />
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-9 h-9 rounded-lg bg-secondary/20 border border-secondary/40 flex items-center justify-center text-secondary relative">
                      <Zap className="w-4.5 h-4.5" />
                    </div>
                    <span className="text-[10px] text-muted">Validator</span>
                  </div>
                </div>

                {/* Animated logs */}
                <div className="flex-grow flex flex-col gap-2.5 justify-end">
                  {logs.map((log, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-muted leading-relaxed">
                      <span className="text-primary font-bold">&gt;</span>
                      <span className={idx === logs.length - 1 ? "text-accent font-semibold" : "text-muted/80"}>
                        {log}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Active queue counter */}
                <div className="border-t border-border/30 pt-3 mt-4 flex items-center justify-between text-[10px] text-muted/60">
                  <span>Queued Tasks: <span className="text-accent font-bold">4</span></span>
                  <span>Latency: <span className="text-emerald-500 font-bold">12ms</span></span>
                </div>
              </div>
            </div>

            {/* Glowing neon ring decoration behind card */}
            <div className="absolute -inset-0.5 bg-gradient-to-r from-primary to-accent rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-1000 -z-10" />
          </motion.div>
        </section>

        {/* SECTION 3: STATISTICS */}
        <section id="about" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 border-t border-border">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <StatsCard value="3+" label="Years Experience" />
            <StatsCard value="20+" label="Projects" />
            <StatsCard value="10+" label="Technologies" />
            <StatsCard value="50+" label="Happy Clients" />
          </div>
        </section>

        {/* SECTION 4: FEATURED PROJECTS */}
        <section id="projects" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 border-t border-border">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-wider text-primary mb-2 block">
              Portfolio
            </span>
            <h2 className="text-3xl md:text-4xl font-black text-gradient-purple mb-4">
              Featured Projects
            </h2>
            <p className="text-muted text-sm md:text-base leading-relaxed">
              Explore three core backend and AI-integrated architectures, highlighting data synchronization, socket channels, and distributed processes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {PROJECTS_DATA.map((project, idx) => {
              // Map icons dynamically
              const icons = [
                <Cpu key={1} className="w-6 h-6" />,
                <MessageSquare key={2} className="w-6 h-6" />,
                <ShoppingBag key={3} className="w-6 h-6" />
              ];
              return (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: idx * 0.1 }}
                >
                  <FeatureCard
                    icon={icons[idx]}
                    title={project.title}
                    description={project.description}
                    tags={project.tech}
                    actionLabel="View Details"
                    onActionClick={() => openProjectDetails(project)}
                  />
                </motion.div>
              );
            })}
          </div>
        </section>

        {/* SECTION 5: TECH STACK */}
        <section className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 border-t border-border">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-wider text-accent mb-2 block">
              Skillsets
            </span>
            <h2 className="text-3xl md:text-4xl font-black text-gradient-cyan mb-4">
              Technologies & Infrastructure
            </h2>
            <p className="text-muted text-sm md:text-base leading-relaxed">
              A robust set of backend utilities, databases, caches, and AI models utilized to build fault-tolerant web architectures.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-9 gap-4">
            {TECH_STACK.map((tech, idx) => (
              <motion.div
                key={tech.name}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: idx * 0.05 }}
                whileHover={{ scale: 1.05 }}
                className="group relative cursor-help"
              >
                <div className="glass-panel rounded-xl p-4 flex flex-col items-center justify-center text-center h-28 border border-white/5 hover:border-accent/40 hover:bg-accent/5 transition-all duration-300">
                  <span className="text-sm font-bold text-foreground group-hover:text-accent transition-colors">
                    {tech.name}
                  </span>
                  <span className="text-[10px] text-muted/60 mt-1 uppercase font-semibold">
                    {tech.category}
                  </span>
                </div>

                {/* Tooltip detail block */}
                <div className="absolute z-20 bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-3 rounded-lg bg-slate-950 border border-border shadow-xl opacity-0 scale-95 pointer-events-none group-hover:opacity-100 group-hover:scale-100 transition-all duration-200">
                  <span className="text-xs font-semibold text-accent block mb-1">{tech.name}</span>
                  <p className="text-[11px] text-muted leading-normal">{tech.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* SECTION 6: TESTIMONIALS */}
        <section id="blog" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 border-t border-border">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-bold uppercase tracking-wider text-primary mb-2 block">
              Validation
            </span>
            <h2 className="text-3xl md:text-4xl font-black text-gradient-purple mb-4">
              Recruiter & Client Feedback
            </h2>
            <p className="text-muted text-sm md:text-base leading-relaxed">
              Read how Lucy AI delivers value through transactional consistency, automation scripting, and backend task scheduling.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {TESTIMONIALS.map((t, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
              >
                <TestimonialCard
                  quote={t.quote}
                  author={t.author}
                  role={t.role}
                  company={t.company}
                />
              </motion.div>
            ))}
          </div>
        </section>

        {/* SECTION 7: CALL TO ACTION */}
        <section id="contact" className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 mb-20">
          <div className="glass-panel rounded-3xl p-8 md:p-12 border border-primary/20 relative overflow-hidden shadow-2xl text-center flex flex-col items-center gap-6">
            {/* Glowing background highlights inside banner */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-primary/10 blur-3xl pointer-events-none" />

            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-xs font-semibold text-accent z-10">
              <Zap className="w-3.5 h-3.5" />
              <span>Available for Hire</span>
            </span>

            <h2 className="text-3xl md:text-5xl font-black text-gradient-cyan max-w-2xl z-10">
              Ready to Build AI-Powered Products?
            </h2>

            <p className="text-muted text-sm md:text-base max-w-xl z-10 leading-relaxed">
              Connect to chat about integrations, django setups, task brokerage, or recruit Lucy AI directly for your engineering squad.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4 z-10 mt-2">
              <a href="mailto:contact@lucy.ai">
                <Button variant="primary" size="lg" className="shadow-lg shadow-primary/25">
                  Hire Me
                  <Send className="w-4.5 h-4.5" />
                </Button>
              </a>
              <a href="#projects">
                <Button variant="outline" size="lg">
                  View Projects
                </Button>
              </a>
            </div>
          </div>
        </section>
      </main>

      <Footer />

      {/* Modals */}
      <ChatModal isOpen={chatOpen} onClose={() => setChatOpen(false)} />
      <ProjectModal
        isOpen={projectModalOpen}
        onClose={() => setProjectModalOpen(false)}
        project={activeProject}
      />
    </>
  );
}
