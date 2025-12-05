import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AuditLogEntry, Candidate, JobDescription } from "@/types";
import { ArrowRight, Database, FileText, Filter, MessageSquare, Shield, TrendingUp } from "lucide-react";

interface PipelineSectionProps {
  candidates: Candidate[];
  jobDescriptions: JobDescription[];
  auditLog: AuditLogEntry[];
  deiMode: boolean;
}

export const PipelineSection = ({ candidates, jobDescriptions, auditLog, deiMode }: PipelineSectionProps) => {
  // Mock data for visualization
  const pipelineStages = [
    { name: "CV Ingest", icon: FileText, input: "CV, Portfolio", output: "Profilo Strutturato" },
    { name: "JD Creation", icon: Database, input: "Job Description", output: "Requisiti Strutturati" },
    { name: "Screening", icon: Filter, input: "Profili + JD", output: "Punteggi Match" },
    { name: "Feedback", icon: MessageSquare, input: "Decision", output: "Feedback Template" },
    { name: "Audit", icon: Shield, input: "Azioni", output: "Compliance Log" },
  ];

  // Calculate DEI stats
  const totalCandidates = candidates.length;
  const candidatesWithOptIn = candidates.filter((c) => c.optInTags.length > 0).length;
  const optInPercentage = totalCandidates > 0 ? (candidatesWithOptIn / totalCandidates) * 100 : 0;

  // 80% rule reference (mock)
  const expectedMinimumPercentage = 80;

  const mockData = {
    candidates: candidates.slice(0, 3).map((c) => ({
      id: c.id,
      name: c.name,
      skills: c.skills.slice(0, 3).map((s) => s.name),
      optIn: c.optInTags.length > 0,
    })),
    jobDescriptions: jobDescriptions.slice(0, 2).map((jd) => ({
      id: jd.id,
      title: jd.title,
      requirements: jd.requirements.slice(0, 3).map((r) => r.text),
    })),
    opportunities: [
      { id: "o1", type: "Grant", title: "Women in Tech Scholarship" },
      { id: "o2", type: "Hackathon", title: "Sostenibilità 2025" },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Pipeline Visualization */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-6">Pipeline del Processo</h3>

        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {pipelineStages.map((stage, index) => (
            <div key={stage.name} className="flex items-center gap-4 w-full md:w-auto">
              <div className="flex flex-col items-center gap-2 flex-1">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                  <stage.icon className="h-8 w-8 text-primary" />
                </div>
                <div className="text-center">
                  <p className="font-semibold text-sm">{stage.name}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    <span className="font-medium">In:</span> {stage.input}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    <span className="font-medium">Out:</span> {stage.output}
                  </p>
                </div>
              </div>
              {index < pipelineStages.length - 1 && (
                <ArrowRight className="h-6 w-6 text-muted-foreground hidden md:block" />
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Current Data JSON (Read-only) */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
          <Database className="h-5 w-5 text-primary" />
          Dati Correnti (JSON)
        </h3>

        <div className="rounded-lg bg-muted p-4 overflow-x-auto">
          <pre className="text-xs">
            {JSON.stringify(mockData, null, 2)}
          </pre>
        </div>
      </Card>

      {/* Bias Monitor */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
          <TrendingUp className="h-5 w-5 text-primary" />
          Bias Monitor
        </h3>

        {deiMode ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-lg border p-4 text-center">
                <p className="text-3xl font-bold text-primary">{totalCandidates}</p>
                <p className="text-sm text-muted-foreground mt-1">Candidati Totali</p>
              </div>
              <div className="rounded-lg border p-4 text-center">
                <p className="text-3xl font-bold text-success">{candidatesWithOptIn}</p>
                <p className="text-sm text-muted-foreground mt-1">Con Tag Opt-in</p>
              </div>
              <div className="rounded-lg border p-4 text-center">
                <p className="text-3xl font-bold text-accent">{optInPercentage.toFixed(0)}%</p>
                <p className="text-sm text-muted-foreground mt-1">Percentuale Opt-in</p>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Rappresentazione Opt-in nei Top 5</span>
                <Badge variant={optInPercentage >= 20 ? "default" : "destructive"} className={optInPercentage >= 20 ? "bg-success" : ""}>
                  {optInPercentage >= 20 ? "Conforme" : "Attenzione"}
                </Badge>
              </div>

              <div className="relative h-8 rounded-full bg-muted overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 bg-success transition-all"
                  style={{ width: `${Math.min(optInPercentage, 100)}%` }}
                />
                <div className="absolute inset-0 flex items-center justify-center text-xs font-medium">
                  {optInPercentage.toFixed(0)}%
                </div>
              </div>

              <p className="text-xs text-muted-foreground">
                Riferimento: almeno 1 candidato con tag opt-in nei top 5 (20% minimo). 
                La "regola dell'80%" suggerisce che la rappresentanza nel pool finale dovrebbe riflettere 
                almeno l'80% della rappresentanza nel pool iniziale.
              </p>
            </div>

            <div className="rounded-lg border border-warning/50 bg-warning/5 p-4">
              <p className="text-sm font-medium mb-2">⚠️ Nota Importante</p>
              <p className="text-xs text-muted-foreground">
                Questo monitor è solo un report statistico. I tag opt-in NON influenzano gli score di matching.
                Il guardrail DEI interviene solo al momento della chiusura della shortlist, richiedendo che
                almeno 1 candidato con tag opt-in sia presente nei top 5.
              </p>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <Shield className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Attiva il DEI Mode per visualizzare le metriche di inclusività</p>
          </div>
        )}
      </Card>

      {/* Audit Log Summary */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Riepilogo Audit Log</h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {auditLog.map((entry) => (
            <div
              key={entry.id}
              className={`p-3 rounded-lg text-sm ${
                entry.deiCompliant === false ? "bg-destructive/10 border border-destructive/20" : "bg-muted"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <Badge variant={entry.deiCompliant === false ? "destructive" : "outline"}>
                    {entry.action.replace(/_/g, " ")}
                  </Badge>
                  <span className="font-medium">{entry.user}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {new Date(entry.timestamp).toLocaleString("it-IT", {
                    day: "2-digit",
                    month: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
              <p className="text-muted-foreground">{entry.details}</p>
              {entry.overrideReason && (
                <p className="text-xs text-destructive mt-1 italic">Motivazione: {entry.overrideReason}</p>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
