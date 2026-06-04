"use client";

import React from "react";

export default function ErrorPage({ error }: { error: Error }) {
  console.error(error);
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-5xl font-black text-gradient">Something went wrong</h1>
        <p className="text-sm text-muted">An unexpected error occurred. Try refreshing the page.</p>
        <button onClick={() => window.location.reload()} className="mt-4 rounded-3xl border border-white/10 bg-slate-900/70 px-6 py-3 font-semibold">Reload</button>
      </div>
    </div>
  );
}
