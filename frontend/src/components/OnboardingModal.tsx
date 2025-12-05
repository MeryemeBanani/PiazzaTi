import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { CheckCircle } from "lucide-react";

interface OnboardingModalProps {
  open: boolean;
  onClose: () => void;
}

export const OnboardingModal = ({ open, onClose }: OnboardingModalProps) => {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl">Benvenuto in Recruiting Demo</DialogTitle>
          <DialogDescription className="text-base">
            Una piattaforma dimostrativa di recruiting inclusivo, trasparente e spiegabile
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-3">
            <h3 className="font-semibold flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-success" />
              Cosa troverai in questa demo
            </h3>
            <ul className="space-y-2 text-sm text-muted-foreground ml-7">
              <li>
                <strong>Sezione Candidato:</strong> Profilo completo con skill, progetti, wall personale e compatibilità con JD
              </li>
              <li>
                <strong>Sezione Azienda:</strong> Creazione JD, inclusivity checker, shortlist e guardrail DEI
              </li>
              <li>
                <strong>Sezione Pipeline:</strong> Visualizzazione processo, bias monitor e audit log
              </li>
              <li>
                <strong>Sezione Scopri:</strong> Network di profili consigliati e opportunità
              </li>
            </ul>
          </div>

          <div className="space-y-3">
            <h3 className="font-semibold flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-success" />
              Funzionalità chiave
            </h3>
            <ul className="space-y-2 text-sm text-muted-foreground ml-7">
              <li>
                <strong>Spiegabilità:</strong> Ogni match mostra percentuali di overlap tra requisiti must-have e nice-to-have
              </li>
              <li>
                <strong>DEI Mode (IT):</strong> Attiva i guardrail di inclusività per l'Italia (almeno 1 candidato con tag opt-in nei top 5)
              </li>
              <li>
                <strong>Audit Log:</strong> Traccia tutte le azioni critiche, inclusi gli override con motivazione
              </li>
              <li>
                <strong>Dati Mock:</strong> Tutti i dati sono simulati e salvati in stato locale
              </li>
            </ul>
          </div>

          <div className="rounded-lg bg-muted p-4 text-sm">
            <p className="font-medium mb-2">📌 Nota importante</p>
            <p className="text-muted-foreground">
              Questa è una demo front-end: non ci sono algoritmi reali di matching, solo interfacce e flussi
              pronti per essere collegati a un backend futuro. L'obiettivo è mostrare come potrebbe funzionare
              una piattaforma di recruiting trasparente e inclusiva.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button onClick={onClose} className="w-full sm:w-auto">
            Inizia la demo
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
