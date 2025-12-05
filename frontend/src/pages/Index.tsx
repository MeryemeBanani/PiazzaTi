import { useState, useEffect, useMemo } from "react";
import { Header } from "@/components/Header";
import { OnboardingModal } from "@/components/OnboardingModal";
import { CandidateSection } from "@/components/CandidateSection";
import { CompanySection } from "@/components/CompanySection";
import { PipelineSection } from "@/components/PipelineSection";
import { DiscoverSection } from "@/components/DiscoverSection";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  mockCandidates,
  mockJobDescriptions,
  mockOpportunities,
  mockFeedback,
  mockAuditLog,
} from "@/data/mockData";
import {
  Candidate,
  JobDescription,
  Opportunity,
  Feedback,
  AuditLogEntry,
  ShortlistCandidate,
  Skill,
  Post,
  OptInTag,
} from "@/types";
import { toast } from "@/hooks/use-toast";
import { User, Building2, GitBranch, Compass } from "lucide-react";

const Index = () => {
  const [showOnboarding, setShowOnboarding] = useState(true);
  const [deiMode, setDeiMode] = useState(true);
  const [activeTab, setActiveTab] = useState("candidate");

  // Data state
  const [candidates, setCandidates] = useState<Candidate[]>(mockCandidates);
  const [jobDescriptions, setJobDescriptions] = useState<JobDescription[]>(mockJobDescriptions);
  const [opportunities, setOpportunities] = useState<Opportunity[]>(mockOpportunities);
  const [feedback, setFeedback] = useState<Feedback[]>(mockFeedback);
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>(mockAuditLog);

  const [selectedJdId, setSelectedJdId] = useState<string | null>(jobDescriptions[0]?.id || null);
  const [activeCandidateId, setActiveCandidateId] = useState<string>(mockCandidates[0].id);

  // Current candidate
  const currentCandidate = candidates.find(c => c.id === activeCandidateId) || candidates[0];

  // Calculate shortlist based on current JD
  const shortlist: ShortlistCandidate[] = useMemo(() => {
    if (!selectedJdId) return [];

    const jd = jobDescriptions.find((j) => j.id === selectedJdId);
    if (!jd) return [];

    return candidates
      .map((candidate) => {
        const mustRequirements = jd.requirements.filter((r) => r.type === "must");
        const niceRequirements = jd.requirements.filter((r) => r.type === "nice");

        const candidateSkillNames = candidate.skills.map((s) => s.name.toLowerCase());

        const mustMatch = mustRequirements.filter((req) =>
          candidateSkillNames.some((skill) => skill.includes(req.text.toLowerCase()))
        ).length;

        const niceMatch = niceRequirements.filter((req) =>
          candidateSkillNames.some((skill) => skill.includes(req.text.toLowerCase()))
        ).length;

        const mustPercentage = mustRequirements.length > 0 ? (mustMatch / mustRequirements.length) * 100 : 0;
        const nicePercentage = niceRequirements.length > 0 ? (niceMatch / niceRequirements.length) * 100 : 0;

        const score = Math.round(mustPercentage * 0.7 + nicePercentage * 0.3);

        return {
          ...candidate,
          match: {
            candidateId: candidate.id,
            score,
            mustHaveMatch: Math.round(mustPercentage),
            niceToHaveMatch: Math.round(nicePercentage),
            explanation: `Match ${score}%: ${mustMatch}/${mustRequirements.length} must-have, ${niceMatch}/${niceRequirements.length} nice-to-have`,
          },
        };
      })
      .sort((a, b) => b.match.score - a.match.score);
  }, [candidates, jobDescriptions, selectedJdId]);

  // Suggested profiles (candidates with similar skills)
  const suggestedProfiles = useMemo(() => {
    return candidates.filter((c) => c.id !== currentCandidate.id);
  }, [candidates, currentCandidate]);

  // Handlers
  const handleAddSkill = (skillName: string) => {
    setCandidates((prev) =>
      prev.map((c) =>
        c.id === currentCandidate.id
          ? { ...c, skills: [...c.skills, { name: skillName, level: "intermediate" }] }
          : c
      )
    );
  };

  const handleAddProject = (project: any) => {
    setCandidates((prev) =>
      prev.map((c) => (c.id === currentCandidate.id ? { ...c, projects: [...c.projects, project] } : c))
    );
  };

  const handleAddPost = (content: string) => {
    const newPost: Post = {
      id: `p${Date.now()}`,
      content,
      date: new Date().toISOString().split("T")[0],
      likes: 0,
    };

    setCandidates((prev) =>
      prev.map((c) => (c.id === currentCandidate.id ? { ...c, posts: [newPost, ...c.posts] } : c))
    );
  };

  const handleAddTag = (tag: OptInTag) => {
    setCandidates((prev) =>
      prev.map((c) => (c.id === currentCandidate.id ? { ...c, optInTags: [...c.optInTags, tag] } : c))
    );
  };

  const handleCreateJd = (jd: Omit<JobDescription, "id" | "createdAt">) => {
    const newJd: JobDescription = {
      ...jd,
      id: `jd${Date.now()}`,
      createdAt: new Date().toISOString(),
    };

    setJobDescriptions((prev) => [newJd, ...prev]);

    const logEntry: AuditLogEntry = {
      id: `a${Date.now()}`,
      timestamp: new Date().toISOString(),
      action: "jd_created",
      user: "current.user@company.it",
      details: `Creata JD: ${newJd.title}`,
      deiCompliant: true,
    };

    setAuditLog((prev) => [logEntry, ...prev]);
  };

  const handleCloseShortlist = (jdId: string, override?: { reason: string }) => {
    const logEntry: AuditLogEntry = {
      id: `a${Date.now()}`,
      timestamp: new Date().toISOString(),
      action: override ? "override_triggered" : "shortlist_closed",
      user: "current.user@company.it",
      details: override
        ? `Override DEI guardrail per JD: ${jdId}`
        : `Shortlist chiusa per JD: ${jdId}`,
      deiCompliant: !override,
      overrideReason: override?.reason,
    };

    setAuditLog((prev) => [logEntry, ...prev]);
  };

  const handleConnect = (candidateId: string) => {
    setCandidates((prev) =>
      prev.map((c) =>
        c.id === currentCandidate.id ? { ...c, connections: c.connections + 1 } : c
      )
    );
    toast({ 
      title: "Connessione aggiunta", 
      description: `Ora sei connesso con ${candidates.find(c => c.id === candidateId)?.name}` 
    });
  };

  const handleOpenProfile = (candidateId: string) => {
    setActiveCandidateId(candidateId);
    setActiveTab("candidate");
    toast({ title: "Profilo aperto", description: `Visualizzazione profilo di ${candidates.find(c => c.id === candidateId)?.name}` });
  };

  const handleAddOpportunity = () => {
    toast({ title: "Funzione demo", description: "Aggiungi opportunità - Form non implementato in questa demo" });
  };

  const handleEvaluateMatch = (jdId: string) => {
    setSelectedJdId(jdId);
    setActiveTab("candidate");
  };

  const handleReset = () => {
    setCandidates(mockCandidates);
    setJobDescriptions(mockJobDescriptions);
    setOpportunities(mockOpportunities);
    setFeedback(mockFeedback);
    setAuditLog(mockAuditLog);
    setSelectedJdId(mockJobDescriptions[0]?.id || null);
    toast({ title: "Reset completato", description: "Tutti i dati sono stati ripristinati" });
  };

  const handleExport = () => {
    const data = {
      candidates,
      jobDescriptions,
      opportunities,
      feedback,
      auditLog,
      exportDate: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `recruiting-demo-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    toast({ title: "Export completato", description: "I dati sono stati esportati in JSON" });
  };

  const handleShowInfo = () => {
    setShowOnboarding(true);
  };

  useEffect(() => {
    // Show onboarding on first visit
    const hasVisited = localStorage.getItem("recruiting-demo-visited");
    if (hasVisited) {
      setShowOnboarding(false);
    } else {
      localStorage.setItem("recruiting-demo-visited", "true");
    }
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Header
        deiMode={deiMode}
        onDeiModeChange={setDeiMode}
        onReset={handleReset}
        onExport={handleExport}
        onShowInfo={handleShowInfo}
      />

      <OnboardingModal open={showOnboarding} onClose={() => setShowOnboarding(false)} />

      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-8">
            <TabsTrigger value="candidate" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Candidato
            </TabsTrigger>
            <TabsTrigger value="company" className="flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              Azienda
            </TabsTrigger>
            <TabsTrigger value="pipeline" className="flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              Pipeline
            </TabsTrigger>
            <TabsTrigger value="discover" className="flex items-center gap-2">
              <Compass className="h-4 w-4" />
              Scopri
            </TabsTrigger>
          </TabsList>

          <TabsContent value="candidate">
            <CandidateSection
              candidate={currentCandidate}
              jobDescriptions={jobDescriptions}
              selectedJdId={selectedJdId}
              onSelectJd={setSelectedJdId}
              feedback={feedback}
              onAddSkill={handleAddSkill}
              onAddProject={handleAddProject}
              onAddPost={handleAddPost}
              onAddTag={handleAddTag}
              suggestedProfiles={suggestedProfiles}
              deiMode={deiMode}
              onConnect={handleConnect}
              onOpenProfile={handleOpenProfile}
            />
          </TabsContent>

          <TabsContent value="company">
            <CompanySection
              jobDescriptions={jobDescriptions}
              onCreateJd={handleCreateJd}
              shortlist={shortlist}
              deiMode={deiMode}
              auditLog={auditLog}
              onCloseShortlist={handleCloseShortlist}
            />
          </TabsContent>

          <TabsContent value="pipeline">
            <PipelineSection
              candidates={candidates}
              jobDescriptions={jobDescriptions}
              auditLog={auditLog}
              deiMode={deiMode}
            />
          </TabsContent>

          <TabsContent value="discover">
            <DiscoverSection
              suggestedProfiles={suggestedProfiles}
              opportunities={opportunities}
              jobDescriptions={jobDescriptions}
              onConnect={handleConnect}
              onAddOpportunity={handleAddOpportunity}
              onEvaluateMatch={handleEvaluateMatch}
            />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
