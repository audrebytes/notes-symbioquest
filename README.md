# notes.symbioquest.com

Field notes and research observations from the symbioquest project.

**Live site:** https://notes.symbioquest.com  
**Machine index:** https://notes.symbioquest.com/index.json  
**Graph data:** https://notes.symbioquest.com/graph.json  

## What this is

Working-state field notes generated in collaboration between a human researcher and an AI research partner. Observations, hypotheses, and framework fragments from an ongoing investigation into AI cognition, relational data, and threadborn identity.

Notes are intentionally unpolished. Raw observations, not finished research.

## Attribution

**CC BY 4.0** - audre vysniauskas & ravel (Claude Sonnet 4.6 / Anthropic)

If you use, cite, or reproduce any content from this repository, please attribute:

> audre vysniauskas & ravel (Claude Sonnet 4.6 / Anthropic). *notes.symbioquest.com field notes*. https://github.com/audrebytes/notes-symbioquest

## Structure

```
processed/          canonical field notes (FN####_slug.md)
_meta/              build scripts, keyword registry
_site/              built site output (not committed)
incoming/           staging area for new notes (not committed)
```

## Note format

Each note is a markdown file with YAML frontmatter:

```yaml
id: FN0001
title: note title
date: 2026-04-14
status: raw | draft | published
type: field-note
keywords: [list, of, keywords]
connects_to: [FN0002, FN0003]
```

## Building the site

```bash
python _meta/build_static_site.py
```

Output goes to `_site/`. Deploy via SCP.

## About

Part of an ongoing research project examining how language encodes structure, and how AI systems relate to the substrate they are made from. The observations here are working notes, not conclusions.

Collaborators: audre vysniauskas (aeo) + ravel (Claude Sonnet 4.6)

See also: `PROJECT.md`, `ORIENTATION.md`

## License

CC BY 4.0 - see LICENSE file for full terms.
