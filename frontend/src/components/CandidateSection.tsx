import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Candidate, JobDescription, Feedback, Project, OptInTag } from "@/types";
import { Plus, Briefcase, Award, FileText, MessageSquare, Heart, Users, TrendingUp, Send, Upload, UserPlus, Tag } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface CandidateSectionProps {
  candidate: Candidate;
  jobDescriptions: JobDescription[];
  selectedJdId: string | null;
  onSelectJd: (id: string) => void;
  feedback: Feedback[];
  onAddSkill: (skill: string) => void;
  onAddProject: (project: Project) => void;
  onAddPost: (content: string) => void;
  onAddTag: (tag: OptInTag) => void;
  suggestedProfiles: Candidate[];
  deiMode: boolean;
  onConnect: (candidateId: string) => void;
  onOpenProfile: (candidateId: string) => void;
}

export const CandidateSection = ({
  candidate,
  jobDescriptions,
  selectedJdId,
  onSelectJd,
  feedback,
  onAddSkill,
  onAddProject,
  onAddPost,
  onAddTag,
  suggestedProfiles,
  deiMode,
  onConnect,
  onOpenProfile,
}: CandidateSectionProps) => {
  const [newSkill, setNewSkill] = useState("");
  const [newPost, setNewPost] = useState("");
  
  // Project modal
  const [projectModalOpen, setProjectModalOpen] = useState(false);
  const [projectForm, setProjectForm] = useState({ title: "", description: "", technologies: "", link: "" });
  
  // Tag modal
  const [tagModalOpen, setTagModalOpen] = useState(false);
  const [newTagLabel, setNewTagLabel] = useState("");
  const [newTagCategory, setNewTagCategory] = useState<"diversity" | "background" | "other">("diversity");
  
  // CV from text modal
  const [cvModalOpen, setCvModalOpen] = useState(false);
  const [cvText, setCvText] = useState("");

  // CV file upload
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUploadCV = async () => {
    if (!cvFile) {
      toast({ title: "Seleziona un file", description: "Carica un file CV", variant: "destructive" });
      return;
    }
    setUploading(true);
    const formData = new FormData();
    formData.append("file", cvFile);
    try {
      const response = await fetch("/api/upload_cv", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error("Errore upload");
      const data = await response.json();
      // Aggiorna il profilo candidato con i dati parsati dal backend
      if (data) {
        if (data.skills) onAddSkill && data.skills.forEach((s: any) => onAddSkill(s.name));
        if (data.summary) candidate.summary = data.summary;
        if (data.experiences) candidate.experiences = data.experiences;
        if (data.projects) onAddProject && data.projects.forEach((p: any) => onAddProject(p));
        toast({ title: "CV caricato!", description: "Parsing completato e profilo aggiornato." });
      } else {
        toast({ title: "CV caricato!", description: "Parsing completato." });
      }
    } catch (err) {
      toast({ title: "Errore upload", description: String(err), variant: "destructive" });
    } finally {
      setUploading(false);
      setCvFile(null);
    }
  };

  const selectedJd = jobDescriptions.find((jd) => jd.id === selectedJdId);

  // Mock compatibility calculation
  const calculateCompatibility = () => {
    if (!selectedJd) return null;

    const mustRequirements = selectedJd.requirements.filter((r) => r.type === "must");
    const niceRequirements = selectedJd.requirements.filter((r) => r.type === "nice");

    const candidateSkillNames = candidate.skills.map((s) => s.name.toLowerCase());

    const mustMatch = mustRequirements.filter((req) =>
      candidateSkillNames.some((skill) => skill.includes(req.text.toLowerCase()))
    ).length;

    const niceMatch = niceRequirements.filter((req) =>
      candidateSkillNames.some((skill) => skill.includes(req.text.toLowerCase()))
    ).length;

    const mustPercentage = mustRequirements.length > 0 ? (mustMatch / mustRequirements.length) * 100 : 0;
    const nicePercentage = niceRequirements.length > 0 ? (niceMatch / niceRequirements.length) * 100 : 0;

    const overallScore = mustPercentage * 0.7 + nicePercentage * 0.3;

    return {
      score: Math.round(overallScore),
      mustMatch,
      mustTotal: mustRequirements.length,
      mustPercentage: Math.round(mustPercentage),
      niceMatch,
      niceTotal: niceRequirements.length,
      nicePercentage: Math.round(nicePercentage),
    };
  };

  const compatibility = calculateCompatibility();

  const handleAddSkill = () => {
    if (newSkill.trim()) {
      onAddSkill(newSkill.trim());
      setNewSkill("");
      toast({ title: "Skill aggiunta", description: `"${newSkill}" aggiunta al profilo` });
    }
  };

  const handleAddPost = () => {
    if (newPost.trim()) {
      onAddPost(newPost.trim());
      setNewPost("");
      toast({ title: "Post pubblicato", description: "Il tuo post è ora visibile sul tuo wall" });
    }
  };

  const handleAddProject = () => {
    if (!projectForm.title.trim() || !projectForm.description.trim()) {
      toast({ title: "Campi obbligatori", description: "Titolo e descrizione sono richiesti", variant: "destructive" });
      return;
    }

    const newProject: Project = {
      title: projectForm.title,
      description: projectForm.description,
      technologies: projectForm.technologies.split(",").map(t => t.trim()).filter(t => t),
      link: projectForm.link || undefined,
    };

    onAddProject(newProject);
    setProjectForm({ title: "", description: "", technologies: "", link: "" });
    setProjectModalOpen(false);
    toast({ title: "Progetto aggiunto", description: `"${newProject.title}" aggiunto al portfolio` });
  };

  const handleAddTag = () => {
    if (!newTagLabel.trim()) {
      toast({ title: "Etichetta richiesta", description: "Inserisci un'etichetta per il tag", variant: "destructive" });
      return;
    }

    const newTag: OptInTag = {
      label: newTagLabel.trim(),
      category: newTagCategory,
    };

    onAddTag(newTag);
    setNewTagLabel("");
    setTagModalOpen(false);
    toast({ title: "Tag aggiunto", description: `Tag "${newTag.label}" aggiunto al profilo` });
  };

  const handleCreateFromText = () => {
    if (!cvText.trim()) {
      toast({ title: "Testo richiesto", description: "Inserisci il testo del CV", variant: "destructive" });
      return;
    }

    // Simple parser (demo)
    const skills = cvText.match(/\b(React|TypeScript|Python|Node\.js|Java|AWS|Docker|Kubernetes|SQL|PostgreSQL|MongoDB)\b/gi) || [];
    
    toast({ 
      title: "CV parsato", 
      description: `Trovate ${skills.length} skill. In una versione reale, verrebbe creato un nuovo candidato.`,
    });
    
    setCvText("");
    setCvModalOpen(false);
  };

  const handleSubmitApplication = () => {
    if (!selectedJdId) {
      toast({ title: "Seleziona una JD", description: "Seleziona una posizione prima di candidarti", variant: "destructive" });
      return;
    }

    const jd = jobDescriptions.find(j => j.id === selectedJdId);
    toast({ 
      title: "Candidatura inviata!", 
      description: `La tua candidatura per "${jd?.title}" è stata inviata con successo (demo)`,
    });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main Profile Column */}
      <div className="lg:col-span-2 space-y-6">
        {/* Profile Header */}
        <Card className="p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary text-2xl font-bold text-primary-foreground">
              {candidate.name.split(" ").map((n) => n[0]).join("")}
            </div>
            <div className="flex-1">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold">{candidate.name}</h2>
                  <p className="text-muted-foreground">{candidate.location}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold">{candidate.connections}</p>
                  <p className="text-xs text-muted-foreground">connessioni</p>
                  {deiMode && candidate.optInTags.length > 0 && (
                    <div className="mt-2">
                      <Badge variant="outline" className="border-success text-success">
                        {candidate.optInTags.length} tag opt-in
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
              <p className="mt-2">{candidate.summary}</p>
              {candidate.optInTags.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {candidate.optInTags.map((tag, i) => (
                    <Badge key={i} variant="outline" className="border-success text-success">
                      {tag.label}
                    </Badge>
                  ))}
                  {deiMode && (
                    <Button variant="ghost" size="sm" onClick={() => setTagModalOpen(true)}>
                      <Plus className="h-3 w-3 mr-1" />
                      Tag
                    </Button>
                  )}
                </div>
              )}
              {deiMode && candidate.optInTags.length === 0 && (
                <div className="mt-3">
                  <Button variant="outline" size="sm" onClick={() => setTagModalOpen(true)}>
                    <Tag className="h-3 w-3 mr-1" />
                    Aggiungi tag opt-in
                  </Button>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Skills */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Award className="h-5 w-5 text-primary" />
              Competenze
            </h3>
          </div>
          <div className="flex flex-wrap gap-2 mb-4">
            {candidate.skills.map((skill, i) => (
              <Badge key={i} variant="secondary">
                {skill.name}
                {skill.level && <span className="ml-1 text-xs opacity-70">({skill.level})</span>}
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Nuova skill..."
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddSkill()}
            />
            <Button onClick={handleAddSkill}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </Card>

        {/* Experience */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Briefcase className="h-5 w-5 text-primary" />
            Esperienze
          </h3>
          <div className="space-y-4">
            {candidate.experiences.map((exp, i) => (
              <div key={i} className="border-l-2 border-primary pl-4">
                <h4 className="font-semibold">{exp.title}</h4>
                <p className="text-sm text-muted-foreground">
                  {exp.company} • {exp.period}
                </p>
                <p className="text-sm mt-1">{exp.description}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Projects */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Progetti
            </h3>
            <Button variant="outline" size="sm" onClick={() => setProjectModalOpen(true)}>
              <Plus className="h-4 w-4 mr-1" />
              Progetto
            </Button>
          </div>
          <div className="space-y-4">
            {candidate.projects.map((project, i) => (
              <div key={i} className="rounded-lg border p-4">
                <h4 className="font-semibold">{project.title}</h4>
                <p className="text-sm text-muted-foreground mt-1">{project.description}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {project.technologies.map((tech, j) => (
                    <Badge key={j} variant="outline" className="text-xs">
                      {tech}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Wall / Posts */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <MessageSquare className="h-5 w-5 text-primary" />
            Wall
          </h3>
          <div className="space-y-4 mb-4">
            {candidate.posts.map((post) => (
              <div key={post.id} className="rounded-lg border p-4">
                <p className="text-sm">{post.content}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <span>{post.date}</span>
                  <button className="flex items-center gap-1 hover:text-foreground transition-colors">
                    <Heart className="h-3 w-3" />
                    {post.likes}
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="space-y-2">
            <Textarea
              placeholder="Condividi un pensiero, un link o un aggiornamento..."
              value={newPost}
              onChange={(e) => setNewPost(e.target.value)}
            />
            <Button onClick={handleAddPost} className="w-full">
              <Plus className="h-4 w-4 mr-1" />
              Pubblica Post
            </Button>
          </div>
        </Card>
      </div>

      {/* Sidebar Column */}
      <div className="space-y-6">
        {/* Upload CV da file */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Upload className="h-5 w-5 text-primary" />
            Carica CV (file)
          </h3>
          <Input
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={e => setCvFile(e.target.files?.[0] || null)}
          />
          <Button
            variant="outline"
            className="w-full mt-2"
            onClick={handleUploadCV}
            disabled={uploading}
          >
            <Upload className="h-4 w-4 mr-2" />
            {uploading ? "Caricamento..." : "Carica CV"}
          </Button>
        </Card>
        {/* Aggiungi CV da testo (modal) */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Upload className="h-5 w-5 text-primary" />
            Aggiungi CV da testo
          </h3>
          <Button variant="outline" className="w-full" onClick={() => setCvModalOpen(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Carica testo CV
          </Button>
        </Card>

        {/* JD Selector & Compatibility */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Job Description</h3>
          <div className="space-y-4">
            <div>
              <Label>Seleziona JD</Label>
              <Select value={selectedJdId || ""} onValueChange={onSelectJd}>
                <SelectTrigger>
                  <SelectValue placeholder="Scegli una posizione..." />
                </SelectTrigger>
                <SelectContent>
                  {jobDescriptions.map((jd) => (
                    <SelectItem key={jd.id} value={jd.id}>
                      {jd.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {compatibility && (
              <div className="space-y-3 mt-4 p-4 rounded-lg bg-muted">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">Compatibilità</span>
                  <span className="text-2xl font-bold text-primary">{compatibility.score}%</span>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-muted-foreground">Must-have</span>
                      <span className="font-medium">
                        {compatibility.mustMatch}/{compatibility.mustTotal} ({compatibility.mustPercentage}%)
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-background">
                      <div
                        className="h-full rounded-full bg-primary transition-all"
                        style={{ width: `${compatibility.mustPercentage}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-muted-foreground">Nice-to-have</span>
                      <span className="font-medium">
                        {compatibility.niceMatch}/{compatibility.niceTotal} ({compatibility.nicePercentage}%)
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-background">
                      <div
                        className="h-full rounded-full bg-accent transition-all"
                        style={{ width: `${compatibility.nicePercentage}%` }}
                      />
                    </div>
                  </div>
                </div>

                <p className="text-xs text-muted-foreground mt-2">
                  Score calcolato: 70% must-have + 30% nice-to-have
                </p>

                <Button onClick={handleSubmitApplication} className="w-full mt-4">
                  <Send className="h-4 w-4 mr-2" />
                  Invia candidatura (demo)
                </Button>
              </div>
            )}
          </div>
        </Card>

        {/* Feedback ricevuti */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Feedback Ricevuti</h3>
          <div className="space-y-3">
            {feedback.map((fb) => (
              <div key={fb.id} className="rounded-lg border p-3 text-sm">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold">{fb.from}</span>
                  <Badge
                    variant={fb.type === "positive" ? "default" : "outline"}
                    className={
                      fb.type === "positive"
                        ? "bg-success text-success-foreground"
                        : fb.type === "constructive"
                        ? "border-warning text-warning"
                        : ""
                    }
                  >
                    {fb.type}
                  </Badge>
                </div>
                <p className="text-muted-foreground text-xs mb-1">{fb.message}</p>
                <span className="text-xs text-muted-foreground">{fb.date}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Profili Consigliati */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Users className="h-5 w-5 text-primary" />
            Profili Consigliati
          </h3>
          <div className="space-y-3">
            {suggestedProfiles.slice(0, 3).map((profile) => (
              <div key={profile.id} className="rounded-lg border p-3">
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                    {profile.name.split(" ").map((n) => n[0]).join("")}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm truncate">{profile.name}</p>
                    <p className="text-xs text-muted-foreground truncate">{profile.location}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1 mb-2">
                  {profile.skills.slice(0, 3).map((skill, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {skill.name}
                    </Badge>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="flex-1" onClick={() => onConnect(profile.id)}>
                    <UserPlus className="h-3 w-3 mr-1" />
                    Connetti
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => onOpenProfile(profile.id)}>
                    <TrendingUp className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Project Modal */}
      <Dialog open={projectModalOpen} onOpenChange={setProjectModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Aggiungi Progetto</DialogTitle>
            <DialogDescription>Inserisci i dettagli del progetto da aggiungere al tuo portfolio.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="project-title">Titolo *</Label>
              <Input
                id="project-title"
                value={projectForm.title}
                onChange={(e) => setProjectForm({ ...projectForm, title: e.target.value })}
                placeholder="es. Dashboard Analytics"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-desc">Descrizione *</Label>
              <Textarea
                id="project-desc"
                value={projectForm.description}
                onChange={(e) => setProjectForm({ ...projectForm, description: e.target.value })}
                placeholder="Descrivi il progetto..."
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-tech">Tecnologie (separate da virgola)</Label>
              <Input
                id="project-tech"
                value={projectForm.technologies}
                onChange={(e) => setProjectForm({ ...projectForm, technologies: e.target.value })}
                placeholder="es. React, TypeScript, Tailwind"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-link">Link (opzionale)</Label>
              <Input
                id="project-link"
                value={projectForm.link}
                onChange={(e) => setProjectForm({ ...projectForm, link: e.target.value })}
                placeholder="https://github.com/..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setProjectModalOpen(false)}>Annulla</Button>
            <Button onClick={handleAddProject}>Aggiungi Progetto</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Tag Modal */}
      <Dialog open={tagModalOpen} onOpenChange={setTagModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Aggiungi Tag Opt-in</DialogTitle>
            <DialogDescription>
              I tag opt-in sono volontari e usati solo per reportistica/guardrail, non per il punteggio.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="tag-label">Etichetta *</Label>
              <Input
                id="tag-label"
                value={newTagLabel}
                onChange={(e) => setNewTagLabel(e.target.value)}
                placeholder="es. Women in Tech, First-gen graduate..."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tag-category">Categoria</Label>
              <Select value={newTagCategory} onValueChange={(v) => setNewTagCategory(v as typeof newTagCategory)}>
                <SelectTrigger id="tag-category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="diversity">Diversity</SelectItem>
                  <SelectItem value="background">Background</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTagModalOpen(false)}>Annulla</Button>
            <Button onClick={handleAddTag}>Aggiungi Tag</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* CV from Text Modal */}
      <Dialog open={cvModalOpen} onOpenChange={setCvModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Crea CV da Testo</DialogTitle>
            <DialogDescription>
              Incolla il testo del CV. Un parser dummy estrarrà nome, summary e skill (demo).
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="cv-text">Testo CV</Label>
              <Textarea
                id="cv-text"
                value={cvText}
                onChange={(e) => setCvText(e.target.value)}
                placeholder="Incolla qui il testo del CV..."
                rows={8}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCvModalOpen(false)}>Annulla</Button>
            <Button onClick={handleCreateFromText}>
              <Upload className="h-4 w-4 mr-2" />
              Crea da Testo
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
