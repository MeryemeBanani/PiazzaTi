import os
import sys

# ensure backend package is importable when tests run from repo root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.schemas.parsed_document import DocumentType, ParsedDocument, PersonalInfo  # noqa: E402, E501


def test_parsed_document_minimal():
    pd = ParsedDocument(document_type=DocumentType.cv)
    assert pd.document_type == DocumentType.cv
    assert isinstance(pd.personal_info, PersonalInfo)
    # defaults
    assert pd.confidence_score == 0.0
    assert pd.warnings == []


def test_detect_missing_sections_and_confidence():
    pd = ParsedDocument(document_type=DocumentType.cv)
    pd.detect_missing_sections()
    assert any("Missing professional summary" in w for w in pd.warnings)
    pd.compute_section_confidence()
    assert "personal_info" in pd.section_confidence
