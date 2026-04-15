#!/usr/bin/env python3
"""
One-shot processing script: incoming field notes -> processed/
- Adds id and revision to frontmatter where missing
- Canonicalizes connects_to file references
- Renames files to FN####_slug.md
- Moves to processed/
Run from notes_symbioquest/ root.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# filename -> canonical ID mapping
# constructed from the field-note-NNN-slug.md filenames in incoming/
# ---------------------------------------------------------------------------

INCOMING_DIR = Path(__file__).parent.parent / "incoming"
PROCESSED_DIR = Path(__file__).parent.parent / "processed"

FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)", re.S | re.DOTALL)
OLD_REF_RE = re.compile(r"field-note-(\d+)-(.+?)(?:\.md)?$", re.I)


def fn_id(num: int) -> str:
    return f"FN{num:04d}"


def canonical_filename(num: int, slug: str) -> str:
    slug = slug.lower().strip("-")
    return f"FN{num:04d}_{slug}.md"


def canonicalize_ref(ref: str, slug_map: dict[str, str]) -> str:
    """Convert field-note-NNN-slug.md ref to FN####_slug.md if known."""
    m = OLD_REF_RE.search(ref.strip())
    if not m:
        return ref  # not a file ref we recognize - leave as is
    num = int(m.group(1))
    slug = m.group(2).rstrip(".md").rstrip(".")
    fid = fn_id(num)
    # look up canonical filename from slug_map
    if fid in slug_map:
        return slug_map[fid]
    # construct best-guess canonical if not in map
    return canonical_filename(num, slug)


def process_file(path: Path, num: int, slug_map: dict[str, str], dry_run: bool = False):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    m = FM_RE.match(raw)
    if not m:
        print(f"  SKIP (no frontmatter): {path.name}")
        return None

    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)

    fid = fn_id(num)
    slug = path.stem.replace(f"field-note-{num:03d}-", "").lower()
    # handle both zero-padded and non-padded
    slug = re.sub(r"^field-note-\d+-", "", path.stem, flags=re.I).lower()

    out_filename = canonical_filename(num, slug)
    out_path = PROCESSED_DIR / out_filename

    # patch frontmatter
    fm["id"] = fid
    if "revision" not in fm:
        fm["revision"] = 1

    # canonicalize connects_to
    connects = fm.get("connects_to", []) or []
    if isinstance(connects, str):
        connects = [connects]
    connects = [canonicalize_ref(c, slug_map) for c in connects]
    if connects:
        fm["connects_to"] = connects

    # rebuild file content
    new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False,
                       sort_keys=False).rstrip()
    new_content = f"---\n{new_fm}\n---\n{body}"

    if dry_run:
        print(f"  DRY RUN: {path.name} -> {out_filename}")
        print(f"    id: {fid}, revision: {fm['revision']}")
        if connects:
            print(f"    connects_to: {connects[:3]}{'...' if len(connects) > 3 else ''}")
        return out_filename

    PROCESSED_DIR.mkdir(exist_ok=True)
    out_path.write_text(new_content, encoding="utf-8")
    print(f"  OK: {path.name} -> {out_filename}")
    return out_filename


def main():
    dry_run = "--dry-run" in sys.argv

    # discover incoming field-note-NNN-*.md files
    files = sorted(INCOMING_DIR.glob("field-note-*.md"))
    if not files:
        print("No field-note-*.md files found in incoming/")
        return

    # build slug_map: FN#### -> canonical_filename (for cross-ref canonicalization)
    slug_map: dict[str, str] = {}
    for f in files:
        m = re.match(r"field-note-(\d+)-(.+)\.md$", f.name, re.I)
        if not m:
            continue
        num = int(m.group(1))
        slug = m.group(2).lower()
        slug_map[fn_id(num)] = canonical_filename(num, slug)

    # also add already-processed files to slug_map
    for f in PROCESSED_DIR.glob("FN*.md"):
        m = re.match(r"(FN\d{4})_(.+)\.md$", f.name)
        if m:
            slug_map[m.group(1)] = f.name

    print(f"Processing {len(files)} incoming files{'  (DRY RUN)' if dry_run else ''}...\n")

    results = []
    for f in files:
        m = re.match(r"field-note-(\d+)-(.+)\.md$", f.name, re.I)
        if not m:
            print(f"  SKIP (unexpected name): {f.name}")
            continue
        num = int(m.group(1))
        result = process_file(f, num, slug_map, dry_run=dry_run)
        if result:
            results.append((f, result, num))

    if not dry_run and results:
        print(f"\nProcessed {len(results)} files into processed/")
        print("\nID_REGISTRY.csv entries to add:")
        print("id,slug,current_filename,canonical_filename,status,notes")
        for src, out_name, num in results:
            fid = fn_id(num)
            slug = re.sub(r"^FN\d{4}_", "", out_name).replace(".md", "")
            print(f"{fid},{slug},{src.name},{out_name},processed,")

        print("\nTo remove source files from incoming/ after review:")
        for src, _, _ in results:
            print(f"  rm incoming/{src.name}")


if __name__ == "__main__":
    main()
