"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  MessageSquare, 
  Send, 
  Paperclip, 
  User, 
  Search, 
  Trash2, 
  CheckCheck,
  Bot
} from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "other";
  text: string;
  timestamp: string;
}

interface ChatSession {
  id: string;
  name: string;
  role: string;
  online: boolean;
  avatarInitials: string;
  messages: Message[];
}

const INITIAL_CHATS: ChatSession[] = [
  {
    id: "chat-1",
    name: "Alexander Mercer",
    role: "Director of Engineering @ Synapse",
    online: true,
    avatarInitials: "AM",
    messages: [
      { id: "m1", sender: "other", text: "Hey Lucy, your experience with Celery queues looks very relevant to our backlog issues. Are you open to a technical screen?", timestamp: "Yesterday 04:12 PM" },
      { id: "m2", sender: "user", text: "Hi Alexander! Yes, absolutely. I restructured Synapse style celery brokers to solve priority queue issues. Let's schedule a call.", timestamp: "Yesterday 04:30 PM" },
      { id: "m3", sender: "other", text: "Perfect. I'll have the system send over calendar options.", timestamp: "Yesterday 04:32 PM" }
    ]
  },
  {
    id: "chat-2",
    name: "Elena Rostova",
    role: "Co-Founder @ Velo Cart",
    online: true,
    avatarInitials: "ER",
    messages: [
      { id: "m4", sender: "other", text: "Stripe payment integration you designed is solid. What is your billing capacity for Q3 contracts?", timestamp: "2h ago" },
      { id: "m5", sender: "user", text: "Thanks Elena! I'll outline my consulting rate details. We can host payments securely.", timestamp: "1h ago" }
    ]
  },
  {
    id: "chat-3",
    name: "Marcus Vance",
    role: "VP of Product @ OmniAI",
    online: false,
    avatarInitials: "MV",
    messages: [
      { id: "m6", sender: "other", text: "Can we request an updated resume evaluation report?", timestamp: "May 28" }
    ]
  }
];

export default function MessagesPage() {
  const [chats, setChats] = React.useState<ChatSession[]>(INITIAL_CHATS);
  const [selectedId, setSelectedId] = React.useState(chats[0].id);
  const [inputText, setInputText] = React.useState("");
  const [isTyping, setIsTyping] = React.useState(false);
  const [search, setSearch] = React.useState("");

  const activeChat = React.useMemo(() => {
    return chats.find((x) => x.id === selectedId) ?? chats[0];
  }, [chats, selectedId]);

  const filteredChats = React.useMemo(() => {
    return chats.filter((x) => x.name.toLowerCase().includes(search.toLowerCase()) || x.role.toLowerCase().includes(search.toLowerCase()));
  }, [chats, search]);

  const handleSend = () => {
    if (!inputText.trim()) return;

    const newMessage: Message = {
      id: `msg-${Date.now()}`,
      sender: "user",
      text: inputText.trim(),
      timestamp: "Just Now"
    };

    setChats((prev) =>
      prev.map((c) =>
        c.id === activeChat.id
          ? { ...c, messages: [...c.messages, newMessage] }
          : c
      )
    );
    
    setInputText("");
    setIsTyping(true);

    // Simulate recruiter reply
    setTimeout(() => {
      const replyMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        sender: "other",
        text: `Thanks for the details! This is an automated mock reply from ${activeChat.name}. I'll review and get back to you shortly.`,
        timestamp: "Just Now"
      };

      setChats((prev) =>
        prev.map((c) =>
          c.id === activeChat.id
            ? { ...c, messages: [...c.messages, replyMessage] }
            : c
        )
      );
      setIsTyping(false);
    }, 1200);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  const handleClearChat = () => {
    if (confirm(`Clear all messages with ${activeChat.name}?`)) {
      setChats((prev) =>
        prev.map((c) => (c.id === activeChat.id ? { ...c, messages: [] } : c))
      );
    }
  };

  return (
    <div className="space-y-6 h-[calc(100vh-140px)] flex flex-col">
      {/* Header */}
      <div className="glass-panel rounded-3xl border border-white/10 p-5 flex items-center justify-between shrink-0">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-primary/80">Communications</p>
          <h1 className="text-2xl font-bold text-foreground">Message Center</h1>
        </div>
        <Badge className="bg-primary/20 text-primary border border-primary/30 text-xs rounded-full">
          Real-time Simulation
        </Badge>
      </div>

      {/* Main chat layout */}
      <div className="flex-grow grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6 overflow-hidden min-h-0">
        
        {/* Left Side: Contact List */}
        <aside className="glass-panel rounded-3xl border border-white/10 p-4 flex flex-col gap-4 overflow-hidden h-full">
          {/* Search Box */}
          <div className="relative shrink-0">
            <Input
              type="text"
              placeholder="Search conversations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="w-4 h-4 text-muted" />}
              className="w-full text-xs"
            />
          </div>

          {/* List area */}
          <div className="flex-grow overflow-y-auto space-y-2 pr-1">
            {filteredChats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => setSelectedId(chat.id)}
                className={`w-full p-3 rounded-2xl border text-left flex gap-3 items-center transition-all ${
                  selectedId === chat.id
                    ? "bg-primary/10 border-primary/20 text-foreground"
                    : "bg-slate-950/40 border-white/5 text-muted hover:border-primary/40 hover:text-foreground"
                }`}
              >
                {/* Avatar */}
                <div className="w-10 h-10 rounded-xl bg-slate-900 border border-white/10 flex items-center justify-center font-bold text-foreground relative shrink-0">
                  {chat.avatarInitials}
                  {chat.online && (
                    <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-slate-950" />
                  )}
                </div>

                {/* Details snippet */}
                <div className="min-w-0 flex-grow">
                  <div className="flex justify-between items-baseline gap-2">
                    <h4 className="text-sm font-semibold text-foreground truncate">{chat.name}</h4>
                  </div>
                  <p className="text-xs text-muted truncate mt-0.5">{chat.role}</p>
                </div>
              </button>
            ))}
          </div>
        </aside>

        {/* Right Side: Conversation Console */}
        <main className="glass-panel rounded-3xl border border-white/10 flex flex-col overflow-hidden h-full">
          {/* Header detail bar */}
          <div className="px-5 py-4 border-b border-white/5 bg-slate-950/20 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center font-bold text-primary">
                {activeChat.avatarInitials}
              </div>
              <div>
                <h3 className="text-sm font-bold text-foreground">{activeChat.name}</h3>
                <p className="text-xs text-muted">{activeChat.role}</p>
              </div>
            </div>

            <Button variant="ghost" size="sm" onClick={handleClearChat} className="text-muted hover:text-rose-400">
              <Trash2 className="w-4.5 h-4.5" />
            </Button>
          </div>

          {/* Messages stream */}
          <div className="flex-grow overflow-y-auto p-5 space-y-4 bg-slate-950/5">
            {activeChat.messages.length > 0 ? (
              activeChat.messages.map((msg) => {
                const isUser = msg.sender === "user";
                return (
                  <div key={msg.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[75%] rounded-3xl border px-4 py-3 shadow-sm space-y-1 ${
                      isUser 
                        ? "bg-primary/10 border-primary/20 text-foreground" 
                        : "bg-slate-900 border-white/5 text-foreground/90"
                    }`}>
                      <p className="text-xs sm:text-sm leading-relaxed">{msg.text}</p>
                      <div className="flex items-center justify-end gap-1 text-[9px] text-muted">
                        <span>{msg.timestamp}</span>
                        {isUser && <CheckCheck className="w-3.5 h-3.5 text-accent" />}
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="h-full flex items-center justify-center text-center p-8 text-muted text-xs">
                No conversation history yet. Send a message to initiate.
              </div>
            )}

            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-slate-900 border border-white/5 text-muted px-4 py-2.5 rounded-3xl text-xs flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce [animation-delay:0.2s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-muted animate-bounce [animation-delay:0.4s]" />
                  <span>{activeChat.name} is typing...</span>
                </div>
              </div>
            )}
          </div>

          {/* Text Input area */}
          <div className="p-4 border-t border-white/5 bg-slate-950/20 shrink-0">
            <div className="grid grid-cols-[auto_1fr_auto] gap-3 items-center">
              <button 
                type="button" 
                onClick={() => alert("Upload file/image (Mock integration)")}
                className="w-11 h-11 rounded-2xl bg-slate-900 border border-white/5 flex items-center justify-center text-muted hover:text-foreground hover:border-primary/30 transition shrink-0"
              >
                <Paperclip className="w-4.5 h-4.5" />
              </button>
              
              <input
                type="text"
                placeholder="Type your message details here..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyPress}
                disabled={isTyping}
                className="w-full h-11 rounded-2xl bg-slate-950 border border-white/10 px-4 text-sm text-foreground focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all duration-300"
              />

              <Button onClick={handleSend} disabled={isTyping} className="h-11 rounded-2xl px-5 shrink-0">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
