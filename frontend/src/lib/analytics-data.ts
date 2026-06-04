export interface TopMetric {
  label: string;
  value: string;
  delta: string;
  trend: "up" | "down" | "flat";
  detail: string;
}

export interface ChartPoint {
  label: string;
  value: number;
}

export interface StatusMetric {
  label: string;
  value: string;
  status: "Healthy" | "Warning" | "Offline";
}

export interface ActivityItem {
  id: string;
  title: string;
  category: string;
  detail: string;
  time: string;
  badge: string;
}

export const TOP_METRICS: TopMetric[] = [
  { label: "Total Executions", value: "12.8k", delta: "+12%", trend: "up", detail: "Monthly execution volume" },
  { label: "Active Agents", value: "28", delta: "+25%", trend: "up", detail: "Agents online this week" },
  { label: "Cache Hit Rate", value: "82.4%", delta: "+5%", trend: "up", detail: "Redis cache efficiency" },
  { label: "Avg. Response Time", value: "420ms", delta: "-4%", trend: "down", detail: "Average agent latency" },
  { label: "Completed Tasks", value: "7.2k", delta: "+18%", trend: "up", detail: "Tasks closed successfully" },
  { label: "AI Requests", value: "49.1k", delta: "+9%", trend: "up", detail: "Calls processed this month" },
];

export const AGENT_USAGE = [
  { label: "Research Agent", value: 27, color: "#a78bfa" },
  { label: "Portfolio Agent", value: 18, color: "#818cf8" },
  { label: "Recruiter Agent", value: 16, color: "#34d399" },
  { label: "Client Agent", value: 12, color: "#fb7185" },
  { label: "Recommendation Agent", value: 10, color: "#38bdf8" },
  { label: "Project Explainer Agent", value: 7, color: "#c084fc" },
];

export const EXECUTION_TRENDS: ChartPoint[] = [
  { label: "Mon", value: 860 },
  { label: "Tue", value: 1120 },
  { label: "Wed", value: 980 },
  { label: "Thu", value: 1230 },
  { label: "Fri", value: 1420 },
  { label: "Sat", value: 1310 },
  { label: "Sun", value: 1550 },
];

export const TOP_AGENTS = [
  { label: "Research Agent", value: 28 },
  { label: "Portfolio Agent", value: 22 },
  { label: "Recruiter Agent", value: 19 },
  { label: "Client Agent", value: 14 },
  { label: "Recommendation Agent", value: 12 },
  { label: "Project Explainer Agent", value: 9 },
];

export const TASK_METRICS = [
  { label: "Pending Tasks", value: "138" },
  { label: "Running Tasks", value: "64" },
  { label: "Completed Tasks", value: "7.2k" },
  { label: "Failed Tasks", value: "18" },
];

export const TASK_COMPLETION_RATE = [
  { label: "Completed", value: 72 },
  { label: "Pending", value: 14 },
  { label: "Running", value: 9 },
  { label: "Failed", value: 5 },
];

export const TASK_GROWTH = [
  { label: "Week 1", value: 740 },
  { label: "Week 2", value: 820 },
  { label: "Week 3", value: 910 },
  { label: "Week 4", value: 1050 },
];

export const CACHE_METRICS = [
  { label: "Redis Cache Hits", value: "102.4k" },
  { label: "Redis Cache Misses", value: "21.8k" },
  { label: "Cache Efficiency", value: "82.4%" },
];

export const CACHE_PERFORMANCE = [
  { label: "Avg. Hit Time", value: 120 },
  { label: "Avg. Miss Time", value: 680 },
  { label: "Effective Speedup", value: 5.7 },
];

export const RESPONSE_TIME_IMPROVEMENT = [
  { label: "Jan", value: 540 },
  { label: "Feb", value: 480 },
  { label: "Mar", value: 430 },
  { label: "Apr", value: 390 },
  { label: "May", value: 360 },
  { label: "Jun", value: 320 },
];

export const GEMINI_METRICS = [
  { label: "Total AI Calls", value: "49.1k" },
  { label: "Saved Calls Through Cache", value: "22.5k" },
  { label: "Avg. Tokens", value: "1.2k" },
  { label: "Estimated Cost Saved", value: "$8.4k" },
];

export const SYSTEM_STATUS: StatusMetric[] = [
  { label: "Redis Status", value: "Healthy", status: "Healthy" },
  { label: "Celery Status", value: "Warning", status: "Warning" },
  { label: "PostgreSQL Status", value: "Healthy", status: "Healthy" },
  { label: "WebSocket Status", value: "Offline", status: "Offline" },
  { label: "Gemini Status", value: "Healthy", status: "Healthy" },
];

export const ACTIVITY_FEED: ActivityItem[] = [
  { id: "activity-1", title: "Execution completed", category: "Agent", detail: "Research Agent finished 210 items in 34 minutes.", time: "5m ago", badge: "Live" },
  { id: "activity-2", title: "New task queued", category: "Task", detail: "Portfolio Agent received a new project analysis request.", time: "12m ago", badge: "Pending" },
  { id: "activity-3", title: "Cache hit spike", category: "Cache", detail: "Redis cache efficiency improved after recent warm-up.", time: "45m ago", badge: "Stable" },
  { id: "activity-4", title: "Report generated", category: "Report", detail: "Gemini analytics report is ready for review.", time: "1h ago", badge: "Ready" },
];
