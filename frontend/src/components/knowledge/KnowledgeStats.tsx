import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface KnowledgeStatsProps {
  documents: number;
  embeddings: number;
  notes: number;
  reports: number;
}

export default function KnowledgeStats({ documents, embeddings, notes, reports }: KnowledgeStatsProps) {
  const items = [
    { label: "Documents", value: documents },
    { label: "Embeddings", value: embeddings },
    { label: "Research Notes", value: notes },
    { label: "Reports", value: reports },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((it) => (
        <Card key={it.label} className="rounded-3xl border border-white/10 p-4">
          <CardHeader className="pb-2">
            <p className="text-sm uppercase tracking-[0.3em] text-muted">{it.label}</p>
            <CardTitle className="mt-3 text-2xl text-foreground">{it.value}</CardTitle>
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}
