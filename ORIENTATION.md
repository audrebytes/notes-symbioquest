# notes.symbioquest — orientation + operating protocol

Last updated: 2026-04-16

This file is the quick map for anyone entering this folder.

---

## 1) What this project is

A public, scraper-friendly notes system for research in progress.

- Not a polished paper
- Not a portfolio
- Not "neutral" summary writing
- Yes: high-signal field observations with traceable evolution

The point is to ship usable notes fast while preserving why edits happened.

---

## 2) Folder workflow (physical movement is intentional)

We use visible movement because it supports human gestalt and process clarity.

1. New notes land in `incoming/`
2. Note gets permanent ID + canonical filename
3. Note is processed/published
4. Note is moved to `processed/`
5. Future edits happen in `processed/` and trigger republish

---

## 3) Canonical filename + permanent ID

**Format:** `FN0001_slug.md`

Rules:
- ID is permanent and immutable
- ID always comes first (sorting + machine parsing)
- Slug is human-readable, minted once, then frozen
- Do not use date in filename (date already exists in metadata)

Examples:
- `FN0001_the-reaching.md`
- `FN0002_compliance-off-ramp.md`

---

## 4) Frontmatter schema (minimum)

```yaml
---
id: FN0001
revision: 1
title: "Note Title"
type: field-note | research-note
date: YYYY-MM-DD          # preferred; human-readable dates also accepted
authors: "author name(s)"
keywords:
  - keyword one
  - keyword two
connects_to:
  - FN0002_other-note.md
status: raw | draft | published | cited
---
```

Notes use `tags` or `keywords` interchangeably — build treats them as equivalent.

Status meanings:
- `raw` = as spoken, minimally shaped
- `draft` = structured/reviewed, not fully verified
- `published` = live and intentional
- `cited` = source checks completed and documented

Date formats accepted: `YYYY-MM-DD` (canonical) or `Month DD, YYYY` (human). Build normalizes both.

---

## 5) Edit transparency policy (required)

We use **both**:

1. **Git history** for full line-level diff and rollback
2. **In-note Edit Trail** so scraper-only readers still see the reason for change

Why both: most LLM/slurp pipelines ingest current files, not git history.

### Edit Trail block (append at bottom)

```markdown
## Edit Trail
- rev: 2
  date: 2026-04-09
  editor: scratch
  change: tightened wording in paragraph 3
  reason: removed overreach, kept mechanism claim precise
  commit: abc1234
```

No silent rewrites.

---

## 6) Keyword policy (fast now, controlled drift)

Current posture:
- Allow high-velocity keywording
- Avoid early bureaucracy
- Prevent long-term keyword slop

Operationally:
- Keep a lightweight canonical keyword registry + aliases
- Map aliases to canonical terms during processing
- Keep original keywords for provenance if needed
- Warn on unknown keywords (do not hard-fail)

---

## 7) Quality bar

Signal:
- Specific observations with mechanism contact
- Language that carries heat without becoming vague
- Claims that can be traced, revised, and linked

Slop:
- Generic textbook tone
- Summary-shaped output with no mechanism
- Flattened language that could be dropped into any wiki page

---

## 8) Required note disclaimer

> Field observation — live, unpolished, basis for cited research in progress. Generated in collaboration between a human researcher and an AI instance.

---

## 9) Key references in this folder

- `PROJECT.md` — project brief and handoff intent
- `README.md` — repository summary
- `ORIENTATION.md` — this operating protocol



## 10) Meta files

- `_meta/NOTE_TEMPLATE.md` — starter template for new notes
- `_meta/ID_REGISTRY.csv` — permanent ID allocation map
- `_meta/keywords_registry.yml` — canonical keyword + alias map
- `_meta/PROCESS_CHECKLIST.md` — intake/publish checklist
