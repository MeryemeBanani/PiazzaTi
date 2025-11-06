"""Utility: validate a parsed JSON example against the Pydantic model.

Usage (from repo root, in your Python venv):

    python backend/scripts/validate_parsed_example.py \
        "c:\\Users\\Merye\\AppData\\Local\\Microsoft\\Windows\\INetCache\\IE\\YXJ0PAY3\\cv_0342_Ilaria_Barbieri_IT_parsed[1].json"

The script prints a short verification of the parsed object (user_id, tags keys,
experience titles, span counts). It exits with code 0 on success, non-zero on
validation error.
"""
import json
import sys
from pathlib import Path


def main(path_str: str):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))

    sample_path = Path(path_str)
    if not sample_path.exists():
        print(f"ERROR: example file not found: {sample_path}")
        return 2

    raw = json.loads(sample_path.read_text(encoding="utf-8"))

    # import here so script is lightweight if not used
    from backend.app.schemas.parsed_document import ParsedDocument

    try:
        # Pydantic v2 uses `model_validate`; v1 uses `parse_obj`.
        if hasattr(ParsedDocument, "model_validate"):
            parsed = ParsedDocument.model_validate(raw)
        elif hasattr(ParsedDocument, "parse_obj"):
            parsed = ParsedDocument.parse_obj(raw)
        else:
            # Fallback: try constructor
            parsed = ParsedDocument(**raw)
    except Exception as e:
        print("ERROR: Pydantic validation failed:")
        print(e)
        return 3

    print("OK: Parsed ParsedDocument")
    print("document_id:", parsed.document_id)
    print("user_id:", parsed.user_id)
    print("tags keys:", list(parsed.tags.keys())[:20])
    print("experience titles:", [e.title for e in parsed.experience])
    print("# all_spans:", len(parsed.all_spans))
    print("# warnings:", len(parsed.warnings))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backend/scripts/validate_parsed_example.py <example.json>")
        raise SystemExit(1)
    rc = main(sys.argv[1])
    raise SystemExit(rc)
