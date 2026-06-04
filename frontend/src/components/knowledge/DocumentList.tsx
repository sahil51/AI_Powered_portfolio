"use client";

import * as React from "react";
import { KBDocument } from "@/lib/knowledge-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface DocumentListProps {
  documents: KBDocument[];
  onOpen: (doc: KBDocument) => void;
}

export default function DocumentList({ documents, onOpen }: DocumentListProps) {
  const [filter, setFilter] = React.useState("");

  const filtered = documents.filter((d) => d.title.toLowerCase().includes(filter.toLowerCase()) || d.category.toLowerCase().includes(filter.toLowerCase()));

  return (
    <Card className="rounded-3xl border border-white/10 p-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Document Library</CardTitle>
        <p className="text-sm text-muted">Search, filter, and preview uploaded documents</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <Input placeholder="Search documents or categories" value={filter} onChange={(e) => setFilter(e.target.value)} />
        <div className="grid gap-3">
          {filtered.map((doc) => (
            <button key={doc.id} onClick={() => onOpen(doc)} className="text-left rounded-2xl p-3 border border-white/5 bg-slate-950/50 hover:border-primary/40">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-foreground">{doc.title}</p>
                  <p className="text-xs text-muted">{doc.category} • {doc.uploadedAt} • {doc.pages ?? "-"} pages</p>
                </div>
                <div className="text-sm text-muted">Preview</div>
              </div>
            </button>
          ))}
          {filtered.length === 0 && <p className="text-sm text-muted">No documents found.</p>}
        </div>
      </CardContent>
    </Card>
  );
}
