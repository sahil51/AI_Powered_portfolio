export interface KBDocument {
  id: string;
  title: string;
  content: string;
  category: string;
  uploadedAt: string;
  pages?: number;
}

export interface SavedReport {
  id: string;
  title: string;
  createdAt: string;
  summary: string;
}

export const KB_DOCS: KBDocument[] = [
  {
    id: "doc-1",
    title: "Lucy AI Platform Overview",
    content: "This document describes the Lucy AI platform architecture, services, and workflows...",
    category: "Platform",
    uploadedAt: "2026-06-01",
    pages: 12,
  },
  {
    id: "doc-2",
    title: "Research Report: AI Hiring Trends",
    content: "A curated research brief summarizing hiring trends and market indicators for 2026...",
    category: "Research",
    uploadedAt: "2026-06-03",
    pages: 8,
  },
  {
    id: "doc-3",
    title: "Recruiter Playbook",
    content: "Guidelines and templates for outreach and evaluation of candidates...",
    category: "Recruiting",
    uploadedAt: "2026-05-30",
    pages: 5,
  },
];

export const SAVED_REPORTS: SavedReport[] = [
  { id: "rep-1", title: "Monthly Agent Usage", createdAt: "2026-06-01", summary: "Top-line agent usage and trends." },
  { id: "rep-2", title: "Recruiter Report - May", createdAt: "2026-05-31", summary: "Candidate evaluations and hiring signals." },
];

export const KB_STATS = {
  documents: KB_DOCS.length,
  embeddings: 12345,
  researchNotes: 34,
  reports: SAVED_REPORTS.length,
};