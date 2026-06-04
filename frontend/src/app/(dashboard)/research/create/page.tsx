"use client";

import { useRouter } from "next/navigation";
import ResearchForm, { ResearchFormPayload } from "@/components/research/ResearchForm";

export default function ResearchCreatePage() {
  const router = useRouter();

  const handleCreate = (payload: ResearchFormPayload) => {
    console.log("New research task", payload);
    router.push("/research");
  };

  return (
    <div className="space-y-8 pb-16">
      <div className="space-y-2">
        <p className="text-sm uppercase tracking-[0.3em] text-primary">Create research task</p>
        <h1 className="text-4xl font-semibold text-foreground">Launch a new AI research job</h1>
        <p className="max-w-2xl text-sm leading-7 text-muted">
          Brief your research agent with a clear query and priority so the team can act on the best insights immediately.
        </p>
      </div>

      <ResearchForm onSubmit={handleCreate} />
    </div>
  );
}
