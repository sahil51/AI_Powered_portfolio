"use client";

import { KBDocument } from "@/lib/knowledge-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface DocumentViewerProps {
  doc?: KBDocument | null;
  onDelete?: (id: string) => void;
}

export default function DocumentViewer({ doc, onDelete }: DocumentViewerProps) {
  if (!doc) {
    return (
      <Card className="rounded-3xl border border-white/10 p-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Document preview</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted">Select a document to preview its content and actions.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="rounded-3xl border border-white/10 p-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">{doc.title}</CardTitle>
        <p className="text-sm text-muted">{doc.category} • {doc.uploadedAt}</p>
      </CardHeader>
      <CardContent>
        <div className="max-h-64 overflow-auto rounded-md bg-slate-900/50 p-4 text-sm text-foreground/80">
          <p>{doc.content}</p>
        </div>
        <div className="mt-4 flex gap-3 justify-end">
          <Button variant="ghost">Download</Button>
          <Button variant="outline" onClick={() => doc && onDelete?.(doc.id)}>Delete</Button>
        </div>
      </CardContent>
    </Card>
  );
}
