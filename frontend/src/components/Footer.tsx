import { Award } from "lucide-react";

const Footer = () => {
  return (
    <footer className="bg-primary text-white py-12">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Award className="w-8 h-8 text-accent" />
              <span className="text-2xl font-bold">PiazzaTi</span>
            </div>
            <p className="text-white/80 max-w-md">
              La piattaforma di recruiting che elimina i pregiudizi e valorizza le competenze. 
              Per un mondo del lavoro più equo e meritocratico.
            </p>
          </div>

          {/* Links - Aziende */}
          <div>
            <h4 className="font-semibold mb-4">Per le Aziende</h4>
            <ul className="space-y-2 text-white/80">
              <li><a href="#" className="hover:text-accent transition-colors">Come funziona</a></li>
              <li><a href="#" className="hover:text-accent transition-colors">Prezzi</a></li>
              <li><a href="#" className="hover:text-accent transition-colors">Case Studies</a></li>
              <li><a href="#" className="hover:text-accent transition-colors">FAQ</a></li>
            </ul>
          </div>

          {/* Links - Candidati */}
          <div>
            <h4 className="font-semibold mb-4">Per i Candidati</h4>
            <ul className="space-y-2 text-white/80">
              <li><a href="#" className="hover:text-accent transition-colors">Crea Profilo</a></li>
              <li><a href="#" className="hover:text-accent transition-colors">Offerte di Lavoro</a></li>
              <li><a href="#" className="hover:text-accent transition-colors">Risorse</a></li>
              <li><a href="#" className="hover:text-accent transition-colors">Blog</a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/20 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-white/60 text-sm">
            © 2025 PiazzaTi. Tutti i diritti riservati.
          </p>
          <div className="flex gap-6 text-sm text-white/60">
            <a href="#" className="hover:text-accent transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-accent transition-colors">Termini di Servizio</a>
            <a href="#" className="hover:text-accent transition-colors">Cookie Policy</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
