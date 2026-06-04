"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dropdown } from "@/components/ui/dropdown";
import { Calendar, Video, Clock, User, Plus, CheckCircle2, ChevronRight } from "lucide-react";

interface Meeting {
  id: string;
  title: string;
  type: string;
  date: string;
  time: string;
  agent: string;
  interviewer: string;
  status: "Scheduled" | "Completed" | "Cancelled";
}

const INITIAL_MEETINGS: Meeting[] = [
  {
    id: "meet-1",
    title: "Intro Call with ABC Corp",
    type: "Recruiter Screen",
    date: "2026-06-12",
    time: "10:00 AM - 10:30 AM",
    agent: "Recruiter Agent",
    interviewer: "Alexander Mercer (Director of Engineering)",
    status: "Scheduled"
  },
  {
    id: "meet-2",
    title: "Technical Showcase & Code Review",
    type: "Deep Dive Review",
    date: "2026-06-16",
    time: "02:00 PM - 03:00 PM",
    agent: "Project Explainer Agent",
    interviewer: "Elena Rostova (Co-Founder)",
    status: "Scheduled"
  },
  {
    id: "meet-3",
    title: "Platform Onboarding Session",
    type: "Consultancy Kickoff",
    date: "2026-05-24",
    time: "11:00 AM - 11:30 AM",
    agent: "Client Agent",
    interviewer: "Sarah Jenkins (DevOps Lead)",
    status: "Completed"
  }
];

const COORDINATORS = [
  { value: "Recruiter Agent", label: "Recruiter Agent" },
  { value: "Project Explainer Agent", label: "Project Explainer Agent" },
  { value: "Client Agent", label: "Client Agent" }
];

export default function MeetingsPage() {
  const [meetings, setMeetings] = React.useState<Meeting[]>(INITIAL_MEETINGS);
  const [title, setTitle] = React.useState("");
  const [date, setDate] = React.useState("");
  const [time, setTime] = React.useState("");
  const [agent, setAgent] = React.useState(COORDINATORS[0].value);
  const [interviewer, setInterviewer] = React.useState("");
  const [showSuccess, setShowSuccess] = React.useState(false);

  const upcomingMeetings = meetings.filter((x) => x.status === "Scheduled");
  const pastMeetings = meetings.filter((x) => x.status === "Completed");

  const handleSchedule = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuccess(false);

    if (!title.trim() || !date || !time || !interviewer.trim()) {
      alert("Please fill in all scheduling fields.");
      return;
    }

    const newMeeting: Meeting = {
      id: `meet-${Date.now()}`,
      title,
      type: "Portfolio Technical Review",
      date,
      time,
      agent,
      interviewer,
      status: "Scheduled"
    };

    setMeetings((prev) => [newMeeting, ...prev]);
    setShowSuccess(true);
    
    // Reset Form
    setTitle("");
    setDate("");
    setTime("");
    setInterviewer("");
  };

  const handleJoin = (title: string) => {
    alert(`Launching Jitsi/Google Meet link for "${title}"... (Mock Conference integration)`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel rounded-3xl border border-white/10 p-6">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-primary/80">Calendar Hub</p>
          <h1 className="text-3xl font-bold text-foreground">Meetings & Scheduling</h1>
          <p className="max-w-2xl text-sm text-muted mt-2">
            Schedule automatic portfolio walkthroughs with explanatory agents or coordinate recruiter interviews.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_1fr] gap-6">
        {/* Left Panel: Meetings list */}
        <div className="space-y-6">
          {/* Upcoming Meetings */}
          <Card className="glass-panel rounded-3xl border border-white/10">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Video className="w-5 h-5 text-accent" />
                Upcoming Meetings ({upcomingMeetings.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-0">
              {upcomingMeetings.length > 0 ? (
                upcomingMeetings.map((meet) => (
                  <div key={meet.id} className="p-5 rounded-2xl bg-slate-950/50 border border-white/5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:border-accent/30 transition">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge className="bg-accent/15 border border-accent/20 text-accent text-[10px] rounded-full">
                          {meet.type}
                        </Badge>
                        <Badge className="bg-slate-900 border border-white/5 text-muted text-[10px] rounded-full">
                          {meet.agent}
                        </Badge>
                      </div>
                      <h4 className="text-base font-bold text-foreground">{meet.title}</h4>
                      <p className="text-xs text-muted flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-muted" />
                        Host: {meet.interviewer}
                      </p>
                    </div>

                    <div className="flex flex-col md:items-end gap-3 w-full md:w-auto">
                      <div className="text-left md:text-right font-mono text-xs text-foreground/90">
                        <div className="flex items-center gap-1.5 md:justify-end">
                          <Calendar className="w-3.5 h-3.5 text-muted" />
                          {meet.date}
                        </div>
                        <div className="flex items-center gap-1.5 md:justify-end mt-1">
                          <Clock className="w-3.5 h-3.5 text-muted" />
                          {meet.time}
                        </div>
                      </div>
                      <Button variant="primary" size="sm" onClick={() => handleJoin(meet.title)} className="w-full md:w-auto">
                        Join Call
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center p-8">
                  <p className="text-sm text-muted">No upcoming conferences scheduled.</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Past Meetings */}
          <Card className="glass-panel rounded-3xl border border-white/10">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                Completed Meetings ({pastMeetings.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              {pastMeetings.map((meet) => (
                <div key={meet.id} className="p-4 rounded-2xl bg-slate-900/30 border border-white/5 flex justify-between items-center text-sm">
                  <div>
                    <h5 className="font-semibold text-foreground">{meet.title}</h5>
                    <p className="text-xs text-muted mt-0.5">With {meet.interviewer} • {meet.date}</p>
                  </div>
                  <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] rounded-full">
                    Completed
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Right Panel: Scheduling Form */}
        <div>
          <Card className="glass-panel rounded-3xl border border-white/10">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Plus className="w-5 h-5 text-primary" />
                Schedule Mock Interview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSchedule} className="space-y-4">
                {showSuccess && (
                  <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-200 text-xs">
                    <CheckCircle2 className="w-4.5 h-4.5 flex-shrink-0 text-emerald-400" />
                    <span>Meeting created! View it in the upcoming list.</span>
                  </div>
                )}

                <Input
                  label="Meeting Title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Introductory screening or tech review"
                />

                <Input
                  label="Interviewer Name"
                  value={interviewer}
                  onChange={(e) => setInterviewer(e.target.value)}
                  placeholder="e.g. John Doe (Tech Lead)"
                />

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground/80 tracking-wide block">Date</label>
                    <input
                      type="date"
                      value={date}
                      onChange={(e) => setDate(e.target.value)}
                      className="w-full rounded-2xl bg-slate-950 border border-white/10 p-3 text-xs text-foreground focus:outline-none"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground/80 tracking-wide block">Time Range</label>
                    <input
                      type="text"
                      placeholder="e.g. 10:00 AM - 11:00 AM"
                      value={time}
                      onChange={(e) => setTime(e.target.value)}
                      className="w-full rounded-2xl bg-slate-950 border border-white/10 p-3 text-xs text-foreground focus:outline-none"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground/80 tracking-wide block">Agent Coordinator</label>
                  <select
                    value={agent}
                    onChange={(e) => setAgent(e.target.value)}
                    className="w-full rounded-2xl bg-slate-950 border border-white/10 p-3 text-xs text-foreground focus:outline-none"
                  >
                    {COORDINATORS.map((x) => (
                      <option key={x.value} value={x.value}>{x.label}</option>
                    ))}
                  </select>
                </div>

                <Button type="submit" variant="primary" className="w-full py-2.5 mt-2">
                  Confirm Schedule
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
