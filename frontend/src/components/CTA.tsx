import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowRight, Building2, UserPlus } from "lucide-react";

const CTA = () => {
  return (
    <section className="py-20 bg-gradient-to-b from-background to-secondary/30">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Inizia oggi a costruire un <span className="text-accent">team migliore</span>
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Unisciti alle aziende che hanno scelto l'equità e le competenze come pilastri del loro recruiting
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Card for Companies */}
            <Card 
              className="p-8 hover:shadow-2xl transition-all duration-300 group border-2 hover:border-primary/50"
              style={{ boxShadow: 'var(--shadow-elegant)' }}
            >
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Building2 className="w-8 h-8 text-primary" />
              </div>
              <h3 className="text-2xl font-bold mb-4">Sei un'Azienda?</h3>
              <p className="text-muted-foreground mb-6 leading-relaxed">
                Accedi a un pool di talenti qualificati selezionati solo per competenze. 
                Costruisci team diversificati e performanti.
              </p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-1">✓</span>
                  <span>Matching basato su skills reali</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-1">✓</span>
                  <span>Riduzione del 70% dei bias nelle selezioni</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-1">✓</span>
                  <span>Dashboard completa per gestire le candidature</span>
                </li>
              </ul>
              <Button className="w-full group" size="lg">
                Registra la tua Azienda
                <ArrowRight className="ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Card>

            {/* Card for Candidates */}
            <Card 
              className="p-8 hover:shadow-2xl transition-all duration-300 group border-2 hover:border-accent/50"
              style={{ boxShadow: 'var(--shadow-elegant)' }}
            >
              <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <UserPlus className="w-8 h-8 text-accent" />
              </div>
              <h3 className="text-2xl font-bold mb-4">Sei un Candidato?</h3>
              <p className="text-muted-foreground mb-6 leading-relaxed">
                Fatti valutare per quello che sai fare, non per come appari. 
                Trova opportunità che valorizzano le tue competenze.
              </p>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-1">✓</span>
                  <span>Profilo anonimo al 100%</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-1">✓</span>
                  <span>Valutazioni basate solo su merito</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-1">✓</span>
                  <span>Opportunità da aziende inclusive</span>
                </li>
              </ul>
              <Button variant="accent" className="w-full group" size="lg">
                Crea il tuo Profilo
                <ArrowRight className="ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTA;
