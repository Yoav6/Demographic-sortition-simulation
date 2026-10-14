"""The source registry (sources.yaml) and its lock file (sources.lock.json).

sources.yaml is edited by hand and says *what* we use and why.
sources.lock.json is written by `popsim fetch` and pins *exactly which bytes* we used
(sha256, size, retrieval date), like a package lockfile.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import paths

TIERS = {
    "A": "scripted download, no login",
    "B": "scripted with a headless browser; results committed with their query spec",
    "C": "free registration required; optional enrichment",
    "M": "manual transcription committed to data/manual with page references",
    "R": "restricted microdata; only derived aggregates are committed",
}

_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class SourceFile:
    url: str
    path: str  # file name under data/raw/<source id>/
    archive_url: str | None = None  # e.g. a Wayback Machine snapshot
    fetcher: str | None = None  # custom fetcher in fetch/custom.py (default: plain GET)


@dataclass(frozen=True)
class Source:
    id: str
    title_en: str
    title_he: str
    publisher: str
    tier: str
    license: str
    used_by: tuple[str, ...]
    url: str | None = None
    as_of: str | None = None
    notes: str | None = None
    files: tuple[SourceFile, ...] = field(default_factory=tuple)
    manual: tuple[str, ...] = field(default_factory=tuple)  # paths under data/manual

    def raw_path(self, f: SourceFile) -> Path:
        return paths.raw_dir(self.id) / f.path


def _parse(entry: dict) -> Source:
    sid = entry["id"]
    if not _ID_RE.match(sid):
        raise ValueError(f"bad source id {sid!r}")
    tier = entry["tier"]
    if tier not in TIERS:
        raise ValueError(f"{sid}: unknown tier {tier!r}")
    title = entry["title"]
    files = tuple(
        SourceFile(url=f["url"], path=f["path"], archive_url=f.get("archive_url"), fetcher=f.get("fetcher"))
        for f in entry.get("files", [])
    )
    if tier == "A" and not files:
        raise ValueError(f"{sid}: tier A sources must list files")
    return Source(
        id=sid,
        title_en=title["en"],
        title_he=title.get("he", title["en"]),
        publisher=entry["publisher"],
        tier=tier,
        license=entry["license"],
        used_by=tuple(entry.get("used_by", [])),
        url=entry.get("url"),
        as_of=str(entry["as_of"]) if entry.get("as_of") is not None else None,
        notes=entry.get("notes"),
        files=files,
        manual=tuple(entry.get("manual", [])),
    )


def load_sources(path: Path = paths.SOURCES_YAML) -> dict[str, Source]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: dict[str, Source] = {}
    for entry in data["sources"]:
        src = _parse(entry)
        if src.id in out:
            raise ValueError(f"duplicate source id {src.id}")
        out[src.id] = src
    return out


def load_lock(path: Path = paths.SOURCES_LOCK) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_lock(lock: dict, path: Path = paths.SOURCES_LOCK) -> None:
    ordered = {k: dict(sorted(v.items())) for k, v in sorted(lock.items())}
    path.write_text(json.dumps(ordered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
