"use client";

import * as React from "react";
import KnowledgeStats from "@/components/knowledge/KnowledgeStats";
import DocumentList from "@/components/knowledge/DocumentList";
import UploadCenter from "@/components/knowledge/UploadCenter";
import VectorSearch from "@/components/knowledge/VectorSearch";
import DocumentViewer from "@/components/knowledge/DocumentViewer";
import SavedReports from "@/components/knowledge/SavedReports";
import { KB_DOCS, KB_STATS, SAVED_REPORTS } from "@/lib/knowledge-data";

export default function KnowledgePage() {
  const [documents, setDocuments] = React.useState(KB_DOCS);
  const [selected, setSelected] = React.useState<typeof KB_DOCS[0] | null>(KB_DOCS[0] ?? null);

  const handleOpen = (doc: typeof KB_DOCS[0]) => setSelected(doc);
  const handleDelete = (id: string) => setDocuments((d) => d.filter((x) => x.id !== id));

  return (
    <div className="space-y-8 pb-16">
      <div className="glass-panel rounded-3xl border border-white/10 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-primary/80">Knowledge Base</p>
            <h1 className="text-3xl font-bold text-foreground">RAG & Document Management</h1>
            <p className="max-w-2xl text-sm text-muted">Upload documents, create embeddings, and run semantic search across your knowledge assets.</p>
          </div>
        </div>
      </div>

      <KnowledgeStats documents={KB_STATS.documents} embeddings={KB_STATS.embeddings} notes={KB_STATS.researchNotes} reports={KB_STATS.reports} />

      <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <aside className="space-y-4">
          <UploadCenter />
          <SavedReports reports={SAVED_REPORTS} />
        </aside>

        <main className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <DocumentList documents={documents} onOpen={handleOpen} />
            <VectorSearch documents={documents} onOpen={handleOpen} />
          </div>

          <DocumentViewer doc={selected} onDelete={handleDelete} />
        </main>
      </div>
    </div>
  );
}
