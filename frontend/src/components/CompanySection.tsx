import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { JobDescription, ShortlistCandidate, AuditLogEntry, InclusivityIssue } from "@/types";
import { AlertTriangle, CheckCircle, Users, FileText, ShieldAlert, Plus, X } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface CompanySectionProps {
  jobDescriptions: JobDescription[];
  onCreateJd: (jd: Omit<JobDescription, "id" | "createdAt">) => void;
  shortlist: ShortlistCandidate[];
  deiMode: boolean;
  auditLog: AuditLogEntry[];
  onCloseShortlist: (jdId: string, override?: { reason: string }) => void;
}

export const CompanySection = ({
  jobDescriptions,
  onCreateJd,
  shortlist,
  deiMode,
  auditLog,
  onCloseShortlist,
}: CompanySectionProps) => {
  const [jdForm, setJdForm] = useState({
    title: "",
    company: "",
    description: "",
    salary: "",
    location: "",
  });
  const [requirements, setRequirements] = useState<{ text: string; type: "must" | "nice" }[]>([]);
  const [newReq, setNewReq] = useState("");
  const [reqType, setReqType] = useState<"must" | "nice">("must");

  const [overrideDialogOpen, setOverrideDialogOpen] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");

  // Inclusivity checker
  const nonInclusiveTerms = [
    { term: "rockstar", severity: "high" as const, suggestion: "esperto/a" },
    { term: "ninja", severity: "high" as const, suggestion: "specialista" },
    { term: "guru", severity: "medium" as const, suggestion: "esperto/a" },
    { term: "aggressivo", severity: "high" as const, suggestion: "proattivo/a" },
    { term: "giovane", severity: "high" as const, suggestion: "dinamico/a" },
    { term: "nativo digitale", severity: "medium" as const, suggestion: "competenze digitali" },
  ];

  const checkInclusivity = (): InclusivityIssue[] => {
    const text = `${jdForm.title} ${jdForm.description} ${requirements.map((r) => r.text).join(" ")}`.toLowerCase();
    return nonInclusiveTerms
      .filter((term) => text.includes(term.term.toLowerCase()))
      .map((term) => ({ ...term, position: 0 }));
  };

  const issues = checkInclusivity();
  const tooManyRequirements = requirements.filter((r) => r.type === "must").length > 5;

  // DEI Guardrail check
  const checkDeiCompliance = (): boolean => {
    if (!deiMode) return true;

    const top5 = shortlist.slice(0, 5);
    const hasOptInTag = top5.some((candidate) => candidate.optInTags.length > 0);

    return hasOptInTag;
  };

  const isDeiCompliant = checkDeiCompliance();

  const handleAddRequirement = () => {
    if (newReq.trim()) {
      setRequirements([...requirements, { text: newReq.trim(), type: reqType }]);
      setNewReq("");
    }
  };

  const handleRemoveRequirement = (index: number) => {
    setRequirements(requirements.filter((_, i) => i !== index));
  };

  const handleCreateJd = () => {
    if (!jdForm.title || !jdForm.company || requirements.length === 0) {
      toast({
        title: "Campi obbligatori mancanti",
        description: "Compila almeno titolo, azienda e un requisito",
        variant: "destructive",
      });
      return;
    }

    onCreateJd({
      ...jdForm,
      requirements,
    });

    // Reset form
    setJdForm({ title: "", company: "", description: "", salary: "", location: "" });
    setRequirements([]);

    toast({
      title: "Job Description creata",
      description: `"${jdForm.title}" aggiunta con successo`,
    });
  };

  const handleCloseShortlist = () => {
    if (!isDeiCompliant && deiMode) {
      setOverrideDialogOpen(true);
    } else {
      onCloseShortlist("current-jd");
      toast({ title: "Shortlist chiusa", description: "Processo completato con successo" });
    }
  };

  const handleOverride = () => {
    if (!overrideReason.trim()) {
      toast({
        title: "Motivazione richiesta",
        description: "Inserisci una motivazione per l'override",
        variant: "destructive",
      });
      return;
    }

    onCloseShortlist("current-jd", { reason: overrideReason });
    setOverrideDialogOpen(false);
    setOverrideReason("");

    toast({
      title: "Override registrato",
      description: "L'azione è stata registrata nell'audit log",
      variant: "destructive",
    });
  };

  return (
    <div className="space-y-6">
      {/* JD Creator */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
          <FileText className="h-5 w-5 text-primary" />
          Crea Job Description
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="title">Titolo Posizione *</Label>
            <Input
              id="title"
              value={jdForm.title}
              onChange={(e) => setJdForm({ ...jdForm, title: e.target.value })}
              placeholder="es. Senior Frontend Developer"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="company">Azienda *</Label>
            <Input
              id="company"
              value={jdForm.company}
              onChange={(e) => setJdForm({ ...jdForm, company: e.target.value })}
              placeholder="es. TechCorp Italia"
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="description">Descrizione</Label>
            <Textarea
              id="description"
              value={jdForm.description}
              onChange={(e) => setJdForm({ ...jdForm, description: e.target.value })}
              placeholder="Descrivi la posizione, il team e le responsabilità..."
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="salary">Salary Range</Label>
            <Input
              id="salary"
              value={jdForm.salary}
              onChange={(e) => setJdForm({ ...jdForm, salary: e.target.value })}
              placeholder="es. 45.000 - 65.000 €"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Input
              id="location"
              value={jdForm.location}
              onChange={(e) => setJdForm({ ...jdForm, location: e.target.value })}
              placeholder="es. Milano (Ibrido)"
            />
          </div>
        </div>

        {/* Requirements */}
        <div className="mt-6">
          <Label>Requisiti *</Label>
          <div className="flex gap-2 mt-2">
            <Input
              value={newReq}
              onChange={(e) => setNewReq(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddRequirement()}
              placeholder="es. React, 5+ anni esperienza..."
            />
            <Select value={reqType} onValueChange={(v) => setReqType(v as "must" | "nice")}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="must">Must</SelectItem>
                <SelectItem value="nice">Nice</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={handleAddRequirement}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>

          <div className="flex flex-wrap gap-2 mt-3">
            {requirements.map((req, i) => (
              <Badge
                key={i}
                variant={req.type === "must" ? "default" : "outline"}
                className="flex items-center gap-1"
              >
                {req.text}
                <button
                  onClick={() => handleRemoveRequirement(i)}
                  className="ml-1 hover:text-destructive transition-colors"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        </div>

        <Button onClick={handleCreateJd} className="mt-6 w-full">
          Crea Job Description
        </Button>
      </Card>

      {/* Inclusivity Checker */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
          <ShieldAlert className="h-5 w-5 text-warning" />
          Inclusivity Checker
        </h3>

        {issues.length === 0 && !tooManyRequirements ? (
          <div className="flex items-center gap-2 text-success">
            <CheckCircle className="h-5 w-5" />
            <span>Nessun problema rilevato</span>
          </div>
        ) : (
          <div className="space-y-3">
            {issues.map((issue, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg border border-warning/50 bg-warning/5">
                <AlertTriangle className="h-5 w-5 text-warning flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium">
                    Termine non inclusivo: <span className="text-warning">"{issue.term}"</span>
                  </p>
                  <p className="text-sm text-muted-foreground">Suggerimento: {issue.suggestion}</p>
                </div>
              </div>
            ))}

            {tooManyRequirements && (
              <div className="flex items-start gap-3 p-3 rounded-lg border border-warning/50 bg-warning/5">
                <AlertTriangle className="h-5 w-5 text-warning flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium">Troppi requisiti must-have</p>
                  <p className="text-sm text-muted-foreground">
                    Considera di spostare alcuni requisiti in "nice-to-have" per ampliare il pool di candidati
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Shortlist */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
          <Users className="h-5 w-5 text-primary" />
          Shortlist Candidati
        </h3>

        {deiMode && (
          <div
            className={`mb-4 p-4 rounded-lg border ${
              isDeiCompliant
                ? "border-success/50 bg-success/5"
                : "border-destructive/50 bg-destructive/5"
            }`}
          >
            <div className="flex items-center gap-2">
              {isDeiCompliant ? (
                <>
                  <CheckCircle className="h-5 w-5 text-success" />
                  <span className="font-medium text-success">Guardrail DEI: Compliant</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="h-5 w-5 text-destructive" />
                  <span className="font-medium text-destructive">
                    Guardrail DEI: Non compliant - Richiesto almeno 1 candidato con tag opt-in nei top 5
                  </span>
                </>
              )}
            </div>
          </div>
        )}

        <div className="space-y-3">
          {shortlist.slice(0, 5).map((candidate, index) => (
            <div key={candidate.id} className="p-4 rounded-lg border">
              <div className="flex items-center gap-3 mb-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-muted font-bold">
                  {index + 1}
                </span>
                <div className="flex-1">
                  <p className="font-semibold">{candidate.name}</p>
                  <p className="text-sm text-muted-foreground">{candidate.location}</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {candidate.skills.slice(0, 3).map((skill, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {skill.name}
                      </Badge>
                    ))}
                    {deiMode && candidate.optInTags.map((tag, i) => (
                      <Badge key={`tag-${i}`} variant="outline" className="text-xs border-success text-success">
                        {tag.label}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-primary">{candidate.match.score}%</p>
                  <p className="text-xs text-muted-foreground">match</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => toast({ title: "Azione demo", description: "Candidato avanzato alla fase successiva" })}
                >
                  Avanza
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => toast({ title: "Azione demo", description: "Richiesta info inviata" })}
                >
                  Richiedi info
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => toast({ title: "Azione demo", description: "Candidato archiviato" })}
                >
                  Archivia
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => toast({ title: "Azione demo", description: "Form feedback aperto (non implementato)" })}
                >
                  Feedback
                </Button>
              </div>
            </div>
          ))}
        </div>

        <Button
          onClick={handleCloseShortlist}
          className="mt-4 w-full"
          variant={isDeiCompliant || !deiMode ? "default" : "destructive"}
        >
          {isDeiCompliant || !deiMode ? "Chiudi Shortlist" : "Richiede Override"}
        </Button>
      </Card>

      {/* Template Feedback */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Template Feedback</h3>
        <div className="space-y-3">
          <div className="p-3 rounded-lg border bg-muted/50">
            <p className="font-medium mb-1">✅ Positivo</p>
            <p className="text-sm text-muted-foreground">
              "Il tuo profilo è molto interessante! Ci piacerebbe conoscerti per una video call conoscitiva."
            </p>
          </div>
          <div className="p-3 rounded-lg border bg-muted/50">
            <p className="font-medium mb-1">📝 Costruttivo</p>
            <p className="text-sm text-muted-foreground">
              "Grazie per la candidatura. Al momento stiamo valutando profili con più esperienza in [skill]."
            </p>
          </div>
          <div className="p-3 rounded-lg border bg-muted/50">
            <p className="font-medium mb-1">🔔 Neutro</p>
            <p className="text-sm text-muted-foreground">
              "Abbiamo ricevuto la tua application. Ti contatteremo entro 2 settimane."
            </p>
          </div>
        </div>
        <Button variant="outline" className="w-full mt-4" onClick={() => toast({ title: "Feedback inviato (demo)" })}>
          Invia Feedback
        </Button>
      </Card>

      {/* Audit Log */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Audit Log</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {auditLog.slice(0, 10).map((entry) => (
            <div
              key={entry.id}
              className={`p-3 rounded-lg text-sm ${
                entry.deiCompliant === false ? "bg-destructive/10 border border-destructive/20" : "bg-muted"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium">{entry.action.replace(/_/g, " ").toUpperCase()}</span>
                <span className="text-xs text-muted-foreground">
                  {new Date(entry.timestamp).toLocaleString("it-IT")}
                </span>
              </div>
              <p className="text-muted-foreground">{entry.details}</p>
              {entry.overrideReason && (
                <p className="text-xs text-destructive mt-1">Override: {entry.overrideReason}</p>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Override Dialog */}
      <Dialog open={overrideDialogOpen} onOpenChange={setOverrideDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Override DEI Guardrail</DialogTitle>
            <DialogDescription>
              Il guardrail di inclusività non è soddisfatto. Per procedere, fornisci una motivazione che verrà
              registrata nell'audit log.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="override-reason">Motivazione Override *</Label>
              <Textarea
                id="override-reason"
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="es. Urgenza aziendale: posizione critica da coprire entro fine mese. Team commitment a rivedere pipeline di sourcing."
                rows={4}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setOverrideDialogOpen(false)}>
              Annulla
            </Button>
            <Button variant="destructive" onClick={handleOverride}>
              Conferma Override
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
