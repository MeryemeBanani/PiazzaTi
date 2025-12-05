import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Code, Palette, LineChart, Users } from "lucide-react";

const HowItWorks = () => {
  return (
    <section className="py-20">
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Come funziona il <span className="text-primary">profilo anonimo</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Mostriamo solo ciò che conta davvero: competenze, esperienze e risultati
          </p>
        </div>

        <div className="max-w-5xl mx-auto">
          <Card className="p-8 md:p-12 shadow-2xl" style={{ boxShadow: 'var(--shadow-elegant)' }}>
            {/* Profile Header - Anonymous */}
            <div className="border-b border-border pb-6 mb-8">
              <div className="flex items-start gap-6">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center text-white text-2xl font-bold">
                  C-2401
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold mb-2">Candidato #2401</h3>
                  <p className="text-muted-foreground mb-4">5+ anni esperienza | Disponibile da Marzo 2025</p>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary" className="bg-accent/10 text-accent border-accent/20">Senior Level</Badge>
                    <Badge variant="secondary">Full-time</Badge>
                    <Badge variant="secondary">Remote</Badge>
                  </div>
                </div>
              </div>
            </div>

            {/* Skills Section */}
            <div className="mb-8">
              <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Code className="w-5 h-5 text-primary" />
                Competenze Tecniche
              </h4>
              <div className="flex flex-wrap gap-2">
                {["React", "TypeScript", "Node.js", "PostgreSQL", "AWS", "Docker", "GraphQL", "CI/CD"].map((skill) => (
                  <Badge key={skill} variant="outline" className="px-3 py-1">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Soft Skills */}
            <div className="mb-8">
              <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Users className="w-5 h-5 text-primary" />
                Soft Skills
              </h4>
              <div className="flex flex-wrap gap-2">
                {["Leadership", "Problem Solving", "Team Collaboration", "Comunicazione"].map((skill) => (
                  <Badge key={skill} variant="outline" className="px-3 py-1 bg-accent/5">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Experience */}
            <div className="mb-8">
              <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <LineChart className="w-5 h-5 text-primary" />
                Esperienze Rilevanti
              </h4>
              <div className="space-y-4">
                <div className="border-l-2 border-accent pl-4">
                  <div className="font-medium">Senior Full Stack Developer</div>
                  <div className="text-sm text-muted-foreground mb-2">Tech Company | 3 anni</div>
                  <p className="text-sm">Guidato team di 5 sviluppatori, implementato architettura microservizi, ridotto tempi di deployment del 60%</p>
                </div>
                <div className="border-l-2 border-primary/40 pl-4">
                  <div className="font-medium">Full Stack Developer</div>
                  <div className="text-sm text-muted-foreground mb-2">Startup | 2 anni</div>
                  <p className="text-sm">Sviluppato piattaforma e-commerce da zero, gestito 100k+ utenti mensili</p>
                </div>
              </div>
            </div>

            {/* Projects */}
            <div>
              <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Palette className="w-5 h-5 text-primary" />
                Progetti Significativi
              </h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-1">•</span>
                  <span>Contribuito a 15+ progetti open source con 500+ stars su GitHub</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-1">•</span>
                  <span>Sviluppato tool interno che ha aumentato produttività team del 40%</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-1">•</span>
                  <span>Speaker a 3 conferenze tech internazionali</span>
                </li>
              </ul>
            </div>
          </Card>

          <div className="mt-8 text-center">
            <p className="text-muted-foreground">
              <span className="font-semibold text-foreground">Nessuna informazione su:</span> età, genere, etnia, nazionalità, stato civile, foto personale
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
