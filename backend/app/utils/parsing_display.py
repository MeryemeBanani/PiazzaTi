from typing import Any, Dict, Tuple

from ..schemas.parsed_document import ParsedDocument


def display_parsing_results(doc: ParsedDocument) -> str:
    """Create a human-friendly summary of a parsed document.

    Returns a multi-line string suitable for logs or UI display.
    """
    lines = []
    lines.append(f"Document: {doc.file_name or doc.document_id}")
    lines.append(f"Parsed at: {doc.parsed_at}")
    lines.append(f"Document type: {doc.document_type}")
    if doc.personal_info:
        pi = doc.personal_info
        lines.append("\nPersonal Info:")
        if pi.full_name:
            lines.append(f"  Name: {pi.full_name}")
        if pi.email:
            lines.append(f"  Email: {pi.email}")
        if pi.phone:
            lines.append(f"  Phone: {pi.phone}")
        if getattr(pi, "address", None):
            lines.append(f"  Address: {pi.address}")

    if doc.experience:
        lines.append("\nExperiences:")
        for e in doc.experience[:6]:
            lines.append(
                f"  - {e.title} @ {e.company} "
                f"({e.start_date or '?'} - {e.end_date or 'present'})"
            )

    if doc.education:
        lines.append("\nEducation:")
        for ed in doc.education[:4]:
            lines.append(
                f"  - {ed.degree or ed.institution} "
                f"({ed.start_date or '?'} - {ed.end_date or '?'})"
            )

    if doc.skills:
        lines.append("\nSkills:")
        for s in doc.skills[:40]:
            lines.append(f"  - {s.name} ({s.level or 'n/a'})")

    if doc.warnings:
        lines.append("\nWarnings:")
        for w in doc.warnings:
            lines.append(f"  - {w}")

    return "\n".join(lines)


def compute_extraction_stats(doc: ParsedDocument) -> Dict[str, Any]:
    """Compute simple statistics for parsed document quality."""
    stats = {
        "n_experiences": len(doc.experience or []),
        "n_education": len(doc.education or []),
        "n_skills": len(doc.skills or []),
        "n_languages": len(doc.languages or []),
        "has_personal_info": bool(
            doc.personal_info
            and (doc.personal_info.email or doc.personal_info.full_name)
        ),
    }
    return stats


def validate_parsing_quality(doc: ParsedDocument) -> Tuple[bool, Dict[str, Any]]:
    """Return (is_ok, report).

    Heuristics-based quality checks.
    """
    report = {}
    is_ok = True

    stats = compute_extraction_stats(doc)
    report.update(stats)

    if not stats["has_personal_info"]:
        is_ok = False
        report["missing"] = report.get("missing", []) + ["personal_info"]

    if stats["n_experiences"] == 0 and stats["n_education"] == 0:
        is_ok = False
        report["missing"] = report.get("missing", []) + ["experiences_or_education"]

    if stats["n_skills"] < 3:
        report["low_skills"] = True

    return is_ok, report


def print_validation_report(doc: ParsedDocument) -> str:
    is_ok, rep = validate_parsing_quality(doc)
    lines = [f"Quality: {'OK' if is_ok else 'ISSUE'}"]
    for k, v in rep.items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)
