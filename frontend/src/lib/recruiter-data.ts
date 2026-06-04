export type SkillLevel = "Beginner" | "Intermediate" | "Advanced" | "Expert";

export interface ProjectSummary {
  id: string;
  title: string;
  description: string;
  repoUrl?: string;
  codeQualityScore: number; // 0-100
  backendReady: boolean;
}

export interface Candidate {
  id: string;
  name: string;
  title: string;
  summary: string;
  experienceYears: number;
  skills: Record<string, SkillLevel>;
  projects: ProjectSummary[];
  resumeUrl?: string;
}

export interface CandidateEvaluation {
  readinessScore: number; // 0-100
  technicalAnalysis: Record<string, { score: number; comment: string }>;
  missingSkills: string[];
  recommendation: "Strong Hire" | "Consider" | "Reject";
}

export const MOCK_CANDIDATES: Candidate[] = [
  {
    id: "cand-1",
    name: "Aisha Khan",
    title: "Senior Backend Engineer",
    summary: "Experienced backend engineer focused on scalable APIs and distributed systems.",
    experienceYears: 7,
    skills: {
      Python: "Expert",
      Django: "Expert",
      PostgreSQL: "Advanced",
      Redis: "Intermediate",
      Docker: "Advanced",
      Kubernetes: "Intermediate",
      "Machine Learning": "Beginner",
    },
    projects: [
      {
        id: "proj-1",
        title: "Realtime Recommendation Service",
        description: "Built a recommendation microservice with event-driven architecture and Redis caching.",
        repoUrl: "https://github.com/example/reco-service",
        codeQualityScore: 86,
        backendReady: true,
      },
      {
        id: "proj-2",
        title: "Analytics Pipeline",
        description: "Data ingestion and transformation pipeline for usage analytics.",
        repoUrl: "https://github.com/example/analytics",
        codeQualityScore: 78,
        backendReady: false,
      },
    ],
    resumeUrl: "",
  },
  {
    id: "cand-2",
    name: "Michael Chen",
    title: "Full Stack Engineer",
    summary: "Full stack generalist with strong frontend and growing backend experience.",
    experienceYears: 4,
    skills: {
      TypeScript: "Advanced",
      React: "Advanced",
      Node: "Intermediate",
      PostgreSQL: "Intermediate",
      Docker: "Intermediate",
      "System Design": "Beginner",
    },
    projects: [
      {
        id: "proj-3",
        title: "Portfolio Builder",
        description: "A platform to create and host developer portfolios.",
        repoUrl: "https://github.com/example/portfolio",
        codeQualityScore: 81,
        backendReady: true,
      },
    ],
    resumeUrl: "",
  },
];

export function evaluateCandidate(candidateId: string) : CandidateEvaluation {
  const candidate = MOCK_CANDIDATES.find((c) => c.id === candidateId);
  if (!candidate) {
    return {
      readinessScore: 0,
      technicalAnalysis: {},
      missingSkills: [],
      recommendation: "Reject",
    };
  }

  const desiredSkills = ["Python", "Django", "PostgreSQL", "Redis", "Docker"];
  const technicalAnalysis: Record<string, { score: number; comment: string }> = {};
  let scoreSum = 0;
  let count = 0;

  Object.entries(candidate.skills).forEach(([skill, level]) => {
    const base = level === "Expert" ? 100 : level === "Advanced" ? 85 : level === "Intermediate" ? 65 : 40;
    technicalAnalysis[skill] = { score: base, comment: `${skill} rated ${level}` };
    scoreSum += base;
    count += 1;
  });

  const missingSkills = desiredSkills.filter((s) => !(s in candidate.skills));

  const readinessScore = Math.round(scoreSum / Math.max(1, count));
  let recommendation: CandidateEvaluation["recommendation"] = "Consider";
  if (readinessScore >= 85 && missingSkills.length === 0) recommendation = "Strong Hire";
  if (readinessScore < 55) recommendation = "Reject";

  return {
    readinessScore,
    technicalAnalysis,
    missingSkills,
    recommendation,
  };
}
