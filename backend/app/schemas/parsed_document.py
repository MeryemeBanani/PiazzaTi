from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# ========================================================================
# ENUMS
# ========================================================================


class DocumentType(str, Enum):
    cv = "cv"
    jd = "jd"


class SkillSource(str, Enum):
    extracted = "extracted"
    inferred = "inferred"
    heuristic = "heuristic"


# ========================================================================
#  UPDATED: PersonalInfo with 'address' field
# ========================================================================


class PersonalInfo(BaseModel):
    """
    UPDATED v1.4.10: Added 'address' field, deprecated 'street'.
    """

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    # NEW: Unified address field
    address: Optional[str] = Field(
        None, description="Full address: Via Roma 156, 35100 Padova (PD)"
    )

    city: Optional[str] = None
    state: Optional[str] = Field(
        None, description="DEPRECATED: Always null, will be removed"
    )
    country: Optional[str] = None
    postal_code: Optional[str] = None

    # Social/Web
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None

    #  DEPRECATED: Use 'address' instead
    street: Optional[str] = Field(
        None, description="DEPRECATED: Use 'address' field instead"
    )


# ========================================================================
# OTHER MODELS (unchanged)
# ========================================================================


class Span(BaseModel):
    start: int
    end: int
    text: str
    field: str
    confidence: float = 0.95


class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    spans: List[Span] = Field(default_factory=list)


class Education(BaseModel):
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    institution: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[str] = None
    spans: List[Span] = Field(default_factory=list)


class Skill(BaseModel):
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None
    source: SkillSource = SkillSource.extracted
    confidence: float = 1.0


class Language(BaseModel):
    name: str
    proficiency: Optional[str] = None
    level: Optional[str] = None
    certificate: Optional[str] = None
    certificate_year: Optional[int] = None


class Certification(BaseModel):
    name: str
    issuer: Optional[str] = None
    date_obtained: Optional[str] = None


class Project(BaseModel):
    name: str
    description: Optional[str] = None
    role: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class JobPreferences(BaseModel):
    desired_roles: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    remote_preference: Optional[str] = None
    salary_expectation: Optional[str] = None
    availability: Optional[str] = None


# ========================================================================
# MAIN DOCUMENT MODEL
# ========================================================================


class ParsedDocument(BaseModel):
    # Metadata
    document_id: Optional[str] = None
    document_type: DocumentType
    file_sha256: Optional[str] = None

    #  UPDATED: personal_info with address field
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)

    # Content
    summary: Optional[str] = None
    summary_span: Optional[Span] = None

    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)

    preferences: Optional[JobPreferences] = None
    gdpr_consent: bool = False

    # File info
    file_name: Optional[str] = None
    full_text: Optional[str] = None
    parsing_method: Optional[str] = None
    confidence_score: float = 0.0
    section_confidence: dict = Field(default_factory=dict)

    parsed_at: Optional[datetime] = None

    warnings: List[str] = Field(default_factory=list)
    all_spans: List[Span] = Field(default_factory=list)

    def add_warning(self, warning: str):
        """Add a warning message."""
        if warning not in self.warnings:
            self.warnings.append(warning)

    def collect_all_spans(self):
        """Collect all spans from nested objects."""
        for exp in self.experience:
            self.all_spans.extend(exp.spans)
        for edu in self.education:
            self.all_spans.extend(edu.spans)
        if self.summary_span:
            self.all_spans.append(self.summary_span)

    def detect_missing_sections(self):
        """Detect missing sections and add warnings."""
        if not self.summary:
            self.add_warning("LOW: Missing professional summary (optional section)")
        if len(self.experience) == 0:
            self.add_warning("HIGH: No work experience found")
        if len(self.education) == 0:
            self.add_warning("MEDIUM: No education found")
        if len(self.skills) == 0:
            self.add_warning("MEDIUM: No skills found")
        if len(self.languages) == 0:
            self.add_warning("LOW: No languages found")
        if not self.preferences:
            self.add_warning("LOW: No job preferences found (optional section)")
        if len(self.all_spans) == 0:
            self.add_warning(
                "INFO: No XAI spans extracted (explainability unavailable)"
            )

    def compute_section_confidence(self):
        """Compute confidence scores for each section."""
        # Personal info
        personal_fields = [
            self.personal_info.full_name,
            self.personal_info.email,
            self.personal_info.phone,
            self.personal_info.city,
        ]
        self.section_confidence["personal_info"] = sum(
            1 for f in personal_fields if f
        ) / len(personal_fields)

        # Summary
        self.section_confidence["summary"] = 1.0 if self.summary else 0.0

        # Experience
        if len(self.experience) > 0:
            exp_scores = []
            for exp in self.experience:
                score = (
                    sum(
                        [
                            1 if exp.title else 0,
                            1 if exp.company else 0,
                            1 if exp.start_date else 0,
                            0.5 if exp.description else 0,
                        ]
                    )
                    / 3.5
                )
                exp_scores.append(score)
            self.section_confidence["experience"] = sum(exp_scores) / len(exp_scores)
        else:
            self.section_confidence["experience"] = 0.0

        # Education
        if len(self.education) > 0:
            edu_scores = []
            for edu in self.education:
                score = (
                    sum(
                        [
                            1 if edu.degree else 0,
                            1 if edu.institution else 0,
                            0.5 if edu.graduation_year else 0,
                        ]
                    )
                    / 2.5
                )
                edu_scores.append(score)
            self.section_confidence["education"] = sum(edu_scores) / len(edu_scores)
        else:
            self.section_confidence["education"] = 0.0

        # Skills
        self.section_confidence["skills"] = (
            1.0 if len(self.skills) >= 3 else len(self.skills) / 3
        )

        # Languages
        self.section_confidence["languages"] = (
            1.0 if len(self.languages) >= 2 else len(self.languages) / 2
        )

        # Certifications
        self.section_confidence["certifications"] = (
            1.0 if len(self.certifications) >= 1 else 0.0
        )

        # Preferences
        self.section_confidence["preferences"] = 1.0 if self.preferences else 0.0

        # Overall confidence
        weights = {
            "personal_info": 0.25,
            "experience": 0.25,
            "education": 0.20,
            "skills": 0.15,
            "languages": 0.10,
            "certifications": 0.05,
        }

        self.confidence_score = sum(
            self.section_confidence.get(section, 0) * weight
            for section, weight in weights.items()
        )

    def detect_low_confidence_sections_v2(self):
        """Detect sections with low confidence."""
        for section_key in [
            "personal_info",
            "experience",
            "education",
            "skills",
            "languages",
            "certifications",
        ]:
            confidence = self.section_confidence.get(section_key, 0.0)
            if confidence == 0.0:
                self.add_warning(
                    f"HIGH: Low confidence '{section_key}' ({confidence:.2f})"
                )
            elif confidence < 0.5:
                self.add_warning(
                    f"HIGH: Low confidence for '{section_key}' ({confidence:.2f})"
                )
            elif confidence < 0.7:
                self.add_warning(
                    f"MEDIUM: Moderate confidence '{section_key}' ({confidence:.2f})"
                )
