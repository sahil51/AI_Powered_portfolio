"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  User, 
  Mail, 
  Globe, 
  UploadCloud, 
  Check, 
  Settings2, 
  Share2, 
  ShieldAlert 
} from "lucide-react";

export default function ProfilePage() {
  // Mock State
  const [name, setName] = React.useState("Lucy AI");
  const [email, setEmail] = React.useState("lucy@agentplatform.ai");
  const [bio, setBio] = React.useState("Distributed backend architect & AI Multi-agent platform engineer focused on Celery, Redis, and LLM orchestration.");
  const [website, setWebsite] = React.useState("https://lucy.ai");
  const [github, setGithub] = React.useState("https://github.com");
  const [linkedin, setLinkedin] = React.useState("https://linkedin.com");
  
  // Settings switches
  const [isPublic, setIsPublic] = React.useState(true);
  const [isAssistantActive, setIsAssistantActive] = React.useState(true);
  const [showLogs, setShowLogs] = React.useState(false);

  // upload state
  const [fileName, setFileName] = React.useState<string | null>("resume_lucy_backend_engineer.pdf");
  const [uploadStatus, setUploadStatus] = React.useState("");

  const handleSave = () => {
    alert("Profile configurations saved successfully!");
  };

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setUploadStatus("Uploading...");
      setTimeout(() => {
        setUploadStatus("Uploaded successfully!");
      }, 1000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel rounded-3xl border border-white/10 p-6">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-primary/80">User Hub</p>
          <h1 className="text-3xl font-bold text-foreground">Profile & Settings</h1>
          <p className="max-w-2xl text-sm text-muted mt-2">
            Configure your recruiter-facing information, bio, social anchors, and download parameters.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_1fr] gap-6">
        {/* Left Side: General Profile Form */}
        <div className="space-y-6">
          <Card className="glass-panel rounded-3xl border border-white/10">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <User className="w-5 h-5 text-primary" />
                General Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Display Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
                <Input
                  label="Email Address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  icon={<Mail className="w-4 h-4" />}
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-foreground/80 tracking-wide block">
                  Short Bio Description
                </label>
                <textarea
                  rows={3}
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  className="w-full rounded-2xl bg-slate-950/70 border border-white/10 p-3 text-sm text-foreground focus:outline-none focus:border-primary/50 transition resize-none"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Website URL"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  icon={<Globe className="w-4 h-4" />}
                />
                <Input
                  label="GitHub Handle"
                  value={github}
                  onChange={(e) => setGithub(e.target.value)}
                />
                <Input
                  label="LinkedIn Profile"
                  value={linkedin}
                  onChange={(e) => setLinkedin(e.target.value)}
                />
              </div>

              <div className="flex justify-end pt-2">
                <Button variant="primary" onClick={handleSave} className="px-6">
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Settings switches */}
          <Card className="glass-panel rounded-3xl border border-white/10">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Settings2 className="w-5 h-5 text-accent" />
                Portfolio Visibility Parameters
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between gap-4 p-3 rounded-2xl bg-slate-950/40 border border-white/5">
                <div>
                  <p className="text-sm font-semibold text-foreground">Public Portfolio Indexing</p>
                  <p className="text-xs text-muted">Allow search engine spiders and guest recruiters to crawl your portfolio landing pages.</p>
                </div>
                <input
                  type="checkbox"
                  checked={isPublic}
                  onChange={(e) => setIsPublic(e.target.checked)}
                  className="w-4 h-4 rounded text-primary bg-slate-900 border-white/10 focus:ring-primary"
                />
              </div>

              <div className="flex items-center justify-between gap-4 p-3 rounded-2xl bg-slate-950/40 border border-white/5">
                <div>
                  <p className="text-sm font-semibold text-foreground">AI Recruiter Assistant</p>
                  <p className="text-xs text-muted">Activate the chat modal agent to let recruiters interview your credentials dynamically.</p>
                </div>
                <input
                  type="checkbox"
                  checked={isAssistantActive}
                  onChange={(e) => setIsAssistantActive(e.target.checked)}
                  className="w-4 h-4 rounded text-primary bg-slate-900 border-white/10 focus:ring-primary"
                />
              </div>

              <div className="flex items-center justify-between gap-4 p-3 rounded-2xl bg-slate-950/40 border border-white/5">
                <div>
                  <p className="text-sm font-semibold text-foreground">Expose Advanced Telemetry Logs</p>
                  <p className="text-xs text-muted">Make execution logs for validation tasks public inside the dashboard console view.</p>
                </div>
                <input
                  type="checkbox"
                  checked={showLogs}
                  onChange={(e) => setShowLogs(e.target.checked)}
                  className="w-4 h-4 rounded text-primary bg-slate-900 border-white/10 focus:ring-primary"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Side: Resume Upload & Actions */}
        <div className="space-y-6">
          <Card className="glass-panel rounded-3xl border border-white/10">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <UploadCloud className="w-5 h-5 text-primary" />
                Resume Document Upload
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <p className="text-xs text-muted leading-relaxed">
                Upload your primary curriculum vitae. The Recruiter Intelligence parser will automatically analyze your resume and sync RAG embeddings.
              </p>

              {/* Drag & drop box */}
              <div className="border border-dashed border-white/10 rounded-2xl bg-slate-950/60 p-6 text-center hover:border-primary/40 transition relative">
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleUpload}
                  className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                />
                <UploadCloud className="w-10 h-10 text-muted mx-auto mb-2" />
                <p className="text-sm font-semibold text-foreground">Drag file here or click to browse</p>
                <p className="text-[10px] text-muted mt-1">Supports PDF, DOCX (Max 10MB)</p>
              </div>

              {fileName && (
                <div className="flex items-center justify-between gap-2 p-3.5 rounded-2xl bg-slate-900 border border-white/5">
                  <div className="overflow-hidden">
                    <p className="text-xs font-semibold text-foreground truncate">{fileName}</p>
                    <p className="text-[10px] text-emerald-400 mt-0.5">
                      {uploadStatus || "Embeddings synced successfully"}
                    </p>
                  </div>
                  <Badge className="bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px] rounded-full shrink-0">
                    Active
                  </Badge>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Social connections preview */}
          <Card className="glass-panel rounded-3xl border border-white/10">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Share2 className="w-5 h-5 text-accent" />
                Integrations Snapshot
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm text-muted">Google Cloud Platform</span>
                <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] rounded-full">Connected</Badge>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm text-muted">Gemini Pro Token Limit</span>
                <span className="text-sm font-semibold text-foreground">98% Remaining</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm text-muted">Redis Cache Nodes</span>
                <span className="text-sm font-semibold text-foreground">1 Primary / 2 Replica</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
