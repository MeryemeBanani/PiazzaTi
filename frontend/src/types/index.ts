export interface Skill {
  name: string;
  level?: "beginner" | "intermediate" | "advanced" | "expert";
}

export interface Experience {
  title: string;
  company: string;
  period: string;
  description: string;
}

export interface Project {
  title: string;
  description: string;
  technologies: string[];
  link?: string;
}

export interface Post {
  id: string;
  content: string;
  date: string;
  likes: number;
}

export interface OptInTag {
  label: string;
  category: "diversity" | "background" | "other";
}

export interface Candidate {
  id: string;
  name: string;
  location: string;
  summary: string;
  skills: Skill[];
  experiences: Experience[];
  projects: Project[];
  posts: Post[];
  optInTags: OptInTag[];
  avatarUrl?: string;
  connections: number;
}

export interface JobRequirement {
  text: string;
  type: "must" | "nice";
}

export interface JobDescription {
  id: string;
  title: string;
  company: string;
  description: string;
  requirements: JobRequirement[];
  salary?: string;
  location: string;
  createdAt: string;
}

export interface CandidateMatch {
  candidateId: string;
  score: number;
  mustHaveMatch: number;
  niceToHaveMatch: number;
  explanation: string;
}

export interface ShortlistCandidate extends Candidate {
  match: CandidateMatch;
}

export interface Feedback {
  id: string;
  from: string;
  message: string;
  date: string;
  type: "positive" | "constructive" | "neutral";
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: "shortlist_closed" | "override_triggered" | "jd_created" | "candidate_added";
  user: string;
  details: string;
  deiCompliant?: boolean;
  overrideReason?: string;
}

export interface Opportunity {
  id: string;
  title: string;
  type: "grant" | "hackathon" | "course" | "fellowship" | "other";
  organization: string;
  description: string;
  deadline?: string;
  link?: string;
}

export interface InclusivityIssue {
  term: string;
  severity: "high" | "medium" | "low";
  suggestion: string;
  position: number;
}
