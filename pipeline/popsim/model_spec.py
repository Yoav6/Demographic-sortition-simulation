"""Reading model/dag.yaml: node definitions, value domains and labels.

dag.yaml is the human-edited description of the model: which nodes exist, their
categories (with Hebrew masculine/feminine and English labels), parents, the file that
holds each node's distribution, sources and documentation. Estimators write the files;
export/bundle.py combines both into the bundle the sampler reads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

from . import paths


@dataclass
class Value:
    id: str
    label: dict  # {en, he, he_f?}
    attrs: dict = field(default_factory=dict)


@dataclass
class Node:
    id: str
    type: str
    label: dict
    raw: dict
    values: list[Value] = field(default_factory=list)
    parents: list[str] = field(default_factory=list)
    vars: list["Node"] = field(default_factory=list)  # frame only

    @property
    def file(self) -> Path | None:
        f = self.raw.get("file")
        return paths.MODEL / f if f else None

    def value_ids(self) -> list[str]:
        return [v.id for v in self.values]

    def index(self) -> dict[str, int]:
        return {v.id: i for i, v in enumerate(self.values)}


def _label(d: dict, ctx: str) -> dict:
    if not isinstance(d, dict) or "en" not in d or "he" not in d:
        raise ValueError(f"{ctx}: label needs at least en and he, got {d!r}")
    extra = set(d) - {"en", "he", "he_f", "en_f"}
    if extra:
        # usually an unquoted comma inside a YAML flow mapping: {en: a, b} parses "b" as a key
        raise ValueError(f"{ctx}: unexpected label keys {sorted(map(str, extra))} (quote labels that contain commas)")
    out = {"en": str(d["en"]), "he": str(d["he"])}
    if d.get("he_f"):
        out["he_f"] = str(d["he_f"])
    if d.get("en_f"):
        out["en_f"] = str(d["en_f"])
    return out


def _load_domain_file(path: Path, ctx: str) -> list[Value]:
    """CSV with columns id, en, he[, he_f] and any attribute columns. A domain file that the
    build has not written yet reads as empty (the step that estimates the node writes it)."""
    if not path.exists():
        return []
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    attrs_cols = [c for c in df.columns if c not in ("id", "en", "he", "he_f", "en_f", "en_source")]
    out = []
    for row in df.itertuples(index=False):
        r = row._asdict()
        label = {"en": r["en"], "he": r["he"]}
        if r.get("he_f"):
            label["he_f"] = r["he_f"]
        if r.get("en_f"):
            label["en_f"] = r["en_f"]
        attrs = {}
        for c in attrs_cols:
            v = r[c]
            if v == "":
                continue
            try:
                attrs[c] = float(v) if "." in v else int(v)
            except ValueError:
                attrs[c] = v
        out.append(Value(id=r["id"], label=label, attrs=attrs))
    if len({v.id for v in out}) != len(out):
        raise ValueError(f"{ctx}: duplicate ids in {path}")
    return out


def _values(d: dict, ctx: str) -> list[Value]:
    if "domain_file" in d:
        return _load_domain_file(paths.MODEL / d["domain_file"], ctx)
    out = []
    for v in d.get("values", []):
        attrs = {}
        for k, a in (v.get("attrs") or {}).items():
            attrs[k] = _label(a, f"{ctx}.{v['id']}.{k}") if isinstance(a, dict) else a
        out.append(Value(id=str(v["id"]), label=_label(v["label"], f"{ctx}.{v['id']}"), attrs=attrs))
    return out


@dataclass
class ModelSpec:
    version: str
    reference_date: str
    population_label: dict
    nodes: list[Node]

    def node(self, node_id: str) -> Node:
        for n in self.nodes:
            if n.id == node_id:
                return n
            for v in n.vars:
                if v.id == node_id:
                    return v
        raise KeyError(node_id)

    def variable_ids(self) -> list[str]:
        out = []
        for n in self.nodes:
            out.extend([v.id for v in n.vars] if n.type == "frame" else [n.id])
        return out


def load_spec(path: Path = paths.DAG_YAML) -> ModelSpec:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    nodes = []
    for d in data["nodes"]:
        ctx = d["id"]
        n = Node(id=d["id"], type=d["type"], label=_label(d["label"], ctx), raw=d)
        if n.type == "frame":
            n.vars = [
                Node(id=v["id"], type="frame_var", label=_label(v["label"], v["id"]), raw=v, values=_values(v, v["id"]))
                for v in d["vars"]
            ]
        else:
            n.values = _values(d, ctx) if ("values" in d or "domain_file" in d) else []
            n.parents = list(d.get("parents", [d["parent"]] if "parent" in d else []))
        nodes.append(n)
    spec = ModelSpec(
        version=str(data["version"]),
        reference_date=str(data["reference_date"]),
        population_label=_label(data["population"]["label"], "population"),
        nodes=nodes,
    )
    _check_order(spec)
    return spec


def _check_order(spec: ModelSpec) -> None:
    seen: set[str] = set()
    for n in spec.nodes:
        for p in n.parents + [n.raw[k] for k in ("cap_by", "floor_by", "subset_of") if n.raw.get(k)]:
            if p not in seen:
                raise ValueError(f"{n.id}: parent {p} must be defined earlier in dag.yaml")
        if n.raw.get("subset_of"):
            outer = spec.node(n.raw["subset_of"])
            if n.type != "multi" or outer.type != "multi" or outer.value_ids() != n.value_ids():
                raise ValueError(f"{n.id}: subset_of needs two multi nodes with the same items, in the same order")
        if n.raw.get("shown_as") and n.raw["shown_as"] not in seen:
            raise ValueError(f"{n.id}: shown_as {n.raw['shown_as']} must be a variable defined earlier")
        bad = [v for v in n.raw.get("not_applicable", []) + n.raw.get("off_scale", []) if v not in n.value_ids()]
        if bad:
            raise ValueError(f"{n.id}: not_applicable lists unknown values {bad}")
        seen.update(v.id for v in n.vars) if n.type == "frame" else seen.add(n.id)
