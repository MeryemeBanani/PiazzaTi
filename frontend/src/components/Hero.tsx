import { Button } from "@/components/ui/button";
import { ArrowRight, Users, Award, TrendingUp } from "lucide-react";
import heroImage from "@/assets/hero-recruiting.jpg";

const Hero = () => {
  return (
    <section className="relative min-h-[90vh] flex items-center overflow-hidden">
      {/* Background with gradient overlay */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary/95 to-primary-glow opacity-95" />
        <img 
          src={heroImage} 
          alt="Skills-based recruitment" 
          className="w-full h-full object-cover mix-blend-overlay opacity-30"
        />
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-20 relative z-10">
        <div className="max-w-4xl mx-auto text-center text-white">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-8 animate-fade-in">
            <Award className="w-4 h-4 text-accent" />
            <span className="text-sm font-medium">Recruiting senza pregiudizi</span>
          </div>

          {/* Brand Name */}
          <div className="text-accent text-3xl md:text-4xl font-bold mb-4 animate-fade-in">
            PiazzaTi
          </div>

          {/* Main heading */}
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
            Le competenze contano,
            <span className="block text-accent mt-2">non i pregiudizi</span>
          </h1>

          {/* Subheading */}
          <p className="text-xl md:text-2xl mb-12 text-white/90 max-w-3xl mx-auto leading-relaxed">
            Piattaforma di recruiting innovativa che nasconde genere, età e razza.
            Solo skills, esperienze e competenze. Selezioni giuste, team migliori.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
            <Button size="lg" variant="accent" className="group">
              Per le Aziende
              <ArrowRight className="ml-2 group-hover:translate-x-1 transition-transform" />
            </Button>
            <Button size="lg" variant="outline" className="bg-white/10 border-white/30 text-white hover:bg-white/20 backdrop-blur-sm">
              Per i Candidati
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-3xl mx-auto">
            <div className="backdrop-blur-sm bg-white/10 rounded-lg p-6 border border-white/20">
              <Users className="w-8 h-8 text-accent mx-auto mb-3" />
              <div className="text-3xl font-bold mb-1">100%</div>
              <div className="text-sm text-white/80">Anonimato garantito</div>
            </div>
            <div className="backdrop-blur-sm bg-white/10 rounded-lg p-6 border border-white/20">
              <Award className="w-8 h-8 text-accent mx-auto mb-3" />
              <div className="text-3xl font-bold mb-1">0</div>
              <div className="text-sm text-white/80">Bias nelle selezioni</div>
            </div>
            <div className="backdrop-blur-sm bg-white/10 rounded-lg p-6 border border-white/20">
              <TrendingUp className="w-8 h-8 text-accent mx-auto mb-3" />
              <div className="text-3xl font-bold mb-1">+40%</div>
              <div className="text-sm text-white/80">Diversità nei team</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
