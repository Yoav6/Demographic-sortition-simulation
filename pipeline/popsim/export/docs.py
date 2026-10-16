"""Documentation generation and checks.

* SOURCES.md is generated entirely from sources.yaml + sources.lock.json.
* Each docs/methodology/<node>.md has hand-written sections plus one generated block
  between the markers below (node summary, parents, categories, sources, validation),
  rewritten by `popsim docs` so the numbers never drift from the model.
* `popsim docs --check` fails if a node lacks a doc, a required section is missing or
  empty, a doc cites an unknown source, or a generated block is out of date.
* Citations are hyperlinks: a bare `src:<id>` in a methodology doc, decision record or
  data/manual README is rewritten to a link to that source's anchor in SOURCES.md (the site
  maps the same link to its Sources page).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .. import paths
from ..model_spec import ModelSpec, Node, load_spec
from ..sources import TIERS, load_lock, load_sources

BEGIN = "<!-- BEGIN GENERATED (popsim docs) -->"
END = "<!-- END GENERATED -->"

REQUIRED_SECTIONS = [
    "Definition",
    "Why these parents",
    "Sources",
    "Preprocessing",
    "Estimation",
    "Calibration",
    "Validation",
    "Limitations",
    "Changelog",
]


def documented_nodes(spec: ModelSpec) -> list[Node]:
    """One doc per frame + every non-frame node (frame variables share the frame doc)."""
    return list(spec.nodes)


def doc_path(node: Node) -> Path:
    return paths.ROOT / node.raw.get("doc", f"docs/methodology/{node.id}.md")


# a citation not yet linked: `src:id` not already the text of a [...](...) link
BARE_CITATION = re.compile(r"(?<!\[)`src:([a-z0-9_]+)`(?!\]\()")


def source_anchor(sid: str) -> str:
    return f"src-{sid}"


def source_href(sid: str, doc: Path) -> str:
    rel = Path(os.path.relpath(paths.ROOT / "SOURCES.md", doc.parent)).as_posix()
    return f"{rel}#{source_anchor(sid)}"


def link_citations(text: str, doc: Path) -> str:
    return BARE_CITATION.sub(lambda m: f"[`src:{m.group(1)}`]({source_href(m.group(1), doc)})", text)


def used_by(spec: ModelSpec | None = None) -> dict[str, list[str]]:
    """Source id -> the model nodes that cite it in dag.yaml."""
    spec = spec or load_spec()
    out: dict[str, list[str]] = {}
    for n in spec.nodes:
        for sid in n.raw.get("sources", []):
            out.setdefault(sid, []).append(n.id)
    return out


def sources_md() -> str:
    srcs = load_sources()
    lock = load_lock()
    uses = used_by()
    lines = [
        "# Sources",
        "",
        "Generated from `sources.yaml` and `sources.lock.json` by `popsim docs`. Do not edit by hand.",
        "",
        "Access tiers: " + "; ".join(f"**{k}** = {v}" for k, v in TIERS.items()) + ".",
        "",
    ]
    for s in srcs.values():
        lines += [f'<a id="{source_anchor(s.id)}"></a>', "", f"## {s.title_en}", "", f"*{s.title_he}*", ""]
        lines.append(f"- **id:** `{s.id}` · **tier:** {s.tier} · **publisher:** {s.publisher}")
        if s.url:
            lines.append(f"- **page:** <{s.url}>")
        if s.as_of:
            lines.append(f"- **data as of:** {s.as_of}")
        lines.append(f"- **terms:** {s.license}")
        if uses.get(s.id):
            lines.append("- **used by:** " + ", ".join(f"`{u}`" for u in uses[s.id]))
        planned = [u for u in s.used_by if u not in uses.get(s.id, [])]
        if planned:
            lines.append("- **planned for:** " + ", ".join(f"`{u}`" for u in planned))
        for f in s.files:
            pin = lock.get(s.id, {}).get(f.path)
            pin_txt = f" — sha256 `{pin['sha256'][:16]}…`, retrieved {pin['retrieved']}" if pin else " — not yet fetched"
            lines.append(f"- file `{f.path}`: <{f.url}>{pin_txt}")
        for m in s.manual:
            lines.append(f"- manual data: `data/manual/{m}`")
        if s.notes:
            lines += ["", " ".join(s.notes.split())]
        lines.append("")
    return "\n".join(lines)


def _validation_block(node_id: str, doc: Path) -> str:
    report = paths.REPORTS / "validation.json"
    if not report.exists():
        return "_No validation run recorded yet (`make validate`)._"
    data = json.loads(report.read_text(encoding="utf-8"))
    checks = [c for c in data.get("checks", []) if node_id in c.get("nodes", [])]
    if not checks:
        return "_No automated validation checks cover this node yet._"
    rows = ["| Check | Target | Max abs. difference¹ | Beyond 2 s.e.² | Tolerance | Status |", "|---|---|---|---|---|---|"]
    for c in checks:
        status = "✅ pass" if c["passed"] else "❌ FAIL"
        excess = f"{c['max_excess']:.4f}" if "max_excess" in c else "—"
        rows.append(f"| {c['name']} | {_cite(c['source'], doc)} | {c['max_abs_error']:.4f} | {excess} | {c['tolerance']} | {status} |")
    rows.append("")
    rows.append(f"Sample: {data.get('sample_size', '?'):,} people, seed {data.get('seed', '?')}, model {data.get('model_version', '?')}. "
                "¹ Survey checks: largest difference in a share, over cells with 30+ respondents; percentile checks: "
                "largest deviation of a tenth of the scale from 10% of people; constraints: share of people violating it; "
                "sampler: largest difference between sampled and table shares (it passes on its Bonferroni-adjusted chi-square p-value). "
                "² Largest difference beyond two standard errors of the survey share (survey checks pass on this column).")
    return "\n".join(rows)


def _cite(sid: str, doc: Path) -> str:
    """A source id as a link to its SOURCES.md entry (validation targets may be other labels)."""
    return f"[`{sid}`]({source_href(sid, doc)})" if sid in load_sources() else f"`{sid}`"


def _node_summary(spec: ModelSpec, node: Node, doc: Path) -> list[str]:
    srcs = load_sources()
    lines = [f"#### `{node.id}` — {node.label['en']} / {node.label['he']}", ""]
    lines.append(f"- **type:** `{node.type}`" + (" · hidden helper" if node.raw.get("hidden") else ""))
    if node.type == "frame":
        for v in node.vars:
            lines.append(f"- **frame variable** `{v.id}` ({v.label['en']}): {len(v.values)} values")
    if node.parents:
        lines.append("- **parents:** " + ", ".join(f"`{p}`" for p in node.parents))
    if node.raw.get("backoff"):
        lines.append("- **back-off order:** " + " → ".join(f"`{p}`" for p in node.raw["backoff"]))
    for k, what in (("cap_by", "capped by"), ("floor_by", "floored by")):
        if node.raw.get(k):
            lines.append(f"- **{what}:** `{node.raw[k]}`")
    if node.file:
        lines.append(f"- **distribution file:** `{node.file.relative_to(paths.ROOT)}`")
    vals = node.values if node.type != "frame" else []
    if vals and len(vals) <= 40:
        lines += ["", "| id | English | עברית (m) | עברית (f) |", "|---|---|---|---|"]
        for v in vals:
            lines.append(f"| `{v.id}` | {v.label['en']} | {v.label['he']} | {v.label.get('he_f', '')} |")
    elif vals:
        lines.append(f"- **categories:** {len(vals)} (see the domain file)")
    if node.raw.get("sources"):
        lines += ["", "Sources: " + "; ".join(
            f"{_cite(sid, doc)} ({srcs[sid].publisher})" if sid in srcs else f"`{sid}` ⚠ unknown" for sid in node.raw["sources"])]
    lines += ["", "Validation:", "", _validation_block(node.id, doc), ""]
    return lines


def generated_block(spec: ModelSpec, nodes: list[Node], doc: Path) -> str:
    """The generated part of a methodology doc: a summary of every node documented in it."""
    lines = [BEGIN, "", "### Model summary (generated)", ""]
    for node in nodes:
        lines += _node_summary(spec, node, doc)
    lines.append(END)
    return "\n".join(lines)


def update_docs(check: bool = False) -> list[str]:
    spec = load_spec()
    problems: list[str] = []
    known = set(load_sources())
    out = paths.ROOT / "SOURCES.md"
    text = sources_md() + "\n"
    if check:
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            problems.append("SOURCES.md is out of date (run `popsim docs`)")
    else:
        out.write_text(text, encoding="utf-8")

    by_doc: dict[Path, list[Node]] = {}
    for node in documented_nodes(spec):
        by_doc.setdefault(doc_path(node), []).append(node)
    for p, nodes in by_doc.items():
        if not p.exists():
            problems.append(f"{', '.join(n.id for n in nodes)}: missing methodology doc {p.relative_to(paths.ROOT)}")
            continue
        doc = p.read_text(encoding="utf-8")
        for sec in REQUIRED_SECTIONS:
            m = re.search(rf"^## {re.escape(sec)}\b.*?$(.*?)(?=^## |\Z|{re.escape(BEGIN)})", doc, flags=re.M | re.S)
            if not m:
                problems.append(f"{p.name}: section '## {sec}' missing")
            elif len(re.sub(r"\s+", " ", m.group(1)).strip()) < 20 and sec != "Validation":
                problems.append(f"{p.name}: section '## {sec}' is empty")
        for node in nodes:
            for sid in node.raw.get("sources", []):
                if sid not in known:
                    problems.append(f"{node.id}: dag.yaml cites unknown source {sid}")
        for sid in re.findall(r"`src:([a-z0-9_]+)`", doc):
            if sid not in known:
                problems.append(f"{p.name}: doc cites unknown source {sid}")
        block = generated_block(spec, nodes, p)
        doc_linked = link_citations(doc, p)
        if BEGIN in doc_linked and END in doc_linked:
            new = doc_linked[: doc_linked.index(BEGIN)] + block + doc_linked[doc_linked.index(END) + len(END) :]
        else:
            new = doc_linked.rstrip() + "\n\n" + block + "\n"
        if new != doc:
            if check:
                problems.append(f"{p.name}: generated block out of date or citations unlinked (run `popsim docs`)")
            else:
                p.write_text(new, encoding="utf-8")

    # other hand-written docs that cite sources: decision records and manual-data notes
    for p in sorted([*(paths.DOCS / "decisions").glob("*.md"), *(paths.ROOT / "data" / "manual").glob("*/README.md")]):
        doc = p.read_text(encoding="utf-8")
        for sid in re.findall(r"`src:([a-z0-9_]+)`", doc):
            if sid not in known:
                problems.append(f"{p.relative_to(paths.ROOT)}: cites unknown source {sid}")
        new = link_citations(doc, p)
        if new != doc:
            if check:
                problems.append(f"{p.relative_to(paths.ROOT)}: citations unlinked (run `popsim docs`)")
            else:
                p.write_text(new, encoding="utf-8")
    return problems
