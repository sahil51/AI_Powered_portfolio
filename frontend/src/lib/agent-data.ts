export type AgentStatus = "Active" | "Inactive" | "Paused";
export type AgentType =
  | "Research Agent"
  | "Portfolio Agent"
  | "Recruiter Agent"
  | "Client Agent"
  | "Recommendation Agent"
  | "Project Explainer Agent";

export interface AgentMemory {
  id: string;
  content: string;
  createdAt: string;
}

export interface AgentExecution {
  id: string;
  prompt: string;
  response: string;
  executionTime: string;
  createdAt: string;
  status: "Success" | "Failed" | "Warning";
}

export interface AgentMetrics {
  totalExecutions: number;
  successRate: number;
  averageResponseTime: number;
  cacheHitRatio: number;
  executionTrend: number[];
  usageTrend: number[];
}

export interface Agent {
  id: string;
  name: string;
  type: AgentType;
  status: AgentStatus;
  createdAt: string;
  lastExecution: string;
  goal: string;
  description: string;
  systemPrompt: string;
  temperature: number;
  maxTokens: number;
  model: string;
  totalExecutions: number;
  metrics: AgentMetrics;
  memory: AgentMemory[];
  executions: AgentExecution[];
}

export const AGENT_TYPES: AgentType[] = [
  "Research Agent",
  "Portfolio Agent",
  "Recruiter Agent",
  "Client Agent",
  "Recommendation Agent",
  "Project Explainer Agent",
];

export const AGENTS: Agent[] = [
  {
    id: "lucy-001",
    name: "Valora Research",
    type: "Research Agent",
    status: "Active",
    createdAt: "2026-02-14",
    lastExecution: "2026-06-03 14:22",
    goal: "Collect market intelligence and summarize competitor positioning.",
    description:
      "A high-speed research assistant trained to extract trend signals from documents and reports.",
    systemPrompt:
      "You are Lucy AI's Research Agent. Focus on evidence-backed market insights and concise summaries.",
    temperature: 0.28,
    maxTokens: 1200,
    model: "gpt-4o-mini",
    totalExecutions: 124,
    metrics: {
      totalExecutions: 124,
      successRate: 94,
      averageResponseTime: 1.6,
      cacheHitRatio: 38,
      executionTrend: [12, 18, 21, 16, 20, 24],
      usageTrend: [8, 12, 15, 14, 16, 19],
    },
    memory: [
      {
        id: "memory-1",
        content: "Referenced Q2 investor deck for new AI hiring trends.",
        createdAt: "2026-05-30",
      },
      {
        id: "memory-2",
        content: "Saved competitor feature comparison for portfolio analysis.",
        createdAt: "2026-06-01",
      },
    ],
    executions: [
      {
        id: "exec-1101",
        prompt: "Summarize the latest survey on AI adoption in finance.",
        response: "The report shows 78% of firms plan to increase AI spend in 2027.",
        executionTime: "1.4s",
        createdAt: "2026-06-03",
        status: "Success",
      },
      {
        id: "exec-1102",
        prompt: "Extract the top three regulatory risks for AI in healthcare.",
        response: "The biggest risks are data privacy, model transparency and compliance drift.",
        executionTime: "1.7s",
        createdAt: "2026-06-02",
        status: "Success",
      },
    ],
  },
  {
    id: "lucy-002",
    name: "Portfolio Genius",
    type: "Portfolio Agent",
    status: "Inactive",
    createdAt: "2026-01-10",
    lastExecution: "2026-05-29 09:52",
    goal: "Create investment narratives and explain work samples for portfolio review.",
    description:
      "An agent focused on structuring portfolio assets and highlighting technical achievements.",
    systemPrompt:
      "You are the Portfolio Agent. Present projects confidently and clearly for technical audiences.",
    temperature: 0.32,
    maxTokens: 1000,
    model: "gpt-4o-mini",
    totalExecutions: 88,
    metrics: {
      totalExecutions: 88,
      successRate: 89,
      averageResponseTime: 1.9,
      cacheHitRatio: 29,
      executionTrend: [9, 14, 12, 11, 14, 18],
      usageTrend: [7, 10, 11, 10, 12, 13],
    },
    memory: [
      {
        id: "memory-3",
        content: "Stored portfolio case study structure for recruiter presentation.",
        createdAt: "2026-05-14",
      },
      {
        id: "memory-4",
        content: "Saved technical skill summary for backend architecture work.",
        createdAt: "2026-05-23",
      },
    ],
    executions: [
      {
        id: "exec-2201",
        prompt: "Build an executive summary for the AI-driven recruiter tool.",
        response: "This tool helps recruiters assess candidate fit using automation and NLP.",
        executionTime: "2.0s",
        createdAt: "2026-05-29",
        status: "Success",
      },
      {
        id: "exec-2202",
        prompt: "List the technologies used in the portfolio platform.",
        response: "Next.js, Django REST, Tailwind CSS, Redis, Celery, Postgres.",
        executionTime: "1.3s",
        createdAt: "2026-05-27",
        status: "Success",
      },
    ],
  },
  {
    id: "lucy-003",
    name: "Talent Scout",
    type: "Recruiter Agent",
    status: "Active",
    createdAt: "2026-03-05",
    lastExecution: "2026-06-04 08:17",
    goal: "Screen candidates and draft recruitment messages for hiring teams.",
    description:
      "A recruiter assistant that helps identify strong candidates and summarize fit.",
    systemPrompt:
      "You are Talent Scout. Focus on candidate strengths, culture fit and recommendation clarity.",
    temperature: 0.35,
    maxTokens: 950,
    model: "gpt-4o-mini",
    totalExecutions: 134,
    metrics: {
      totalExecutions: 134,
      successRate: 91,
      averageResponseTime: 1.5,
      cacheHitRatio: 44,
      executionTrend: [14, 18, 19, 21, 22, 24],
      usageTrend: [12, 15, 16, 15, 17, 20],
    },
    memory: [
      {
        id: "memory-5",
        content: "Saved candidate screening criteria for software engineering roles.",
        createdAt: "2026-06-01",
      },
      {
        id: "memory-6",
        content: "Stored corporate tone for outreach messages.",
        createdAt: "2026-06-02",
      },
    ],
    executions: [
      {
        id: "exec-3301",
        prompt: "Draft a message to a senior engineer about an AI position.",
        response: "Hi Alex, I found a role that aligns with your expertise in AI systems...",
        executionTime: "1.2s",
        createdAt: "2026-06-04",
        status: "Success",
      },
      {
        id: "exec-3302",
        prompt: "Summarize candidate strengths for the interview team.",
        response: "Strong backend design skills, data pipeline experience and leadership potential.",
        executionTime: "1.6s",
        createdAt: "2026-06-03",
        status: "Success",
      },
    ],
  },
];
