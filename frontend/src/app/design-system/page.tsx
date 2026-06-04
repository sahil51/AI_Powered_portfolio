"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowLeft, Bot, Sparkles, AlertCircle, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, StatsCard, FeatureCard, TestimonialCard } from "@/components/ui/card";
import { Input, SearchBox } from "@/components/ui/input";
import { Dropdown } from "@/components/ui/dropdown";
import { Modal } from "@/components/ui/modal";
import { Footer } from "@/components/footer";

const COLORS = [
  { name: "Primary", hex: "#8B5CF6", desc: "Violet accent for key CTAs and highlights" },
  { name: "Secondary", hex: "#7C3AED", desc: "Deep violet accent for active focus and buttons" },
  { name: "Accent", hex: "#22D3EE", desc: "Cyan highlight for micro-indicators and secondary rings" },
  { name: "Background", hex: "#0F172A", desc: "Slate-900 base for dark mode premium background" },
  { name: "Card", hex: "#111827", desc: "Slate-950/900 glass panels overlay background" },
  { name: "Text", hex: "#F8FAFC", desc: "Slate-50 for high-contrast legible headings" },
  { name: "Muted", hex: "#94A3B8", desc: "Slate-400 for subtext and descriptions" }
];

export default function DesignSystem() {
  const [searchValue, setSearchValue] = React.useState("");
  const [dropdownValue, setDropdownValue] = React.useState("");
  const [modalOpen, setModalOpen] = React.useState(false);
  const [copiedColor, setCopiedColor] = React.useState<string | null>(null);

  const copyToClipboard = (hex: string) => {
    navigator.clipboard.writeText(hex);
    setCopiedColor(hex);
    setTimeout(() => setCopiedColor(null), 1500);
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Background radial orbs */}
      <div className="absolute top-0 left-0 w-full h-[600px] overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[400px] h-[400px] rounded-full bg-orb-purple blur-[120px] opacity-25" />
        <div className="absolute bottom-[10%] right-[-10%] w-[400px] h-[400px] rounded-full bg-orb-cyan blur-[120px] opacity-15" />
      </div>

      {/* Header bar */}
      <header className="border-b border-border bg-slate-950/40 backdrop-blur-md sticky top-0 z-30 py-4 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-2 rounded-lg bg-slate-900 border border-border text-muted hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-xl font-bold flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                Lucy AI Design System
              </h1>
              <p className="text-xs text-muted">A living catalog of design tokens and reusable UI elements</p>
            </div>
          </div>

          <Link href="/">
            <Button variant="primary" size="sm">
              Back to Portfolio
            </Button>
          </Link>
        </div>
      </header>

      {/* Body content */}
      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Sidebar Index */}
        <aside className="lg:col-span-3 hidden lg:block sticky top-24 self-start">
          <nav className="flex flex-col gap-1 border-l border-border pl-4">
            {["Colors", "Typography", "Buttons", "Inputs", "Dropdown", "Cards", "Modals"].map((item) => (
              <a
                key={item}
                href={`#${item.toLowerCase()}`}
                className="text-sm font-medium text-muted hover:text-foreground hover:translate-x-1 transition-all py-1.5"
              >
                {item}
              </a>
            ))}
          </nav>
        </aside>

        {/* Components View */}
        <div className="lg:col-span-9 flex flex-col gap-16">
          
          {/* SECTION: COLORS */}
          <section id="colors" className="scroll-mt-24">
            <h2 className="text-2xl font-black text-gradient mb-2">Design Tokens: Colors</h2>
            <p className="text-muted text-sm mb-6">Harmonious premium SaaS palette leveraging rich dark layers with soft neon accents.</p>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {COLORS.map((color) => (
                <div
                  key={color.name}
                  onClick={() => copyToClipboard(color.hex)}
                  className="glass-panel rounded-xl p-4 flex flex-col justify-between h-36 border border-white/5 hover:border-primary/30 cursor-pointer relative group transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-foreground">{color.name}</span>
                    <button className="text-muted group-hover:text-foreground p-1 rounded hover:bg-white/5">
                      {copiedColor === color.hex ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                  
                  <div>
                    <div
                      className="w-full h-4 rounded-md mb-2"
                      style={{ backgroundColor: color.hex }}
                    />
                    <span className="font-mono text-xs text-accent block">{color.hex}</span>
                    <span className="text-[10px] text-muted leading-tight block mt-1">{color.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* SECTION: TYPOGRAPHY */}
          <section id="typography" className="scroll-mt-24 border-t border-border pt-12">
            <h2 className="text-2xl font-black text-gradient-purple mb-2">Typography Hierarchy</h2>
            <p className="text-muted text-sm mb-6">Configured with google-font Inter using modern high-contrast sizes and weights.</p>
            
            <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6">
              <div className="border-b border-border/30 pb-4">
                <span className="text-xs text-muted block mb-1">Heading 1 (Hero Title)</span>
                <span className="text-4xl md:text-5xl font-black text-gradient">The quick brown fox jumps...</span>
              </div>
              <div className="border-b border-border/30 pb-4">
                <span className="text-xs text-muted block mb-1">Heading 2 (Section Title)</span>
                <span className="text-2xl md:text-3xl font-black text-foreground">The quick brown fox jumps...</span>
              </div>
              <div className="border-b border-border/30 pb-4">
                <span className="text-xs text-muted block mb-1">Heading 3 (Component Title)</span>
                <span className="text-lg md:text-xl font-bold text-foreground">The quick brown fox jumps...</span>
              </div>
              <div>
                <span className="text-xs text-muted block mb-1">Body text (Clean & Readable)</span>
                <p className="text-sm text-muted leading-relaxed">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse potenti. In hac habitasse platea dictumst. Curabitur vel leo efficitur, dictum leo quis, congue nisi.
                </p>
              </div>
            </div>
          </section>

          {/* SECTION: BUTTONS */}
          <section id="buttons" className="scroll-mt-24 border-t border-border pt-12">
            <h2 className="text-2xl font-black text-gradient-cyan mb-2">Button Catalog</h2>
            <p className="text-muted text-sm mb-6">Interactive click states, hover elevations, and custom borders.</p>
            
            <div className="glass-panel rounded-2xl p-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 items-center justify-items-center">
              <div className="flex flex-col items-center gap-2">
                <span className="text-xs text-muted">Primary Button</span>
                <Button variant="primary">Get Started</Button>
              </div>
              
              <div className="flex flex-col items-center gap-2">
                <span className="text-xs text-muted">Secondary Button</span>
                <Button variant="secondary">View Source</Button>
              </div>
              
              <div className="flex flex-col items-center gap-2">
                <span className="text-xs text-muted">Ghost Button</span>
                <Button variant="ghost">Cancel</Button>
              </div>
              
              <div className="flex flex-col items-center gap-2">
                <span className="text-xs text-muted">Outline Button</span>
                <Button variant="outline">Learn More</Button>
              </div>
            </div>
          </section>

          {/* SECTION: INPUTS */}
          <section id="inputs" className="scroll-mt-24 border-t border-border pt-12">
            <h2 className="text-2xl font-black text-gradient mb-2">Input Fields & Search Box</h2>
            <p className="text-muted text-sm mb-6">Forms with validation errors, layout helpers, and clear triggers.</p>
            
            <div className="glass-panel rounded-2xl p-6 flex flex-col gap-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="User Name"
                  placeholder="Enter username"
                  helperText="Use a descriptive nickname"
                />
                <Input
                  label="Password"
                  type="password"
                  placeholder="••••••••"
                  error="Password must contain at least 8 characters"
                />
              </div>

              <div>
                <label className="text-sm font-semibold text-foreground/80 tracking-wide mb-1.5 block">
                  Search Filter Box
                </label>
                <SearchBox
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  onClear={() => setSearchValue("")}
                  placeholder="Search files, branches, or repositories..."
                />
              </div>
            </div>
          </section>

          {/* SECTION: DROPDOWN */}
          <section id="dropdown" className="scroll-mt-24 border-t border-border pt-12">
            <h2 className="text-2xl font-black text-gradient-purple mb-2">Dropdown Selector</h2>
            <p className="text-muted text-sm mb-6">Fully custom selection options with slide overlays and click-away closings.</p>
            
            <div className="glass-panel rounded-2xl p-6 max-w-md">
              <Dropdown
                label="Active Worker Branch"
                placeholder="Choose cluster branch"
                selectedValue={dropdownValue}
                onChange={(val) => setDropdownValue(val)}
                options={[
                  { value: "main", label: "main (production-ready)" },
                  { value: "staging", label: "staging (live deployment)" },
                  { value: "development", label: "dev-branch (local worker)" }
                ]}
              />
            </div>
          </section>

          {/* SECTION: CARDS */}
          <section id="cards" className="scroll-mt-24 border-t border-border pt-12">
            <h2 className="text-2xl font-black text-gradient-cyan mb-2">Component Cards</h2>
            <p className="text-muted text-sm mb-6">Specialized card grids supporting numbers count, tags lists, and quote modules.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <StatsCard value="12ms" label="Queue Response Latency" />
              <TestimonialCard
                quote="The deployment backend is rock solid. Lucy AI automated all our staging pipelines."
                author="Sarah Jenkins"
                role="DevOps Lead"
                company="Nexus Integration"
              />
            </div>
            
            <FeatureCard
              icon={<Bot className="w-6 h-6" />}
              title="Feature Card Integration"
              description="A reusable component designed to display products with icons, description blocks, inline tech tags, and custom details action parameters."
              tags={["React", "Framer Motion", "Tailwind"]}
              actionLabel="Demo Details Trigger"
              onActionClick={() => alert("Action triggered successfully!")}
            />
          </section>

          {/* SECTION: MODALS */}
          <section id="modals" className="scroll-mt-24 border-t border-border pt-12 mb-12">
            <h2 className="text-2xl font-black text-gradient mb-2">Modal Overlay</h2>
            <p className="text-muted text-sm mb-6">Transitions featuring backdrop blurs, scrolling overlays, and escape buttons.</p>
            
            <div className="glass-panel rounded-2xl p-6 flex flex-col items-center justify-center min-h-36">
              <Button variant="primary" onClick={() => setModalOpen(true)}>
                Open Showcase Modal
              </Button>
            </div>
          </section>

        </div>
      </main>

      <Footer />

      {/* Showcase Modal */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Showcase Modal Panel">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-xs">
              This modal locks body scroll, handles key escapes, and closes safely when the backdrop is clicked.
            </span>
          </div>
          <p className="text-sm text-muted">
            You can inject any layout here! This allows you to showcase detail lists, databases configurations, or automated logs.
          </p>
          <div className="flex justify-end mt-4">
            <Button variant="primary" size="sm" onClick={() => setModalOpen(false)}>
              Close Modal
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
