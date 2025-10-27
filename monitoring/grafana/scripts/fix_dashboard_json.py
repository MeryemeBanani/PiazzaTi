#!/usr/bin/env python3
"""fix_dashboard_json.py

Small utility to fix corrupted Grafana dashboard JSON files that contain
leading/trailing garbage (git/HEAD markers, embedded shell snippets, BOMs).

Usage:
  python3 fix_dashboard_json.py /opt/piazzati/monitoring/grafana/dashboards/piazzati-dashboard.json

The script will create a backup: <file>.bak.<timestamp> and write a fixed file
to <file>.fixed (and optionally overwrite the original with --inplace).
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime


def remove_bom(data: bytes) -> bytes:
    # UTF-8 BOM
    BOM = b"\xef\xbb\xbf"
    if data.startswith(BOM):
        return data[len(BOM):]
    return data


def extract_first_json_object(text: str) -> str | None:
    """Find the first balanced JSON object in text and return it, or None."""
    start = None
    depth = 0
    in_string = False
    esc = False
    for i, ch in enumerate(text):
        if start is None:
            if ch == '{' and not in_string:
                start = i
                depth = 1
                continue
            if ch == '"' and not esc:
                in_string = not in_string
            esc = (ch == '\\' and not esc)
            continue

        # we're inside a candidate object
        if ch == '"' and not esc:
            in_string = not in_string
        if not in_string:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        esc = (ch == '\\' and not esc)

    return None


def backup_file(path: str) -> str:
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    bak = f"{path}.bak.{ts}"
    shutil.copy2(path, bak)
    return bak


def main():
    p = argparse.ArgumentParser(description="Fix Grafana dashboard JSON files")
    p.add_argument('file', help='Path to dashboard JSON file')
    p.add_argument('--inplace', action='store_true', help='Replace original file when fixed')
    args = p.parse_args()

    path = args.file
    if not os.path.isfile(path):
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(2)

    with open(path, 'rb') as f:
        raw = f.read()

    raw = remove_bom(raw)
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        print("ERROR: file is not valid UTF-8", file=sys.stderr)
        sys.exit(3)

    # quick try: is whole file valid JSON?
    try:
        obj = json.loads(text)
        fixed_text = json.dumps(obj, indent=2)
        out_path = path + '.fixed'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(fixed_text)
        print(f"OK: file is valid JSON. Wrote pretty output to {out_path}")
        if args.inplace:
            bak = backup_file(path)
            shutil.move(out_path, path)
            print(f"Replaced original (backup: {bak})")
        sys.exit(0)
    except json.JSONDecodeError:
        # fall through to extraction
        pass

    candidate = extract_first_json_object(text)
    if not candidate:
        print("ERROR: couldn't find a balanced JSON object in the file", file=sys.stderr)
        sys.exit(4)

    # validate candidate
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError as e:
        print(f"ERROR: extracted candidate still invalid JSON: {e}", file=sys.stderr)
        # write candidate for inspection
        out_path = path + '.candidate'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(candidate)
        print(f"Wrote candidate to {out_path} for manual inspection")
        sys.exit(5)

    fixed_text = json.dumps(obj, indent=2, ensure_ascii=False)
    out_path = path + '.fixed'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(fixed_text)

    print(f"SUCCESS: extracted and validated JSON written to {out_path}")
    if args.inplace:
        bak = backup_file(path)
        shutil.move(out_path, path)
        print(f"Replaced original file with fixed version (backup: {bak})")


if __name__ == '__main__':
    main()
