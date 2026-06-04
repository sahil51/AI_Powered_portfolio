"use client";

import * as React from "react";
import { Search, Paperclip, Send, Copy, RefreshCcw, Trash2, Sparkles, Bot, ChevronDown, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface AssistantMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: string;
}

interface AssistantConversation {
  id: string;
  title: string;
  agent: string;
  lastActivity: string;
  pinned: boolean;
  snippet: string;
  messages: AssistantMessage[];
}

const AGENTS = [
  "Research Agent",
  "Portfolio Agent",
  "Recruiter Agent",
  "Client Agent",
  "Recommendation Agent",
  "Project Explainer Agent",
];

const PROMPTS = [
  "Analyze My Portfolio",
  "Review Resume",
  "Generate Project Ideas",
  "Research AI Trends",
  "Career Roadmap",
];

const INITIAL_CONVERSATIONS: AssistantConversation[] = [
  {
    id: "chat-1",
    title: "Portfolio strategy review",
    agent: "Portfolio Agent",
    lastActivity: "2m ago",
    pinned: true,
    snippet: "Optimize your portfolio narrative for product hiring...",
    messages: [
      { id: "m1", role: "assistant", text: "Ready when you are. What would you like Lucy AI to help with today?", timestamp: "08:44" },
    ],
  },
  {
    id: "chat-2",
    title: "Recruiter outreach plan",
    agent: "Recruiter Agent",
    lastActivity: "1h ago",
    pinned: false,
    snippet: "Build a follow-up sequence for recruiters...",
    messages: [
      { id: "m2", role: "assistant", text: "I can help you draft a recruiter outreach plan with strong personalization. Send me the details.", timestamp: "07:22" },
    ],
  },
  {
    id: "chat-3",
    title: "AI trend signals",
    agent: "Research Agent",
    lastActivity: "Yesterday",
    pinned: false,
    snippet: "Summarize the major AI trends shaping product delivery...",
    messages: [
      { id: "m3", role: "assistant", text: "Let me summarize the top AI trends for your portfolio context.", timestamp: "Thu" },
    ],
  },
];

export default function AssistantPage() {
  const [conversations, setConversations] = React.useState<AssistantConversation[]>(INITIAL_CONVERSATIONS);
  const [selectedConversationId, setSelectedConversationId] = React.useState(conversations[0].id);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [selectedAgent, setSelectedAgent] = React.useState(AGENTS[0]);
  const [inputValue, setInputValue] = React.useState("");
  const [isTyping, setIsTyping] = React.useState(false);

  const selectedConversation = React.useMemo(
    () => conversations.find((conversation) => conversation.id === selectedConversationId) ?? conversations[0],
    [conversations, selectedConversationId]
  );

  const filteredConversations = React.useMemo(
    () => conversations.filter((conversation) => conversation.title.toLowerCase().includes(searchTerm.toLowerCase())),
    [conversations, searchTerm]
  );

  const handleSelectConversation = (id: string) => {
    setSelectedConversationId(id);
    const selected = conversations.find((item) => item.id === id);
    if (selected) {
      setSelectedAgent(selected.agent);
    }
  };

  const handleSend = () => {
    if (!inputValue.trim()) {
      return;
    }

    const userMessage: AssistantMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text: inputValue.trim(),
      timestamp: "Now",
    };

    const updatedConversations = conversations.map((conversation) => {
      if (conversation.id !== selectedConversation.id) return conversation;
      return {
        ...conversation,
        messages: [...conversation.messages, userMessage],
        lastActivity: "Now",
      };
    });

    setConversations(updatedConversations);
    setInputValue("");
    setIsTyping(true);

    window.setTimeout(() => {
      const assistantMessage: AssistantMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: `Here is a smart answer from ${selectedAgent}. I distilled the latest guidance, portfolio impact, and next steps for you.`,
        timestamp: "Now",
      };

      setConversations((current) =>
        current.map((conversation) => {
          if (conversation.id !== selectedConversation.id) return conversation;
          return {
            ...conversation,
            messages: [...conversation.messages, assistantMessage],
          };
        })
      );
      setIsTyping(false);
    }, 900);
  };

  const handleCopyResponse = (text: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
    }
  };

  const handleRegenerate = () => {
    if (!selectedConversation) return;
    const lastAssistant = [...selectedConversation.messages].reverse().find((message) => message.role === "assistant");
    if (!lastAssistant) return;

    setIsTyping(true);
    window.setTimeout(() => {
      setConversations((current) =>
        current.map((conversation) => {
          if (conversation.id !== selectedConversation.id) return conversation;
          return {
            ...conversation,
            messages: conversation.messages.map((message) =>
              message.id === lastAssistant.id
                ? { ...message, text: `${message.text} (refined response generated again to sharpen the recommendation.)` }
                : message
            ),
          };
        })
      );
      setIsTyping(false);
    }, 900);
  };

  const handleDeleteChat = () => {
    const updated = conversations.filter((conversation) => conversation.id !== selectedConversation.id);
    setConversations(updated);
    if (updated.length > 0) {
      setSelectedConversationId(updated[0].id);
      setSelectedAgent(updated[0].agent);
    }
  };

  const selectPrompt = (prompt: string) => {
    setInputValue(prompt);
  };

  return (
    <div className="space-y-8 pb-16">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-primary">AI Assistant</p>
          <h1 className="mt-4 text-4xl font-semibold text-foreground">Lucy AI chat workspace</h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-muted">Ask questions, run research, and refine your portfolio with a powerful multi-agent assistant experience.</p>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <aside className="space-y-6 rounded-3xl border border-white/10 bg-slate-950/60 p-5 shadow-2xl shadow-black/20 backdrop-blur-xl">
          <div className="mb-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.3em] text-muted">Conversations</p>
                <h2 className="mt-2 text-xl font-semibold text-foreground">Recent chats</h2>
              </div>
              <Badge variant="outline">{conversations.length}</Badge>
            </div>
            <div className="mt-4">
              <Input
                label="Search chats"
                placeholder="Search by title"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                icon={<Search className="w-4 h-4" />}
              />
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted mb-3">Pinned chats</p>
              <div className="space-y-3">
                {filteredConversations.filter((item) => item.pinned).map((conversation) => (
                  <button
                    key={conversation.id}
                    onClick={() => handleSelectConversation(conversation.id)}
                    className={`w-full rounded-3xl border px-4 py-4 text-left transition ${conversation.id === selectedConversation.id ? "border-primary bg-primary/5" : "border-white/10 bg-slate-950/80 hover:border-primary/40"}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-foreground">{conversation.title}</span>
                      <Badge variant="secondary">Pinned</Badge>
                    </div>
                    <p className="mt-2 text-xs text-muted">{conversation.snippet}</p>
                  </button>
                ))}
                {filteredConversations.filter((item) => item.pinned).length === 0 && (
                  <p className="text-sm text-muted">No pinned chats yet.</p>
                )}
              </div>
            </div>

            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted mb-3">Recent conversations</p>
              <div className="space-y-3">
                {filteredConversations.map((conversation) => (
                  <button
                    key={conversation.id}
                    onClick={() => handleSelectConversation(conversation.id)}
                    className={`w-full rounded-3xl border px-4 py-3 text-left transition ${conversation.id === selectedConversation.id ? "border-primary bg-primary/5" : "border-white/10 bg-slate-950/80 hover:border-primary/40"}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-foreground">{conversation.title}</span>
                      <span className="text-xs text-muted">{conversation.lastActivity}</span>
                    </div>
                    <p className="mt-2 text-xs text-muted line-clamp-2">{conversation.snippet}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>

        <main className="space-y-6">
          <Card className="rounded-3xl border border-white/10 bg-slate-950/80">
            <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="text-2xl">{selectedConversation.title}</CardTitle>
                <p className="text-sm text-muted">{selectedConversation.agent} • Last updated {selectedConversation.lastActivity}</p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Badge variant="secondary">{selectedAgent}</Badge>
                <Button variant="ghost" size="sm" onClick={handleRegenerate}>
                  <RefreshCcw className="w-4 h-4" /> Regenerate
                </Button>
                <Button variant="ghost" size="sm" onClick={handleDeleteChat}>
                  <Trash2 className="w-4 h-4" /> Delete Chat
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-3">
                <div className="flex flex-wrap gap-2">
                  {AGENTS.map((agent) => (
                    <button
                      key={agent}
                      onClick={() => setSelectedAgent(agent)}
                      className={`rounded-full border px-4 py-2 text-sm transition ${selectedAgent === agent ? "border-primary bg-primary/10 text-primary" : "border-white/10 bg-slate-900 text-muted hover:border-primary/40"}`}
                    >
                      {agent}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-5 rounded-3xl border border-white/10 bg-slate-950/70 p-5 shadow-2xl shadow-black/20">
            <div className="space-y-4 max-h-[640px] overflow-y-auto pr-2">
              {selectedConversation.messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === "assistant" ? "justify-start" : "justify-end"}`}>
                  <div className={`max-w-[85%] rounded-3xl border px-5 py-4 shadow-sm ${message.role === "assistant" ? "border-white/10 bg-slate-900" : "border-primary/30 bg-primary/10 text-foreground"}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <div className={`rounded-full p-2 ${message.role === "assistant" ? "bg-slate-800" : "bg-primary/20"}`}>
                          {message.role === "assistant" ? <Bot className="w-4 h-4 text-primary" /> : <User className="w-4 h-4 text-foreground" />}
                        </div>
                        <span className="text-sm font-semibold text-foreground">{message.role === "assistant" ? "Lucy AI" : "You"}</span>
                      </div>
                      <span className="text-xs text-muted">{message.timestamp}</span>
                    </div>
                    <p className="mt-3 text-sm leading-7 text-foreground/90">{message.text}</p>
                    {message.role === "assistant" && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" onClick={() => handleCopyResponse(message.text)}>
                          <Copy className="w-4 h-4" /> Copy
                        </Button>
                        <Button variant="outline" size="sm" onClick={handleRegenerate}>
                          <RefreshCcw className="w-4 h-4" /> Regenerate
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex items-center gap-3 rounded-3xl border border-white/10 bg-slate-900/90 p-4">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                    <Sparkles className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground">Lucy AI is typing</p>
                    <p className="text-xs text-muted">Generating the next tailored response.</p>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                {PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => selectPrompt(prompt)}
                    className="rounded-full border border-white/10 bg-slate-900/80 px-4 py-2 text-sm text-muted transition hover:border-primary/40 hover:text-foreground"
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
                <div className="rounded-3xl border border-white/10 bg-slate-900/80 p-4 flex items-center gap-3">
                  <button type="button" className="inline-flex items-center justify-center rounded-2xl border border-white/10 bg-slate-950/80 p-3 text-muted hover:text-foreground hover:border-primary/40 transition">
                    <Paperclip className="w-4 h-4" />
                  </button>
                  <Input
                    placeholder="Ask Lucy AI anything..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    className="bg-transparent border-0 p-0 text-sm text-foreground placeholder:text-muted focus:ring-0"
                  />
                </div>
                <Button onClick={handleSend} className="rounded-full px-6 py-3">
                  <Send className="w-4 h-4" /> Send
                </Button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
