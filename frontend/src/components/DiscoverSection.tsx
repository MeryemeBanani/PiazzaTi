import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Candidate, Opportunity, JobDescription } from "@/types";
import { Users, Lightbulb, Briefcase, Plus, ExternalLink, TrendingUp, Calendar } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface DiscoverSectionProps {
  suggestedProfiles: Candidate[];
  opportunities: Opportunity[];
  jobDescriptions: JobDescription[];
  onConnect: (candidateId: string) => void;
  onAddOpportunity: () => void;
  onEvaluateMatch: (jdId: string) => void;
}

export const DiscoverSection = ({
  suggestedProfiles,
  opportunities,
  jobDescriptions,
  onConnect,
  onAddOpportunity,
  onEvaluateMatch,
}: DiscoverSectionProps) => {
  const getOpportunityIcon = (type: string) => {
    switch (type) {
      case "grant":
        return "💰";
      case "hackathon":
        return "🏆";
      case "course":
        return "📚";
      case "fellowship":
        return "🎓";
      default:
        return "✨";
    }
  };

  return (
    <div className="space-y-6">
      {/* Profili Consigliati */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" />
            Profili Consigliati
          </h3>
          <Badge variant="outline">{suggestedProfiles.length} profili</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {suggestedProfiles.map((profile) => (
            <Card key={profile.id} className="p-4 hover:shadow-lg transition-shadow">
              <div className="flex items-start gap-3 mb-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground flex-shrink-0">
                  {profile.name.split(" ").map((n) => n[0]).join("")}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold truncate">{profile.name}</p>
                  <p className="text-xs text-muted-foreground truncate">{profile.location}</p>
                </div>
              </div>

              <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{profile.summary}</p>

              <div className="flex flex-wrap gap-1 mb-3">
                {profile.skills.slice(0, 4).map((skill, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {skill.name}
                  </Badge>
                ))}
                {profile.skills.length > 4 && (
                  <Badge variant="outline" className="text-xs">
                    +{profile.skills.length - 4}
                  </Badge>
                )}
              </div>

              {profile.optInTags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {profile.optInTags.map((tag, i) => (
                    <Badge key={i} variant="outline" className="text-xs border-success text-success">
                      {tag.label}
                    </Badge>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={() => {
                    onConnect(profile.id);
                    toast({ title: "Richiesta inviata", description: `Richiesta di connessione a ${profile.name}` });
                  }}
                >
                  Connetti
                </Button>
                <Button variant="ghost" size="sm" onClick={() => toast({ title: "Funzione demo" })}>
                  <TrendingUp className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </Card>

      {/* Opportunità */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-primary" />
            Opportunità
          </h3>
          <Button variant="outline" size="sm" onClick={onAddOpportunity}>
            <Plus className="h-4 w-4 mr-1" />
            Aggiungi
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {opportunities.map((opp) => (
            <Card key={opp.id} className="p-4 hover:shadow-lg transition-shadow">
              <div className="flex items-start gap-3 mb-3">
                <span className="text-2xl">{getOpportunityIcon(opp.type)}</span>
                <div className="flex-1 min-w-0">
                  <Badge variant="outline" className="mb-2 text-xs">
                    {opp.type}
                  </Badge>
                  <h4 className="font-semibold">{opp.title}</h4>
                  <p className="text-xs text-muted-foreground">{opp.organization}</p>
                </div>
              </div>

              <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{opp.description}</p>

              {opp.deadline && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                  <Calendar className="h-3 w-3" />
                  <span>Scadenza: {opp.deadline}</span>
                </div>
              )}

              <Button variant="outline" size="sm" className="w-full" onClick={() => toast({ title: "Funzione demo" })}>
                {opp.link ? (
                  <>
                    <ExternalLink className="h-3 w-3 mr-1" />
                    Visita
                  </>
                ) : (
                  "Info"
                )}
              </Button>
            </Card>
          ))}
        </div>
      </Card>

      {/* Proposte di Lavoro */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Briefcase className="h-5 w-5 text-primary" />
            Proposte di Lavoro
          </h3>
          <Badge variant="outline">{jobDescriptions.length} posizioni</Badge>
        </div>

        <div className="space-y-3">
          {jobDescriptions.map((jd) => (
            <Card key={jd.id} className="p-4 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <h4 className="font-semibold">{jd.title}</h4>
                  <p className="text-sm text-muted-foreground">{jd.company}</p>
                  <p className="text-sm mt-2 line-clamp-2">{jd.description}</p>

                  <div className="flex flex-wrap gap-2 mt-3">
                    <Badge variant="outline" className="text-xs">
                      📍 {jd.location}
                    </Badge>
                    {jd.salary && (
                      <Badge variant="outline" className="text-xs">
                        💰 {jd.salary}
                      </Badge>
                    )}
                    {jd.requirements.slice(0, 3).map((req, i) => (
                      <Badge key={i} variant={req.type === "must" ? "default" : "secondary"} className="text-xs">
                        {req.text}
                      </Badge>
                    ))}
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    onEvaluateMatch(jd.id);
                    toast({ title: "Valutazione match", description: `Analisi compatibilità per "${jd.title}"` });
                  }}
                >
                  Valuta Match
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </Card>
    </div>
  );
};
