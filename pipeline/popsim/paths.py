"""Repository paths used across the pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SOURCES_YAML = ROOT / "sources.yaml"
SOURCES_LOCK = ROOT / "sources.lock.json"

DATA = ROOT / "data"
RAW = DATA / "raw"
MANUAL = DATA / "manual"
INTERIM = DATA / "interim"

MODEL = ROOT / "model"
DAG_YAML = MODEL / "dag.yaml"
CPTS = MODEL / "cpts"
BUILD = MODEL / "build"

DOCS = ROOT / "docs"
METHODOLOGY_DOCS = DOCS / "methodology"
REPORTS = ROOT / "reports"


def raw_dir(source_id: str) -> Path:
    return RAW / source_id


def interim_path(table: str) -> Path:
    return INTERIM / f"{table}.csv"
