import { Shield, Eye, Brain, CheckCircle2 } from "lucide-react";
import { Card } from "@/components/ui/card";

const features = [
  {
    icon: Eye,
    title: "Profili Anonimi",
    description: "Nessuna informazione su età, genere o etnia. Solo competenze, esperienze e risultati concreti.",
  },
  {
    icon: Brain,
    title: "Skills al Centro",
    description: "Valutazione basata su competenze tecniche, soft skills e progetti realizzati. Meritocrazia pura.",
  },
  {
    icon: Shield,
    title: "Conformità Legale",
    description: "Piena conformità con normative anti-discriminazione e protezione dati personali (GDPR).",
  },
  {
    icon: CheckCircle2,
    title: "Matching Intelligente",
    description: "Algoritmi avanzati che collegano aziende e talenti basandosi esclusivamente sulle competenze.",
  },
];

const Features = () => {
  return (
    <section className="py-20 bg-secondary/50">
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Recruiting equo e <span className="text-accent">trasparente</span>
          </h2>
          <p className="text-lg text-muted-foreground">
            Una piattaforma che elimina i bias inconsci e promuove la diversità basandosi solo sul merito
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
          {features.map((feature, index) => (
            <Card 
              key={index} 
              className="p-6 hover:shadow-xl transition-all duration-300 border-border/50 hover:border-accent/50 group"
              style={{ background: 'var(--gradient-card)' }}
            >
              <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <feature.icon className="w-6 h-6 text-accent" />
              </div>
              <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
              <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
