"use client";

import * as React from "react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import { ProjectModal, ProjectDetail } from "@/components/project-modal";
import { FeatureCard } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { Search, Sparkles, Filter, Code2, ArrowLeft, Cpu, MessageSquare, ShoppingBag } from "lucide-react";
import Link from "next/link";

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

const CATEGORIES = ["All", "Django", "Redis", "Celery", "WebSockets", "PostgreSQL"];

export default function ProjectsPage() {
  const [chatOpen, setChatOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [activeCategory, setActiveCategory] = React.useState("All");
  const [activeProject, setActiveProject] = React.useState<ProjectDetail | null>(null);
  const [modalOpen, setModalOpen] = React.useState(false);

  const filteredProjects = React.useMemo(() => {
    return PROJECTS_DATA.filter((project) => {
      const matchesSearch = project.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                            project.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            project.tech.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesCategory = activeCategory === "All" || project.tech.includes(activeCategory);
      return matchesSearch && matchesCategory;
    });
  }, [searchQuery, activeCategory]);

  const openProjectDetails = (project: ProjectDetail) => {
    setActiveProject(project);
    setModalOpen(true);
  };

  const projectIcons = [
    <Cpu key={1} className="w-6 h-6 text-primary" />,
    <MessageSquare key={2} className="w-6 h-6 text-accent" />,
    <ShoppingBag key={3} className="w-6 h-6 text-secondary" />
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col relative overflow-hidden">
      {/* Background grids and lights */}
      <div className="absolute top-0 left-0 w-full h-[600px] overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-orb-purple blur-[140px] opacity-15" />
        <div className="absolute top-[30%] right-[-10%] w-[450px] h-[450px] rounded-full bg-orb-cyan blur-[130px] opacity-10" />
      </div>

      <Navbar onTalkToAI={() => setChatOpen(true)} />

      <main className="flex-grow pt-28 pb-20 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 w-full">
        {/* Header Breadcrumb */}
        <div className="mb-8 flex items-center gap-3">
          <Link href="/" className="p-2 rounded-xl bg-slate-900 border border-border text-muted hover:text-foreground transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <span className="text-sm font-mono text-muted">/projects</span>
        </div>

        {/* Hero Section */}
        <div className="text-center max-w-2xl mx-auto mb-12">
          <span className="text-xs font-bold uppercase tracking-wider text-primary mb-2 block">
            Technical Portfolio
          </span>
          <h1 className="text-3xl md:text-5xl font-black text-gradient-purple mb-4">
            Architectures & Codebases
          </h1>
          <p className="text-sm text-muted leading-relaxed">
            Review detailed execution graphs, asynchronous message queues, Stripe webhooks, and AI pipelines. Click any card to explore full blueprints.
          </p>
        </div>

        {/* Filter Controls Bar */}
        <div className="glass-panel rounded-3xl border border-white/10 p-5 mb-10 flex flex-col md:flex-row gap-4 items-center justify-between shadow-xl">
          {/* Search Box */}
          <div className="w-full md:w-80">
            <Input
              type="text"
              placeholder="Search by title or stack..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={<Search className="w-4 h-4 text-muted" />}
              className="w-full"
            />
          </div>

          {/* Category Tabs */}
          <div className="flex flex-wrap gap-2 justify-center">
            {CATEGORIES.map((category) => (
              <button
                key={category}
                onClick={() => setActiveCategory(category)}
                className={`text-xs font-semibold px-4 py-2 rounded-full border transition-all duration-300 ${
                  activeCategory === category
                    ? "bg-primary border-primary text-foreground shadow-md shadow-primary/20"
                    : "bg-slate-950/60 border-white/5 text-muted hover:border-primary/40 hover:text-foreground"
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* Projects Grid */}
        {filteredProjects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredProjects.map((project, idx) => (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: idx * 0.1 }}
              >
                <FeatureCard
                  icon={projectIcons[project.id - 1] || <Code2 className="w-6 h-6 text-primary" />}
                  title={project.title}
                  description={project.description}
                  tags={project.tech}
                  actionLabel="View Blueprint Details"
                  onActionClick={() => openProjectDetails(project)}
                />
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="glass-panel rounded-3xl border border-white/10 p-12 text-center">
            <Filter className="w-12 h-12 text-muted mx-auto mb-4" />
            <h3 className="text-lg font-bold text-foreground">No matches found</h3>
            <p className="text-sm text-muted mt-1">
              Try adjusting your filters or searching for other backend frameworks.
            </p>
          </div>
        )}
      </main>

      <Footer />

      {/* Details modal */}
      <ProjectModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        project={activeProject}
      />
    </div>
  );
}
