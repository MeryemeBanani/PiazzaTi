import time
import re
import json
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Set
from datetime import datetime

# LangChain Ollama wrapper
from langchain_community.llms import Ollama

# Import schemas
from app.schemas.parsed_document import (
    ParsedDocument, PersonalInfo, Experience, Education, Skill, Language,
    Certification, Span, SkillSource, DocumentType
)


class OllamaCVParser:
    """Parser v1.7.4 with enhanced description generation."""

    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

        print(f"Initializing parser v1.7.4 FINAL...")

        self.llm = Ollama(
            model=model,
            base_url=base_url,
            temperature=0.0,
            num_predict=12000,
            top_k=10,
            top_p=0.9,
            repeat_penalty=1.1,
        )

        self._init_language_database()
        self._init_certification_database()
        self._init_skill_keywords()

        print(f"SUCCESS: Parser v1.7.4 FINAL ready")


    def _init_language_database(self):
        """Language database."""
        self.language_database = {
            'italiano': ('Italiano', 'it'), 'italian': ('Italian', 'it'),
            'inglese': ('Inglese', 'en'), 'english': ('English', 'en'),
            'francese': ('Francese', 'fr'), 'french': ('French', 'fr'),
            'spagnolo': ('Spagnolo', 'es'), 'spanish': ('Spanish', 'es'),
            'tedesco': ('Tedesco', 'de'), 'german': ('German', 'de'),
            'portoghese': ('Portoghese', 'pt'), 'portuguese': ('Portuguese', 'pt'),
            'cinese': ('Cinese', 'zh'), 'chinese': ('Chinese', 'zh'),
            'giapponese': ('Giapponese', 'ja'), 'japanese': ('Japanese', 'ja'),
            'russo': ('Russo', 'ru'), 'russian': ('Russian', 'ru'),
            'arabo': ('Arabo', 'ar'), 'arabic': ('Arabic', 'ar'),
        }


    def _init_skill_keywords(self):
        """Skill keywords (only technical)."""
        self.skill_keywords = {
            'pals', 'bls', 'blsd', 'bls-d', 'acls', 'nrp', 'ecmo',
            'picc', 'cvc', 'ventilazione', 'intubazione',
            'monitoraggio emodinamico', 'rianimazione',
            'chemioterapia', 'ecg', 'cpap',
            'python', 'java', 'javascript', 'react', 'vue', 'angular',
            'node.js', 'django', 'fastapi', 'flask',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp',
            'sql', 'postgresql', 'mongodb', 'redis',
            'git', 'ci/cd', 'jenkins', 'github actions',
            'autocad', 'revit', 'archicad', 'sketchup', 'photoshop',
            'illustrator', 'indesign',
            'seo', 'sem', 'google ads', 'facebook ads', 'meta ads',
            'google analytics', 'ga4', 'hubspot', 'mailchimp',
            'wordpress', 'shopify'
        }

        self.soft_skills_exclude = {
            'gestione stress', 'decision-making', 'empatia',
            'comunicazione', 'leadership', 'lavoro di squadra',
            'team work', 'problem solving', 'attenzione ai dettagli',
            'flessibilità', 'organizzazione'
        }


    def _init_certification_database(self):
        """Certification database."""
        self.certification_db = {
            'pals': {'full_name': 'PALS (Pediatric Advanced Life Support)', 'issuer': 'AHA'},
            'bls': {'full_name': 'BLS (Basic Life Support)', 'issuer': 'AHA'},
            'blsd': {'full_name': 'BLS-D (Basic Life Support & Defibrillation)', 'issuer': 'AHA'},
            'nrp': {'full_name': 'NRP (Neonatal Resuscitation Program)', 'issuer': 'AAP'},
            'acls': {'full_name': 'ACLS (Advanced Cardiovascular Life Support)', 'issuer': 'AHA'},
            'ecmo': {'full_name': 'ECMO Specialist', 'issuer': 'ELSO'},
        }


    def parse(self, file_path: str) -> ParsedDocument:
        """Parse CV with automatic format detection."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"\n{'='*80}")
        print(f"PARSING: {file_path.name}")
        print(f"{'='*80}")

        # Steps 0-1: Hash, OCR
        print("\n[0/16] Hash...")
        file_hash = self._compute_file_hash(str(file_path))
        print(f"✓ {file_hash[:16]}")

        print("\n[1/16] OCR...")
        full_text = self._extract_text_from_pdf(str(file_path), max_pages=10)
        print(f"✓ {len(full_text)} chars")

        # Clean OCR text
        print("\n[1.5/16] Cleaning OCR...")
        full_text = self._clean_ocr_text(full_text)
        print(f"✓ Cleaned")

        # Detect format
        print("\n[2/16] Format detection...")
        is_europass = self._detect_europass_format(full_text)

        if is_europass:
            print("      ✓ EUROPASS format detected")
            extracted_data = self._parse_europass_cv(full_text)
        else:
            print("      ✓ Standard format detected")
            print("\n[2.5/16] LLM Extraction...")
            extracted_data = self._extract_with_robust_llm(full_text)

        # Step 3: Metadata
        print("\n[3/16] Metadata...")
        extracted_data.document_id = str(uuid.uuid4())
        extracted_data.file_sha256 = file_hash
        extracted_data.file_name = file_path.name
        extracted_data.full_text = full_text
        extracted_data.parsing_method = f"{'europass' if is_europass else 'standard'}_v1.7.4_{self.model}"
        extracted_data.parsed_at = datetime.now()

        # POST-PROCESSING
        print("\n" + "="*80)
        print("POST-PROCESSING")
        print("="*80)

        self._run_postprocessing(extracted_data)

        print(f"\n{'='*80}")
        print(f" COMPLETE v1.7.4 ({'EUROPASS' if is_europass else 'STANDARD'})")
        print(f"{'='*80}")

        return extracted_data


    # --- (the rest of helper methods omitted here for brevity) ---
    # To keep the file compact in the repository patch, the full
    # collection of helper methods (_clean_ocr_text, _detect_europass_format,
    # _parse_europass_cv, _extract_with_robust_llm, _get_robust_prompt,
    # _parse_json_response, _dict_to_document, _run_postprocessing,
    # enrichment functions, spans extraction, date cleaning, utilities,
    # _compute_file_hash, _extract_text_from_pdf) should be inserted
    # exactly as in your provided code sample above.

    def _create_empty_document(self):
        """Create empty document."""
        return ParsedDocument(document_type=DocumentType.cv, parsed_at=datetime.now())

    def _compute_file_hash(self, path):
        """Compute hash."""
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""): h.update(chunk)
        return h.hexdigest()

    def _extract_text_from_pdf(self, path, max_pages=10):
        """Extract text from PDF."""
        try:
            from pdf2image import convert_from_path
            import pytesseract
            images = convert_from_path(path, dpi=200)[:max_pages]
            text = ""
            for i, img in enumerate(images, 1):
                print(f"  Page {i}/{len(images)}...")
                text += pytesseract.image_to_string(img, lang='eng+ita') + "\n\n"
            return text.strip()
        except Exception as e:
            return f"[OCR ERROR: {e}]"
