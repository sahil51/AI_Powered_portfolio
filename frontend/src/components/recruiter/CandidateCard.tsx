import { Candidate } from "@/lib/recruiter-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface CandidateCardProps {
  candidate: Candidate;
  onSelect?: () => void;
}

export default function CandidateCard({ candidate, onSelect }: CandidateCardProps) {
  return (
    <Card className="rounded-3xl border border-white/10 p-4 cursor-pointer" onClick={onSelect}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{candidate.name}</CardTitle>
            <p className="text-sm text-muted">{candidate.title} • {candidate.experienceYears} yrs</p>
          </div>
          <Badge className="bg-slate-800 text-muted border border-white/10">Resume</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground/80">{candidate.summary}</p>
        <div className="mt-4 grid gap-2">
          <div className="flex flex-wrap gap-2">
            {Object.keys(candidate.skills).slice(0,6).map((s) => (
              <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-slate-900/80 border border-border text-muted">{s}</span>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
