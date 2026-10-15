"""Compile model/dag.yaml + the estimated files into the sampler bundle (popsim-model/1).

File formats the estimators write (all value columns hold value *ids*):
  frame     CSV  <var ids...>, count
  lookup    CSV  <parent>, value
  table     CSV  <parents...>, value, p        ("*" in a parent column = any value)
  multi     CSV  <parents...>, item, p          (p = inclusion probability)
  logit     JSON {intercept: {value: x}, coef: {parent: {parent value: {value: x}}}}
  interval  CSV  <parent>, lo, hi
  percentile CSV percentile, value              (percentile 0..100)
Probabilities become integer weights scaled to 1e9 so sampling is exact in every language.
Tables, sets and logits also carry their national shares (`marginal`, from
model/marginals.json) for the "How unusual?" score.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .. import paths
from ..model_spec import ModelSpec, Node, Value, load_spec
from ..sources import load_sources

PROB_SCALE = 10**9


def _vals(values: list[Value]) -> list[dict]:
    out = []
    for v in values:
        d = {"id": v.id, "label": v.label}
        if v.attrs:
            d["attrs"] = v.attrs
        out.append(d)
    return out


def _common(n: Node) -> dict:
    d = {"id": n.id, "label": n.label}
    for k in ("doc", "sources", "hidden", "shown_as", "ordered", "off_scale", "quality_scale"):
        if k in n.raw:
            d[k] = n.raw[k]
    return d


def _domain_index(spec: ModelSpec, var: str) -> dict[str, int]:
    return spec.node(var).index()


def _int_weights(p: np.ndarray, ctx: str) -> list[int]:
    p = np.asarray(p, dtype=float)
    if (p < 0).any() or not np.isfinite(p).all():
        raise ValueError(f"{ctx}: negative or non-finite probability")
    s = p.sum()
    if s <= 0:
        raise ValueError(f"{ctx}: probabilities sum to zero")
    return [int(x) for x in np.rint(p / s * PROB_SCALE)]


def _frame(spec: ModelSpec, n: Node) -> dict:
    df = pd.read_csv(n.file, dtype={v.id: str for v in n.vars})
    rows = {}
    for v in n.vars:
        idx = v.index()
        missing = set(df[v.id]) - set(idx)
        if missing:
            raise ValueError(f"frame: unknown {v.id} values {sorted(missing)[:5]}")
        rows[v.id] = [idx[x] for x in df[v.id]]
    weights = [int(round(c)) for c in df["count"]]
    d = _common(n)
    d.update(
        type="frame",
        vars=[
            {"id": v.id, "label": v.label, "values": _vals(v.values), **({"hidden": True} if v.raw.get("hidden") else {})}
            for v in n.vars
        ],
        rows=rows,
        weights=weights,
    )
    return d


def _key(spec: ModelSpec, parents: list[str], row: dict, ctx: str) -> str:
    parts = []
    for p in parents:
        x = str(row[p])
        if x == "*":
            parts.append("*")
        else:
            idx = _domain_index(spec, p)
            if x not in idx:
                raise ValueError(f"{ctx}: unknown {p} value {x!r}")
            parts.append(str(idx[x]))
    return "|".join(parts)


def _table(spec: ModelSpec, n: Node) -> dict:
    df = pd.read_csv(n.file, dtype=str, keep_default_na=False)
    df["p"] = df["p"].astype(float)
    vidx = n.index()
    rows: dict[str, list] = {}
    for key_vals, g in df.groupby(n.parents, sort=False) if n.parents else [((), df)]:
        key_vals = key_vals if isinstance(key_vals, tuple) else (key_vals,)
        key = _key(spec, n.parents, dict(zip(n.parents, key_vals)), n.id)
        g = g[g["p"] > 0]
        unknown = set(g["value"]) - set(vidx)
        if unknown:
            raise ValueError(f"{n.id}: unknown values {sorted(unknown)[:5]}")
        order = sorted(g.itertuples(index=False), key=lambda r: vidx[r.value])
        idxs = [vidx[r.value] for r in order]
        w = _int_weights(np.array([r.p for r in order]), f"{n.id}[{key}]")
        keep = [(i, x) for i, x in zip(idxs, w) if x > 0]
        rows[key] = [[i for i, _ in keep], [x for _, x in keep]]
    d = _common(n)
    d.update(type="table", parents=n.parents, values=_vals(n.values), rows=rows)
    if n.raw.get("numeric"):
        d["numeric"] = True
    if n.raw.get("backoff"):
        d["backoff"] = n.raw["backoff"]
    return d


def _multi(spec: ModelSpec, n: Node) -> dict:
    df = pd.read_csv(n.file, dtype=str, keep_default_na=False)
    df["p"] = df["p"].astype(float)
    items = n.index()
    rows = {}
    for key_vals, g in df.groupby(n.parents, sort=False):
        key_vals = key_vals if isinstance(key_vals, tuple) else (key_vals,)
        key = _key(spec, n.parents, dict(zip(n.parents, key_vals)), n.id)
        probs = [0] * len(items)
        for r in g.itertuples(index=False):
            probs[items[r.item]] = int(round(min(max(r.p, 0.0), 1.0) * PROB_SCALE))
        rows[key] = probs
    d = _common(n)
    d.update(type="multi", parents=n.parents, items=_vals(n.values), rows=rows)
    if n.raw.get("backoff"):
        d["backoff"] = n.raw["backoff"]
    if n.raw.get("subset_of"):
        d["subset_of"] = n.raw["subset_of"]
    return d


def _lookup(spec: ModelSpec, n: Node) -> dict:
    parent = n.parents[0]
    df = pd.read_csv(n.file, dtype=str, keep_default_na=False)
    pidx = _domain_index(spec, parent)
    vidx = n.index()
    mapping = dict(zip(df[parent], df["value"]))
    pvals = spec.node(parent).value_ids()
    missing = [p for p in pvals if p not in mapping]
    if missing:
        raise ValueError(f"{n.id}: no value for {parent} {missing[:5]}")
    d = _common(n)
    d.update(type="lookup", parent=parent, values=_vals(n.values), map=[vidx[mapping[p]] for p in pvals])
    assert len(d["map"]) == len(pidx)
    return d


def _logit(spec: ModelSpec, n: Node) -> dict:
    raw = json.loads(n.file.read_text(encoding="utf-8"))
    vids = n.value_ids()
    d = _common(n)
    coef = {}
    for p, table in raw.get("coef", {}).items():
        pvals = spec.node(p).value_ids()
        coef[p] = [[float(table.get(pv, {}).get(v, 0.0)) for v in vids] for pv in pvals]
    d.update(
        type="logit",
        parents=n.parents,
        values=_vals(n.values),
        intercept=[float(raw["intercept"].get(v, 0.0)) for v in vids],
        coef=coef,
    )
    return d


def _interval(spec: ModelSpec, n: Node) -> dict:
    """Empty lo = not applicable for that parent value (NaN); empty hi = open-ended (Pareto tail)."""
    parent = n.parents[0]
    df = pd.read_csv(n.file, dtype=str, keep_default_na=False)
    pvals = spec.node(parent).value_ids()
    lookup = {}
    for r in df.to_dict("records"):
        lookup[r[parent]] = None if r["lo"] == "" else [float(r["lo"]), None if r["hi"] == "" else float(r["hi"])]
    missing = [p for p in pvals if p not in lookup]
    if missing:
        raise ValueError(f"{n.id}: no interval for {parent} {missing[:5]}")
    if any(iv and iv[1] is None for iv in lookup.values()) and "tail_alpha" not in n.raw:
        raise ValueError(f"{n.id}: open-ended interval needs tail_alpha in dag.yaml")
    d = _common(n)
    d.update(type="interval", parent=parent, intervals=[lookup[p] for p in pvals], scale=n.raw.get("scale", "linear"))
    for k in ("round", "tail_alpha", "tail_u_max"):
        if n.raw.get(k) is not None:
            d[k] = n.raw[k]
    if n.raw.get("cap_by"):
        # upper bound per value of a bracket variable = the top of that bracket's own interval
        cap_var = n.raw["cap_by"]
        cap_node = next(m for m in spec.nodes if m.type == "interval" and m.parents[0] == cap_var)
        cap = pd.read_csv(cap_node.file, dtype=str, keep_default_na=False).set_index(cap_var)
        upper = []
        for v in spec.node(cap_var).value_ids():
            hi = cap.loc[v, "hi"] if v in cap.index else ""
            upper.append(None if hi == "" else float(hi))
        d["cap"] = {"var": cap_var, "upper": upper}
    if n.raw.get("floor_by"):
        d["floor"] = n.raw["floor_by"]
    return d


def _percentile(spec: ModelSpec, n: Node) -> dict:
    df = pd.read_csv(n.file).sort_values("percentile")
    d = _common(n)
    d.update(type="percentile", parent=n.parents[0], breakpoints=[float(x) for x in df["value"]])
    return d


BUILDERS = {
    "frame": _frame,
    "table": _table,
    "multi": _multi,
    "lookup": _lookup,
    "logit": _logit,
    "interval": _interval,
    "percentile": _percentile,
}


def _add_marginals(spec: ModelSpec, nodes: list[dict]) -> None:
    """National shares per value (per item for sets), aligned with the node's domain."""
    from ..estimate.marginals import OUT, WEIGHTS, explained, targets

    if not OUT.exists():
        raise FileNotFoundError(f"{OUT.relative_to(paths.ROOT)} is missing (run `popsim build marginals`)")
    marginals = json.loads(OUT.read_text(encoding="utf-8"))
    by_id = {d["id"]: d for d in nodes}
    for n in targets(spec):
        m = marginals.get(n.id)
        if m is None or set(m) != set(n.value_ids()):
            raise ValueError(f"{n.id}: model/marginals.json is out of date (run `popsim build marginals`)")
        by_id[n.id]["marginal"] = [m[v] for v in n.value_ids()]
        if n.raw.get("not_applicable"):
            by_id[n.id]["not_applicable"] = list(n.raw["not_applicable"])
    # people per parent combination: flattened parent value indices (in `parents` order) and weights
    for n in explained(spec):
        f = WEIGHTS / f"{n.id}.csv"
        if not f.exists():
            raise FileNotFoundError(f"{f.relative_to(paths.ROOT)} is missing (run `popsim build marginals`)")
        df = pd.read_csv(f, dtype=str, keep_default_na=False)
        if list(df.columns) != list(n.parents) + ["w"]:
            raise ValueError(f"{n.id}: {f.name} is out of date (run `popsim build marginals`)")
        flat: list[int] = []
        for p in n.parents:
            idx = _domain_index(spec, p)
            df[p] = df[p].map(idx)
            if df[p].isna().any():
                raise ValueError(f"{n.id}: {f.name} has unknown {p} values (run `popsim build marginals`)")
        flat = df[n.parents].astype(int).to_numpy().ravel().tolist()
        by_id[n.id]["parent_weights"] = {"v": flat, "w": [float(x) for x in df["w"]]}


def build_bundle(spec: ModelSpec | None = None) -> dict:
    spec = spec or load_spec()
    nodes = [BUILDERS[n.type](spec, n) for n in spec.nodes]
    _add_marginals(spec, nodes)
    frame = nodes[0]
    srcs = load_sources()
    used = sorted({s for n in nodes for s in n.get("sources", [])})
    unknown = [s for s in used if s not in srcs]
    if unknown:
        raise ValueError(f"unknown source ids in dag.yaml: {unknown}")
    return {
        "format": "popsim-model/1",
        "version": spec.version,
        "reference_date": spec.reference_date,
        "population_label": spec.population_label,
        "population_total": int(sum(frame["weights"])),
        "nodes": nodes,
        "sources": [
            {
                "id": s,
                "title": {"en": srcs[s].title_en, "he": srcs[s].title_he},
                "publisher": srcs[s].publisher,
                "url": srcs[s].url or (srcs[s].files[0].url if srcs[s].files else None),
                "tier": srcs[s].tier,
            }
            for s in used
        ],
    }


def bundle_text() -> tuple[str, str]:
    """The compiled bundle (canonical JSON) and its SHA-256."""
    text = json.dumps(build_bundle(), ensure_ascii=False, separators=(",", ":")) + "\n"
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_bundle() -> tuple[bool, str, str]:
    """Rebuild the bundle from model/ and compare its hash with the committed model.sha256."""
    _, digest = bundle_text()
    recorded = (paths.BUILD / "model.sha256").read_text(encoding="utf-8").split()[0]
    return digest == recorded, digest, recorded


def write_bundle(out: Path | None = None) -> Path:
    text, digest = bundle_text()
    bundle = json.loads(text)
    out = out or paths.BUILD / "model.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    (out.parent / "model.sha256").write_text(f"{digest}  {out.name}\n")
    versioned = out.parent / f"model-{bundle['version']}.json"
    versioned.write_text(text, encoding="utf-8")
    write_sources_json(out.parent / "sources.json")
    return out


def write_sources_json(path: Path) -> None:
    """All registered sources with their pinned files, for the website's Sources page."""
    from ..sources import load_lock

    from .docs import used_by

    lock = load_lock()
    uses = used_by()
    out = []
    for s in load_sources().values():
        out.append(
            {
                "id": s.id,
                "title": {"en": s.title_en, "he": s.title_he},
                "publisher": s.publisher,
                "tier": s.tier,
                "url": s.url,
                "license": s.license,
                "as_of": s.as_of,
                "used_by": uses.get(s.id, []),
                "planned_for": [u for u in s.used_by if u not in uses.get(s.id, [])],
                "notes": " ".join(s.notes.split()) if s.notes else None,
                "files": [
                    {"path": f.path, "url": f.url, **{k: v for k, v in lock.get(s.id, {}).get(f.path, {}).items() if k in ("sha256", "retrieved")}}
                    for f in s.files
                ],
            }
        )
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
