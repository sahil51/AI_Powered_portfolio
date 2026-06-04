"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function UploadCenter() {
  const [progress, setProgress] = React.useState(0);
  const [drag, setDrag] = React.useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    setProgress(10);
    // simulate upload
    setTimeout(() => setProgress(100), 800);
  };

  return (
    <Card className="rounded-3xl border border-white/10 p-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Upload Center</CardTitle>
        <p className="text-sm text-muted">Drag & drop PDFs, DOCX, or TXT to create embeddings</p>
      </CardHeader>
      <CardContent>
        <div
          onDragOver={(e) => e.preventDefault()}
          onDragEnter={() => setDrag(true)}
          onDragLeave={() => setDrag(false)}
          onDrop={handleDrop}
          className={`rounded-2xl border-dashed p-6 text-center ${drag ? "border-primary" : "border-white/10"}`}
        >
          <p className="text-sm text-muted">Drop files here</p>
          <p className="mt-2 text-xs text-muted">Supported: PDF, DOCX, TXT</p>
          <div className="mt-4">
            <Button variant="secondary">Select files</Button>
          </div>
          {progress > 0 && (
            <div className="mt-4">
              <div className="h-3 rounded-full bg-slate-900/70">
                <div className="h-full rounded-full bg-gradient-to-r from-primary to-accent" style={{ width: `${progress}%` }} />
              </div>
              <p className="text-xs text-muted mt-2">Processing: {progress}%</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
