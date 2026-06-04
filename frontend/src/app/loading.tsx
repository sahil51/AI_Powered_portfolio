"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";

export default function LoadingPage() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <Card className="rounded-3xl p-8 glass-panel text-center">
        <div className="animate-[var(--animate-float)] mb-4">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" className="mx-auto">
            <circle cx="12" cy="12" r="10" stroke="#8B5CF6" strokeWidth="2" strokeOpacity="0.3" />
            <path d="M4 12a8 8 0 018-8" stroke="#22D3EE" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold">Loading…</h3>
        <p className="text-sm text-muted mt-2">Preparing your premium AI workspace.</p>
      </Card>
    </div>
  );
}
