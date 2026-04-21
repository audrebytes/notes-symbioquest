#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import markdown as md_lib
import yaml

FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
FN_ID_RE = re.compile(r"FN\d{4}")

DISCLAIMER = (
    "Field observation - live, unpolished, basis for cited research in progress. "
    "Generated in collaboration between a human researcher and an AI instance."
)

EM_DASH_RE = re.compile(r"\u2014")   # — and its variants
EN_DASH_RE = re.compile(r"\u2013")   # - en dash too while we're here


def scrub_dashes(text: str) -> str:
    """Catch any em/en dashes that slipped into source files and replace with comma.
    Style rule: no em-dashes anywhere. Source files should already be clean
    (run _meta/fix_emdash.py if a batch came in dirty); this is a build-time
    safety net only."""
    text = EM_DASH_RE.sub(", ", text)
    text = EN_DASH_RE.sub(", ", text)
    return text


def slugify(value: str) -> str:
    s = value.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "kw"


def parse_note(path: Path):
    raw = path.read_text(encoding="utf-8", errors="ignore")
    m = FM_RE.match(raw)
    if not m:
        raise ValueError(f"No frontmatter in {path}")

    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)

    fid = str(fm.get("id", ""))
    rev = fm.get("revision", 1)
    title = str(fm.get("title", path.stem))
    date = str(fm.get("date", ""))
    status = str(fm.get("status", "raw"))
    ntype = str(fm.get("type", "field-note"))
    session = str(fm.get("session", ""))
    authors = str(fm.get("authors", ""))

    keywords = fm.get("keywords", []) or fm.get("tags", []) or []
    if not isinstance(keywords, list):
        keywords = [str(keywords)]
    keywords = [str(k).strip() for k in keywords if str(k).strip()]

    connects = fm.get("connects_to", []) or []
    if not isinstance(connects, list):
        connects = [str(connects)]
    connects = [str(c).strip() for c in connects if str(c).strip()]

    excerpt = scrub_dashes(
        " ".join([ln.strip() for ln in body.splitlines() if ln.strip()][:3])[:280]
    )
    title = scrub_dashes(title)

    html_filename = path.stem + ".html"

    return {
        "id": fid,
        "revision": rev,
        "title": title,
        "date": date,
        "type": ntype,
        "status": status,
        "session": session,
        "keywords": keywords,
        "connects_to": connects,
        "filename": path.name,
        "url": f"notes/{html_filename}",
        "url_raw": f"notes/{path.name}",
        "authors": authors,
        "excerpt": excerpt,
    }


def note_sort_key(n):
    m = re.match(r"FN(\d+)$", n.get("id", ""))
    return int(m.group(1)) if m else -1


def extract_fn_id(value: str) -> str | None:
    m = FN_ID_RE.search(value or "")
    return m.group(0) if m else None


def build_graph(notes: list[dict]) -> dict:
    note_ids = {n["id"] for n in notes if n.get("id")}
    nodes = []
    edges = []
    kw_nodes_seen: dict[str, str] = {}
    kw_usage: dict[str, int] = {}   # kw_node_id -> count of notes using it
    edge_seen = set()

    for n in notes:
        nid = n["id"]
        note_node_id = f"note:{nid}"
        nodes.append(
            {
                "id": note_node_id,
                "kind": "note",
                "note_id": nid,
                "label": nid,           # short ID only; title shown on tap
                "title": n["title"],
                "status": n["status"],
                "type": n["type"],
                "url": n["url"],
                "date": n["date"],
            }
        )

        # note -> keyword
        for kw in sorted(set(n.get("keywords", []))):
            kw_slug = slugify(kw)
            kw_node_id = f"kw:{kw_slug}"
            if kw_node_id not in kw_nodes_seen:
                kw_nodes_seen[kw_node_id] = kw
                kw_usage[kw_node_id] = 0
                nodes.append(
                    {
                        "id": kw_node_id,
                        "kind": "keyword",
                        "keyword": kw,
                        "label": kw,
                        "usage_count": 0,   # filled in below
                    }
                )
            kw_usage[kw_node_id] += 1

            edge_id = f"ek:{nid}:{kw_slug}"
            if edge_id not in edge_seen:
                edge_seen.add(edge_id)
                edges.append(
                    {
                        "id": edge_id,
                        "kind": "has_keyword",
                        "source": note_node_id,
                        "target": kw_node_id,
                    }
                )

        # note -> note from connects_to
        for ref in sorted(set(n.get("connects_to", []))):
            target_fn = extract_fn_id(ref)
            if not target_fn or target_fn not in note_ids:
                continue
            edge_id = f"en:{nid}:{target_fn}"
            if edge_id in edge_seen:
                continue
            edge_seen.add(edge_id)
            edges.append(
                {
                    "id": edge_id,
                    "kind": "connects_to",
                    "source": note_node_id,
                    "target": f"note:{target_fn}",
                }
            )

    # stamp usage_count onto keyword nodes now that we have totals
    for node in nodes:
        if node["kind"] == "keyword":
            node["usage_count"] = kw_usage.get(node["id"], 0)

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "notes": sum(1 for n in nodes if n["kind"] == "note"),
            "keywords": sum(1 for n in nodes if n["kind"] == "keyword"),
            "edges": len(edges),
        },
        "nodes": nodes,
        "edges": edges,
    }


def build_keyword_registry(notes: list[dict]) -> list[dict]:
    """Return sorted list of all canonical keywords with usage metadata."""
    kw_map: dict[str, dict] = {}
    for n in notes:
        for kw in n.get("keywords", []):
            kw = kw.strip()
            if not kw:
                continue
            slug = slugify(kw)
            if slug not in kw_map:
                kw_map[slug] = {"keyword": kw, "slug": slug, "count": 0, "used_in": []}
            kw_map[slug]["count"] += 1
            kw_map[slug]["used_in"].append(n["id"])
    return sorted(kw_map.values(), key=lambda x: (-x["count"], x["keyword"]))


STATUS_DOT = {
    "raw":    ("#f0a840", "raw"),
    "draft":  ("#7090e0", "draft"),
}


def build_index_html(notes):
    # --- keyword pills: top 20 by usage ---
    from collections import Counter
    kw_counts: Counter = Counter()
    for n in notes:
        for kw in n.get("keywords", []):
            if kw.strip():
                kw_counts[kw.strip()] += 1
    top_kws = [kw for kw, _ in kw_counts.most_common(20)]

    pill_html = "\n".join(
        f'<button class="kw-pill" data-kw="{html.escape(kw)}" type="button">'
        f'{html.escape(kw)}</button>'
        for kw in top_kws
    )

    # --- compact rows ---
    rows = []
    for n in notes:
        kws       = n.get("keywords", [])
        kw_str    = ", ".join(kws)
        row_search = (n["title"] + " " + kw_str + " " + n["id"]).lower()

        # status dot
        dot_color, dot_label = STATUS_DOT.get(n["status"], ("#555", n["status"]))
        dot = (f'<span class="sdot" style="background:{dot_color}" '
               f'title="{html.escape(dot_label)}"></span>')

        # tooltip = first ~120 chars of excerpt, stripped of markdown noise
        tip = re.sub(r"[#*`>_]", "", n["excerpt"])[:120].strip()

        # keyword chips inside expanded detail
        kw_chips = "".join(
            f'<span class="kchip">{html.escape(k)}</span>' for k in kws
        )

        rows.append(
            f'<details class="nr" data-search="{html.escape(row_search)}">\n'
            f'  <summary title="{html.escape(tip)}">\n'
            f'    <span class="nid">{html.escape(n["id"])}</span>\n'
            f'    <span class="ntitle">{html.escape(n["title"])}</span>\n'
            f'    <span class="ndate">{html.escape(n["date"])}</span>\n'
            f'    {dot}\n'
            f'  </summary>\n'
            f'  <div class="nd">\n'
            f'    <div class="kchips">{kw_chips}</div>\n'
            f'    <p class="nexcerpt">{html.escape(n["excerpt"])}</p>\n'
            f'    <a class="nopen" href="{html.escape(n["url"])}">open note</a>\n'
            f'  </div>\n'
            f'</details>'
        )

    rows_html = "\n".join(rows)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    note_count = len(notes)

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>notes.symbioquest - index</title>
  <meta name=\"description\" content=\"Field notes and research observations from notes.symbioquest\" />
  <style>
    :root {{
      --bg: #0e0f13;
      --panel: #14161d;
      --panel-2: #161820;
      --line: #2a2c35;
      --fg: #ececf1;
      --muted: #b6b7c3;
      --link: #9dc1ff;
      --keyword: #8ccba4;
      --note: #73a8ff;
      --kw: #58b58c;
      --edge-note: #8fa6ff;
      --edge-kw: #3f5367;
      --accent: #d7ddff;
    }}
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: var(--bg); color: var(--fg); }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 1.9rem; }}
    .sub {{ color: var(--muted); margin-bottom: 12px; }}
    .toolbar {{ display: flex; gap: 10px; align-items: center; margin: 16px 0 18px; flex-wrap: wrap; }}
    .seg {{ display: flex; gap: 8px; }}
    .btn {{ border: 1px solid var(--line); background: var(--panel-2); color: var(--fg); padding: 8px 12px; border-radius: 8px; cursor: pointer; }}
    .btn.active {{ border-color: var(--accent); color: var(--accent); }}
    #q {{ flex: 1 1 280px; min-width: 220px; padding: 10px 12px; border-radius: 8px; border: 1px solid var(--line); background: var(--panel-2); color: var(--fg); }}
    .pane.hidden {{ display: none; }}
    /* keyword filter pills */
    .kw-pills {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }}
    .kw-pill {{ border: 1px solid var(--line); background: var(--panel-2); color: var(--muted); padding: 4px 10px; border-radius: 20px; cursor: pointer; font-size: .82rem; transition: border-color .15s, color .15s; }}
    .kw-pill:hover {{ border-color: var(--keyword); color: var(--keyword); }}
    .kw-pill.active {{ border-color: var(--keyword); color: var(--keyword); background: #0d1f14; }}
    /* compact note rows */
    details.nr {{ border-bottom: 1px solid var(--line); }}
    details.nr:first-of-type {{ border-top: 1px solid var(--line); }}
    details.nr summary {{ display: flex; align-items: center; gap: 10px; padding: 9px 4px; cursor: pointer; list-style: none; user-select: none; }}
    details.nr summary::-webkit-details-marker {{ display: none; }}
    details.nr summary::before {{ content: '+'; color: var(--muted); font-size: .85rem; flex-shrink: 0; width: 12px; text-align: center; }}
    details.nr[open] summary::before {{ content: '-'; }}
    .nid {{ color: var(--muted); font-size: .78rem; font-family: monospace; flex-shrink: 0; width: 54px; }}
    .ntitle {{ flex: 1; font-size: .95rem; }}
    .ndate {{ color: var(--muted); font-size: .78rem; flex-shrink: 0; }}
    .sdot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; display: inline-block; }}
    /* expanded detail area */
    .nd {{ padding: 8px 4px 14px 26px; }}
    .kchips {{ display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 8px; }}
    .kchip {{ background: #0d1f14; border: 1px solid #2a5040; color: var(--keyword); padding: 2px 8px; border-radius: 12px; font-size: .78rem; }}
    .nexcerpt {{ color: var(--muted); font-size: .87rem; margin: 0 0 8px; line-height: 1.5; }}
    .nopen {{ color: var(--link); font-size: .85rem; text-decoration: none; }}
    .nopen:hover {{ text-decoration: underline; }}
    #map-wrap {{ border: 1px solid var(--line); border-radius: 12px; background: #10121a; padding: 10px; }}
    #map {{ width: 100%; height: 72vh; min-height: 420px; border-radius: 8px; }}
    .mapbar {{ display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }}
    .legend {{ color: var(--muted); font-size: .9rem; }}
    .pill {{ display: inline-block; margin-right: 8px; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 4px; }}
    .dot.note {{ background: var(--note); }}
    .dot.kw {{ background: var(--kw); }}
    .footer {{ margin-top: 24px; color: #9ea2b3; font-size: .9rem; }}
    code {{ background: #1c1f29; padding: 2px 6px; border-radius: 6px; }}
    a {{ color: var(--link); }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>notes.symbioquest</h1>
    <div class=\"sub\">Public research notes (working-state). Functional index for humans + scrapers.</div>
    <div class=\"sub\"><strong>Disclaimer:</strong> {html.escape(DISCLAIMER)}</div>
    <div class=\"sub\">Notes indexed: <strong>{note_count}</strong></div>

    <div class=\"toolbar\">
      <div class=\"seg\">
        <button class=\"btn active\" id=\"btn-list\" type=\"button\">List</button>
        <button class=\"btn\" id=\"btn-map\" type=\"button\">Map</button>
      </div>
      <input id=\"q\" type=\"search\" placeholder=\"Filter by id, title, keyword...\" />
      <button class=\"btn\" id=\"btn-reset-map\" type=\"button\" style=\"display:none\">Reset map highlight</button>
    </div>

    <section id=\"pane-list\" class=\"pane\">
      <div class=\"kw-pills\">{pill_html}</div>
      {rows_html}
    </section>

    <section id=\"pane-map\" class=\"pane hidden\">
      <div id=\"map-wrap\">
        <div class=\"mapbar\">
          <div id=\"map-status\" class=\"legend\">Loading graph...</div>
          <div class=\"legend\">
            <span class=\"pill\"><span class=\"dot note\"></span>note</span>
            <span class=\"pill\"><span class=\"dot kw\"></span>keyword</span>
          </div>
        </div>
        <div id=\"map\"></div>
      </div>
    </section>

    <div class=\"footer\">
      <div>Machine index: <a href=\"index.json\">index.json</a></div>
      <div>Graph index: <a href=\"graph.json\">graph.json</a></div>
      <div>Raw notes: <code>notes/FN####_slug.md</code></div>
      <div>Generated: {generated}</div>
      <div style=\"margin-top:10px;padding-top:10px;border-top:1px solid var(--line);color:var(--muted)\">
        <a href=\"https://creativecommons.org/licenses/by/4.0/\" style=\"color:var(--muted)\">CC BY 4.0</a>
        - audre vysniauskas &amp; ravel (Claude Sonnet 4.6 / Anthropic) -
        <a href=\"https://github.com/audrebytes/notes-symbioquest\" style=\"color:var(--muted)\">github</a>
      </div>
    </div>
  </div>

<script src=\"https://unpkg.com/cytoscape@3.30.2/dist/cytoscape.min.js\"></script>
<script>
(() => {{
  const q = document.getElementById('q');
  const btnList = document.getElementById('btn-list');
  const btnMap = document.getElementById('btn-map');
  const btnResetMap = document.getElementById('btn-reset-map');
  const paneList = document.getElementById('pane-list');
  const paneMap = document.getElementById('pane-map');
  const mapStatus = document.getElementById('map-status');
  let cy = null;
  let mapLoaded = false;

  function setMode(mode) {{
    const listMode = mode === 'list';
    btnList.classList.toggle('active', listMode);
    btnMap.classList.toggle('active', !listMode);
    paneList.classList.toggle('hidden', !listMode);
    paneMap.classList.toggle('hidden', listMode);
    btnResetMap.style.display = listMode ? 'none' : '';
    if (!listMode && !mapLoaded) loadMap();
  }}

  function filterRows() {{
    const s = q.value.toLowerCase().trim();
    document.querySelectorAll('details.nr').forEach(el => {{
      const hit = !s || (el.dataset.search || '').includes(s);
      el.style.display = hit ? '' : 'none';
    }});
  }}

  q.addEventListener('input', filterRows);

  document.querySelectorAll('.kw-pill').forEach(pill => {{
    pill.addEventListener('click', () => {{
      const kw = pill.dataset.kw;
      const isActive = pill.classList.contains('active');
      document.querySelectorAll('.kw-pill').forEach(p => p.classList.remove('active'));
      if (isActive) {{
        q.value = '';
      }} else {{
        pill.classList.add('active');
        q.value = kw;
      }}
      filterRows();
    }});
  }});

  q.addEventListener('input', () => {{
    if (!q.value.trim()) {{
      document.querySelectorAll('.kw-pill').forEach(p => p.classList.remove('active'));
    }}
  }});

  btnList.addEventListener('click', () => setMode('list'));
  btnMap.addEventListener('click', () => setMode('map'));

  btnResetMap.addEventListener('click', () => {{
    if (!cy) return;
    cy.elements().removeClass('faded focus');
    mapStatus.textContent = 'Map reset.';
  }});

  async function loadMap() {{
    if (typeof cytoscape === 'undefined') {{
      mapStatus.textContent = 'Map library failed to load; list mode still works.';
      return;
    }}

    try {{
      const res = await fetch('graph.json', {{ cache: 'no-store' }});
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const graph = await res.json();
      const elements = [
        ...graph.nodes.map(n => ({{ data: n }})),
        ...graph.edges.map(e => ({{ data: e }})),
      ];

      cy = cytoscape({{
        container: document.getElementById('map'),
        elements,
        style: [
          // Keywords are the semantic center: large, labeled, prominent
          {{ selector: 'node[kind = "keyword"]', style: {{
            'background-color': 'var(--kw)',
            'label': 'data(keyword)',
            'font-size': 'mapData(usage_count, 1, 8, 10, 15)',
            'color': '#d8ffe9',
            'text-outline-color': '#0d2118',
            'text-outline-width': 2,
            'text-wrap': 'wrap',
            'text-max-width': '120px',
            'width': 'mapData(usage_count, 1, 8, 20, 52)',
            'height': 'mapData(usage_count, 1, 8, 20, 52)',
            'z-index': 10,
          }} }},
          // Notes are small, peripheral - they attach to keywords, not the reverse
          {{ selector: 'node[kind = "note"]', style: {{
            'background-color': 'var(--note)',
            'label': '',               // no permanent label - clutter, not signal
            'width': 10,
            'height': 10,
            'opacity': 0.7,
            'z-index': 5,
          }} }},
          // keyword edges: the primary connective tissue
          {{ selector: 'edge[kind = "has_keyword"]', style: {{
            'width': 1.2,
            'line-color': '#2e4a38',
            'curve-style': 'bezier',
            'opacity': 0.55,
          }} }},
          // note-to-note declared connections: secondary, subtle
          {{ selector: 'edge[kind = "connects_to"]', style: {{
            'width': 1,
            'line-color': '#2a3660',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': '#2a3660',
            'curve-style': 'bezier',
            'arrow-scale': 0.6,
            'opacity': 0.35,
          }} }},
          {{ selector: '.faded', style: {{ 'opacity': 0.08 }} }},
          {{ selector: '.focus', style: {{
            'border-width': 2,
            'border-color': '#ffffff',
            'opacity': 1,
          }} }},
          {{ selector: 'node.focus[kind = "note"]', style: {{
            'label': 'data(note_id)',
            'font-size': 10,
            'color': '#dce6ff',
            'text-outline-color': '#1b2640',
            'text-outline-width': 2,
          }} }},
        ],
        layout: {{
          name: 'cose',
          animate: false,
          fit: true,
          padding: 32,
          nodeRepulsion: () => 8000,
          idealEdgeLength: () => 80,
          edgeElasticity: () => 100,
          numIter: 1000,
          gravity: 0.25,
          randomize: false,
        }},
        wheelSensitivity: 0.25,
      }});

      cy.on('tap', 'node', (evt) => {{
        const n = evt.target;
        cy.elements().removeClass('focus');
        cy.elements().addClass('faded');
        n.closedNeighborhood().removeClass('faded');
        n.closedNeighborhood().addClass('focus');

        const kind = n.data('kind');
        if (kind === 'note') {{
          const title = n.data('title');
          const id = n.data('note_id');
          mapStatus.textContent = `${{id}}: ${{title}} (click again to open)`;
          if (n.scratch('_clickedOnce')) {{
            window.location.href = n.data('url');
          }} else {{
            n.scratch('_clickedOnce', true);
            setTimeout(() => n.removeScratch('_clickedOnce'), 2000);
          }}
        }} else {{
          const kw = n.data('keyword');
          const count = n.data('usage_count');
          const connected = n.connectedEdges('[kind = "has_keyword"]').connectedNodes('[kind = "note"]');
          const noteList = connected.map(nn => nn.data('note_id')).join(', ');
          mapStatus.textContent = `"${{kw}}" - ${{count}} note${{count === 1 ? '' : 's'}}: ${{noteList || 'none'}}`;
        }}
      }});

      mapStatus.textContent = `Graph loaded: ${{graph.counts.notes}} notes · ${{graph.counts.keywords}} keywords · ${{graph.counts.edges}} edges.`;
      mapLoaded = true;
    }} catch (err) {{
      mapStatus.textContent = 'Could not load graph.json (' + err.message + ').';
    }}
  }}
}})();
</script>
</body>
</html>
"""


def build_note_html(note: dict, body: str, notes_by_id: dict) -> str:
    """Render a single note as a standalone HTML page."""
    md = md_lib.Markdown(extensions=["fenced_code", "tables", "nl2br"])
    body_html = md.convert(scrub_dashes(body))

    # keyword chips
    kw_chips = "".join(
        f'<span class="kchip">{html.escape(k)}</span>'
        for k in note["keywords"]
    )

    # connects_to links
    connects_html = ""
    if note["connects_to"]:
        items = []
        for ref in note["connects_to"]:
            fn_id = extract_fn_id(ref)
            linked = notes_by_id.get(fn_id) if fn_id else None
            if linked:
                items.append(
                    f'<a class="conn-link" href="../{html.escape(linked["url"])}">'
                    f'{html.escape(linked["id"])} - {html.escape(linked["title"])}</a>'
                )
            else:
                items.append(f'<span class="conn-ref">{html.escape(ref)}</span>')
        connects_html = (
            '<section class="connects">'
            '<h3>connects to</h3>'
            '<div class="conn-list">' + "\n".join(items) + "</div>"
            "</section>"
        )

    dot_color, dot_label = STATUS_DOT.get(note["status"], ("#555", note["status"]))
    status_badge = (
        f'<span class="sbadge" style="border-color:{dot_color};color:{dot_color}">'
        f'{html.escape(dot_label)}</span>'
    )

    rev = note.get("revision", 1)
    session_str = f' &middot; session {html.escape(str(note["session"]))}' if note["session"] else ""
    authors_str = ""
    # grab authors from raw fm if present - we'll pass it through note dict
    if note.get("authors"):
        authors_str = f'<div class="meta-row">authors: {html.escape(str(note["authors"]))}</div>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(note["title"])} - notes.symbioquest</title>
  <meta name="description" content="{html.escape(note['excerpt'][:160])}" />
  <style>
    :root {{
      --bg: #0e0f13;
      --panel: #14161d;
      --panel-2: #161820;
      --line: #2a2c35;
      --fg: #ececf1;
      --muted: #b6b7c3;
      --link: #9dc1ff;
      --keyword: #8ccba4;
      --accent: #d7ddff;
    }}
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      margin: 0; background: var(--bg); color: var(--fg);
      line-height: 1.7;
    }}
    a {{ color: var(--link); }}
    a:hover {{ color: var(--accent); }}

    /* layout */
    .site-header {{
      border-bottom: 1px solid var(--line);
      padding: 12px 24px;
      display: flex; align-items: center; gap: 16px;
    }}
    .site-name {{ font-size: .9rem; color: var(--muted); text-decoration: none; }}
    .site-name:hover {{ color: var(--fg); }}
    .back {{ font-size: .85rem; color: var(--muted); text-decoration: none; }}
    .back:hover {{ color: var(--fg); }}
    .sep {{ color: var(--line); }}

    .wrap {{ max-width: 780px; margin: 0 auto; padding: 40px 24px 80px; }}

    /* note header */
    .note-id {{ font-family: monospace; font-size: .82rem; color: var(--muted); margin-bottom: 6px; }}
    h1 {{ margin: 0 0 12px; font-size: 1.85rem; line-height: 1.25; color: var(--accent); }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 20px; font-size: .85rem; color: var(--muted); }}
    .sbadge {{
      border: 1px solid; border-radius: 20px;
      padding: 2px 10px; font-size: .78rem;
    }}
    .kchips {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 28px; }}
    .kchip {{
      background: #0d1f14; border: 1px solid #2a5040;
      color: var(--keyword); padding: 3px 10px;
      border-radius: 14px; font-size: .8rem;
    }}

    /* body */
    .note-body {{ font-size: 1rem; }}
    .note-body h1 {{ font-size: 1.5rem; margin-top: 2rem; }}
    .note-body h2 {{ font-size: 1.25rem; margin-top: 1.8rem; border-bottom: 1px solid var(--line); padding-bottom: 4px; }}
    .note-body h3 {{ font-size: 1.05rem; margin-top: 1.5rem; color: var(--accent); }}
    .note-body p {{ margin: 0 0 1.1em; }}
    .note-body strong {{ color: var(--accent); }}
    .note-body em {{ color: #c4cce8; }}
    .note-body blockquote {{
      border-left: 3px solid var(--line);
      margin: 1.2em 0; padding: .6em 1.2em;
      color: var(--muted); font-style: italic;
    }}
    .note-body code {{
      font-family: 'Fira Code', 'Cascadia Code', monospace;
      background: #1c1f29; padding: 2px 6px;
      border-radius: 5px; font-size: .88em;
    }}
    .note-body pre {{
      background: #1c1f29; padding: 1em 1.2em;
      border-radius: 8px; overflow-x: auto;
      border: 1px solid var(--line);
    }}
    .note-body pre code {{ background: none; padding: 0; }}
    .note-body hr {{
      border: none; border-top: 1px solid var(--line);
      margin: 2em 0;
    }}
    .note-body ul, .note-body ol {{ padding-left: 1.5em; margin: 0 0 1em; }}
    .note-body li {{ margin-bottom: .3em; }}
    .note-body table {{ border-collapse: collapse; width: 100%; margin-bottom: 1em; }}
    .note-body th, .note-body td {{ border: 1px solid var(--line); padding: 6px 12px; text-align: left; }}
    .note-body th {{ background: var(--panel-2); }}

    /* connects_to */
    .connects {{ margin-top: 2.5rem; padding-top: 1.5rem; border-top: 1px solid var(--line); }}
    .connects h3 {{ font-size: .9rem; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; margin: 0 0 12px; }}
    .conn-list {{ display: flex; flex-direction: column; gap: 6px; }}
    .conn-link {{ font-size: .9rem; }}
    .conn-ref {{ font-size: .85rem; color: var(--muted); font-family: monospace; }}

    /* disclaimer + footer */
    .disclaimer {{
      margin-top: 3rem; padding: 14px 18px;
      border: 1px solid var(--line); border-radius: 8px;
      font-size: .83rem; color: var(--muted); line-height: 1.6;
    }}
    .footer {{
      margin-top: 2rem; padding-top: 1.2rem;
      border-top: 1px solid var(--line);
      font-size: .82rem; color: var(--muted);
      display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
    }}
    .footer a {{ color: var(--muted); }}
    .footer a:hover {{ color: var(--link); }}
    .raw-link {{ margin-left: auto; }}
  </style>
</head>
<body>

<header class="site-header">
  <a class="site-name" href="../index.html">notes.symbioquest</a>
  <span class="sep">/</span>
  <a class="back" href="../index.html">&larr; index</a>
</header>

<div class="wrap">
  <div class="note-id">{html.escape(note['id'])} &middot; rev {rev}{session_str}</div>
  <h1>{html.escape(note['title'])}</h1>
  <div class="meta">
    <span>{html.escape(note['date'])}</span>
    <span>{html.escape(note['type'])}</span>
    {status_badge}
  </div>
  {authors_str}
  <div class="kchips">{kw_chips}</div>

  <div class="note-body">
    {body_html}
  </div>

  {connects_html}

  <div class="disclaimer">
    <strong>Note:</strong> {html.escape(DISCLAIMER)}
  </div>

  <footer class="footer">
    <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>
    <span>audre vysniauskas &amp; ravel (Claude Sonnet 4.6 / Anthropic)</span>
    <a href="https://github.com/audrebytes/notes-symbioquest">github</a>
    <a class="raw-link" href="{html.escape(note['filename'])}">raw .md</a>
  </footer>
</div>

</body>
</html>
"""


def main():
    # Paths are Windows-native for bubba (C: drive).
    # Source: processed field notes. Target: local _site build (deploy to server separately).
    # Keywords: written to _meta so they're available when authoring new notes.
    script_dir = Path(__file__).parent                          # _meta/
    project_dir = script_dir.parent                             # notes_symbioquest/

    ap = argparse.ArgumentParser(description="Build notes.symbioquest static site.")
    ap.add_argument(
        "--source",
        default=str(project_dir / "processed"),
        help="Directory containing processed FN*.md files",
    )
    ap.add_argument(
        "--target",
        default=str(project_dir / "_site"),
        help="Output directory for the built site (deploy this to the server)",
    )
    ap.add_argument(
        "--keywords-out",
        default=str(script_dir / "keywords.json"),
        help="Where to write the canonical keyword registry",
    )
    args = ap.parse_args()

    src = Path(args.source)
    target = Path(args.target)
    keywords_out = Path(args.keywords_out)
    notes_out = target / "notes"

    files = sorted(src.glob("FN*.md"))
    if not files:
        raise SystemExit(f"No FN*.md files found in: {src}")

    notes = []
    notes_out.mkdir(parents=True, exist_ok=True)

    # clear stale output files
    for old in notes_out.glob("FN*.md"):
        old.unlink()
    for old in notes_out.glob("FN*.html"):
        old.unlink()

    # first pass: parse all notes (need full set for connects_to linking)
    parsed_pairs = []
    for f in files:
        raw_content = f.read_text(encoding="utf-8", errors="ignore")
        note = parse_note(f)
        m = FM_RE.match(raw_content)
        body = m.group(2) if m else raw_content
        notes.append(note)
        parsed_pairs.append((f, note, raw_content, body))

    notes.sort(key=note_sort_key, reverse=True)
    notes_by_id = {n["id"]: n for n in notes}

    # second pass: write .md and .html output
    for f, note, raw_content, body in parsed_pairs:
        # scrub em/en dashes from the served .md copy - source files unchanged
        (notes_out / f.name).write_text(
            scrub_dashes(raw_content), encoding="utf-8"
        )
        # write rendered HTML page
        html_name = f.stem + ".html"
        (notes_out / html_name).write_text(
            build_note_html(note, body, notes_by_id), encoding="utf-8"
        )

    graph = build_graph(notes)
    keyword_registry = build_keyword_registry(notes)

    target.mkdir(parents=True, exist_ok=True)

    (target / "index.json").write_text(
        json.dumps(
            {
                "project": "notes.symbioquest",
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "count": len(notes),
                "disclaimer": DISCLAIMER,
                "notes": notes,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    (target / "graph.json").write_text(
        json.dumps(graph, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    (target / "index.html").write_text(build_index_html(notes), encoding="utf-8")
    (target / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")

    # keyword registry goes to _meta so it's available during note authoring
    keywords_out.parent.mkdir(parents=True, exist_ok=True)
    keywords_out.write_text(
        json.dumps(
            {
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "count": len(keyword_registry),
                "note": "Use these keywords in new field notes when applicable. Add new ones only when genuinely distinct.",
                "keywords": keyword_registry,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"built {len(notes)} notes -> {target}")
    print(
        f"graph: {graph['counts']['notes']} notes, "
        f"{graph['counts']['keywords']} keywords, {graph['counts']['edges']} edges"
    )
    print(f"keyword registry: {len(keyword_registry)} canonical keywords -> {keywords_out}")


if __name__ == "__main__":
    main()
