export type ResearchAgentType =
  | "Research"
  | "Portfolio"
  | "Recruiter"
  | "Client"
  | "Recommendation"
  | "Project Explainer";

export type ResearchStatus = "Pending" | "Running" | "Completed" | "Failed";
export type ResearchPriority = "Low" | "Medium" | "High";

export interface ResearchTimelineStep {
  label: string;
  date: string;
  status: "complete" | "current" | "upcoming";
}

export interface ResearchLog {
  id: string;
  event: string;
  details: string;
  timestamp: string;
  duration: string;
}

export interface ResearchTask {
  id: string;
  title: string;
  query: string;
  agentType: ResearchAgentType;
  status: ResearchStatus;
  createdAt: string;
  priority: ResearchPriority;
  result: string;
  timeline: ResearchTimelineStep[];
  logs: ResearchLog[];
}

export interface ResearchStats {
  totalTasks: number;
  runningTasks: number;
  completedTasks: number;
  failedTasks: number;
  trends: number[];
  usage: number[];
  completionRate: number;
}

export const RESEARCH_TASKS: ResearchTask[] = [
  {
    id: "research-101",
    title: "AI hiring market trend analysis",
    query: "Analyze hiring trends for AI engineers in 2026.",
    agentType: "Research",
    status: "Running",
    createdAt: "2026-06-04",
    priority: "High",
    result: "Scanning top AI job boards and recent surveys for hiring momentum.",
    timeline: [
      { label: "Task Created", date: "2026-06-04 08:00", status: "complete" },
      { label: "Agent Started", date: "2026-06-04 08:05", status: "complete" },
      { label: "Processing", date: "2026-06-04 08:12", status: "current" },
      { label: "Completed", date: "--", status: "upcoming" },
    ],
    logs: [
      { id: "log-1", event: "Query processed", details: "Parsed research keywords and context.", timestamp: "08:05", duration: "0.3s" },
      { id: "log-2", event: "Data source lookup", details: "Retrieved market reports and job listings.", timestamp: "08:07", duration: "0.8s" },
      { id: "log-3", event: "Summary drafted", details: "Created initial findings summary.", timestamp: "08:12", duration: "1.2s" },
    ],
  },
  {
    id: "research-102",
    title: "Portfolio storytelling brief",
    query: "Build a narrative for the AI portfolio that highlights backend and research expertise.",
    agentType: "Portfolio",
    status: "Pending",
    createdAt: "2026-06-03",
    priority: "Medium",
    result: "Awaiting agent execution.",
    timeline: [
      { label: "Task Created", date: "2026-06-03 17:22", status: "complete" },
      { label: "Agent Started", date: "--", status: "upcoming" },
      { label: "Processing", date: "--", status: "upcoming" },
      { label: "Completed", date: "--", status: "upcoming" },
    ],
    logs: [
      { id: "log-4", event: "Task queued", details: "Task entered the pending queue.", timestamp: "17:22", duration: "0.1s" },
    ],
  },
  {
    id: "research-103",
    title: "Recruiter outreach optimization",
    query: "Identify the top messaging patterns for recruiter follow-up.",
    agentType: "Recruiter",
    status: "Completed",
    createdAt: "2026-06-02",
    priority: "High",
    result: "Created a set of optimized recruiter outreach templates with personalization cues.",
    timeline: [
      { label: "Task Created", date: "2026-06-02 13:03", status: "complete" },
      { label: "Agent Started", date: "2026-06-02 13:05", status: "complete" },
      { label: "Processing", date: "2026-06-02 13:09", status: "complete" },
      { label: "Completed", date: "2026-06-02 13:12", status: "complete" },
    ],
    logs: [
      { id: "log-5", event: "Dialogue patterns analyzed", details: "Evaluated engagement metrics for messaging.", timestamp: "13:05", duration: "0.8s" },
      { id: "log-6", event: "Template generated", details: "Produced three outreach variations.", timestamp: "13:09", duration: "1.3s" },
    ],
  },
  {
    id: "research-104",
    title: "Client persona briefing",
    query: "Compile a client persona for product marketing outreach.",
    agentType: "Client",
    status: "Failed",
    createdAt: "2026-05-30",
    priority: "Low",
    result: "Failed due to missing data sources; retry with expanded input.",
    timeline: [
      { label: "Task Created", date: "2026-05-30 09:10", status: "complete" },
      { label: "Agent Started", date: "2026-05-30 09:12", status: "complete" },
      { label: "Processing", date: "2026-05-30 09:15", status: "complete" },
      { label: "Completed", date: "2026-05-30 09:18", status: "complete" },
    ],
    logs: [
      { id: "log-7", event: "Source validation failed", details: "Required client dataset not available.", timestamp: "09:15", duration: "0.5s" },
      { id: "log-8", event: "Task failed", details: "Marked task as failed for review.", timestamp: "09:18", duration: "0.2s" },
    ],
  },
  {
    id: "research-105",
    title: "Recommendation engine benchmark",
    query: "Compare common recommendation algorithms for tech hiring products.",
    agentType: "Recommendation",
    status: "Completed",
    createdAt: "2026-05-28",
    priority: "Medium",
    result: "Benchmarked collaborative filtering, content-based, and hybrid systems.",
    timeline: [
      { label: "Task Created", date: "2026-05-28 11:40", status: "complete" },
      { label: "Agent Started", date: "2026-05-28 11:42", status: "complete" },
      { label: "Processing", date: "2026-05-28 11:50", status: "complete" },
      { label: "Completed", date: "2026-05-28 11:56", status: "complete" },
    ],
    logs: [
      { id: "log-9", event: "Algorithm set loaded", details: "Prepared recommendation patterns for comparison.", timestamp: "11:42", duration: "1.0s" },
      { id: "log-10", event: "Report assembled", details: "Generated benchmark summary.", timestamp: "11:56", duration: "0.9s" },
    ],
  },
  {
    id: "research-106",
    title: "Project explainer draft",
    query: "Write a summary explaining the portfolio platform architecture.",
    agentType: "Project Explainer",
    status: "Pending",
    createdAt: "2026-06-01",
    priority: "Low",
    result: "Awaiting step-by-step agent execution.",
    timeline: [
      { label: "Task Created", date: "2026-06-01 14:00", status: "complete" },
      { label: "Agent Started", date: "--", status: "upcoming" },
      { label: "Processing", date: "--", status: "upcoming" },
      { label: "Completed", date: "--", status: "upcoming" },
    ],
    logs: [
      { id: "log-11", event: "Awaiting execution", details: "This task has not started yet.", timestamp: "14:00", duration: "0.0s" },
    ],
  },
];

export const RESEARCH_STATS: ResearchStats = {
  totalTasks: RESEARCH_TASKS.length,
  runningTasks: RESEARCH_TASKS.filter((task) => task.status === "Running").length,
  completedTasks: RESEARCH_TASKS.filter((task) => task.status === "Completed").length,
  failedTasks: RESEARCH_TASKS.filter((task) => task.status === "Failed").length,
  trends: [4, 5, 7, 6, 8, 9],
  usage: [15, 18, 22, 19, 26, 30],
  completionRate: 74,
};
