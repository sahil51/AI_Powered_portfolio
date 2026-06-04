"use client";

import * as React from "react";
import { Bot, Send, User, Sparkles, Terminal } from "lucide-react";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";

interface Message {
  sender: "user" | "ai";
  text: string;
  timestamp: string;
}

const PRESETS = [
  { q: "Tell me about Lucy's Django experience", a: "Lucy has 3+ years of experience with Django, building robust REST APIs using DRF, securing endpoints with JWT, and optimizing queries to reduce DB load by up to 40%. She treats Django as the core orchestrator of her multi-agent pipelines." },
  { q: "What is Lucy's Redis & Celery experience?", a: "Lucy uses Redis as both a caching layer and a Celery message broker. She has configured celery-beat task scheduling, managed distributed event streams, and set up WebSockets with Redis Pub/Sub for real-time portfolio updates." },
  { q: "What multi-agent projects has she built?", a: "Her flagship project is Lucy AI, a multi-agent system orchestrating autonomous researchers, recruiter analysis agents, and system health monitors. It is powered by Django, Gemini AI, and Celery workflows." },
  { q: "Is she open to relocation or remote work?", a: "Lucy is open to Remote opportunities worldwide, or hybrid/on-site positions in major tech hubs. She loves collaborative environments pushing the boundaries of AI integration!" }
];

export function ChatModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [messages, setMessages] = React.useState<Message[]>([
    {
      sender: "ai",
      text: "Hello recruiter! I am Lucy's autonomous agent assistant. Ask me anything about her skills, experience, projects, or availability.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputValue, setInputValue] = React.useState("");
  const [isTyping, setIsTyping] = React.useState(false);
  const chatEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = (text: string) => {
    if (!text.trim()) return;

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMessage: Message = { sender: "user", text, timestamp };
    
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    // Simulate agent response
    setTimeout(() => {
      // Find matching preset or default response
      const matched = PRESETS.find(p => text.toLowerCase().includes(p.q.toLowerCase()) || p.q.toLowerCase().includes(text.toLowerCase()));
      let responseText = "That's a great question! Lucy excels in Django backend architectures, asynchronous background execution with Celery/Redis, and large language model integrations. Would you like me to elaborate on her Django or AI experience?";
      
      if (matched) {
        responseText = matched.a;
      } else if (text.toLowerCase().includes("django") || text.toLowerCase().includes("python")) {
        responseText = PRESETS[0].a;
      } else if (text.toLowerCase().includes("celery") || text.toLowerCase().includes("redis") || text.toLowerCase().includes("broker")) {
        responseText = PRESETS[1].a;
      } else if (text.toLowerCase().includes("agent") || text.toLowerCase().includes("gemini") || text.toLowerCase().includes("project")) {
        responseText = PRESETS[2].a;
      } else if (text.toLowerCase().includes("job") || text.toLowerCase().includes("hire") || text.toLowerCase().includes("salary") || text.toLowerCase().includes("relocate")) {
        responseText = PRESETS[3].a;
      }

      setMessages((prev) => [...prev, {
        sender: "ai",
        text: responseText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
      setIsTyping(false);
    }, 1200);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Lucy AI - Recruiter Console" size="lg">
      <div className="flex flex-col h-[500px]">
        {/* Terminal Header Info */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-950/60 border border-white/5 mb-4 text-xs font-mono text-muted">
          <Terminal className="w-3.5 h-3.5 text-accent" />
          <span>sec-session: authenticated // agent-status:</span>
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-emerald-500 font-bold">ONLINE</span>
          </span>
        </div>

        {/* Chat Stream */}
        <div className="flex-grow overflow-y-auto pr-1 flex flex-col gap-4 mb-4 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex items-start gap-3 max-w-[85%] ${
                msg.sender === "user" ? "self-end flex-row-reverse" : "self-start"
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 shadow-md ${
                  msg.sender === "user"
                    ? "bg-slate-800 text-muted border border-border"
                    : "bg-gradient-to-br from-primary to-accent text-slate-950 border border-white/10"
                }`}
              >
                {msg.sender === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble */}
              <div className="flex flex-col gap-1">
                <div
                  className={`p-3.5 rounded-2xl text-sm leading-relaxed border ${
                    msg.sender === "user"
                      ? "bg-primary/10 border-primary/20 text-foreground rounded-tr-none"
                      : "bg-slate-900/60 border-border text-foreground/90 rounded-tl-none backdrop-blur-sm"
                  }`}
                >
                  {msg.text}
                </div>
                <span
                  className={`text-[10px] text-muted/60 px-1.5 ${
                    msg.sender === "user" ? "self-end" : "self-start"
                  }`}
                >
                  {msg.timestamp}
                </span>
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex items-start gap-3 self-start max-w-[80%]">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent text-slate-950 border border-white/10 flex items-center justify-center shadow-md animate-pulse">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-900/60 border border-border text-muted/80 p-3.5 rounded-2xl rounded-tl-none flex items-center gap-1.5">
                <span className="text-xs font-mono">Agent analyzing query</span>
                <span className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: "300ms" }} />
                </span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Preset Prompt Suggestions */}
        {messages.length === 1 && (
          <div className="mb-4">
            <span className="text-xs font-semibold text-muted/80 block mb-2 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-accent" />
              Quick Prompts:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(p.q)}
                  className="text-xs text-left p-2.5 rounded-xl bg-slate-900/40 border border-border hover:border-primary/40 hover:bg-primary/5 transition-all text-muted hover:text-foreground cursor-pointer"
                >
                  {p.q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Footer */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend(inputValue);
          }}
          className="flex items-center gap-2 mt-auto border-t border-border pt-4 bg-slate-950/20"
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type a message or skill (e.g. Django, Celery)..."
            className="flex-grow bg-slate-900/60 border border-border rounded-xl py-3 px-4 text-sm text-foreground placeholder:text-muted/60 focus:outline-none focus:border-accent/60 focus:ring-1 focus:ring-accent/40"
          />
          <Button type="submit" variant="primary" className="p-3 rounded-xl flex-shrink-0" disabled={!inputValue.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </Modal>
  );
}
