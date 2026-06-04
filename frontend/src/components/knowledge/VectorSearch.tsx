"use client";

import * as React from "react";
import { KBDocument } from "@/lib/knowledge-data";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface VectorSearchProps {
  documents: KBDocument[];
  onOpen: (doc: KBDocument) => void;
}

export default function VectorSearch({ documents, onOpen }: VectorSearchProps) {
  const [query, setQuery] = React.useState("");
  const [results, setResults] = React.useState<KBDocument[]>([]);

  const handleSearch = () => {
    // naive semantic search simulation
    const q = query.toLowerCase();
    const found = documents.filter((d) => d.title.toLowerCase().includes(q) || d.content.toLowerCase().includes(q));
    setResults(found);
  };

  return (
    <Card className="rounded-3xl border border-white/10 p-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Vector Search</CardTitle>
        <p className="text-sm text-muted">Search semantically across uploaded documents</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex gap-3">
            <Input placeholder="Semantic search..." value={query} onChange={(e) => setQuery(e.target.value)} />
            <button onClick={handleSearch} className="rounded-xl px-4 py-2 bg-primary text-slate-900">Search</button>
          </div>
          <div className="grid gap-2">
            {results.map((r) => (
              <button key={r.id} onClick={() => onOpen(r)} className="text-left rounded-2xl p-3 border border-white/5 bg-slate-950/50 hover:border-primary/40">
                <p className="font-semibold text-foreground">{r.title}</p>
                <p className="text-xs text-muted line-clamp-2">{r.content}</p>
              </button>
            ))}
            {results.length === 0 && <p className="text-sm text-muted">No semantic matches yet.</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
