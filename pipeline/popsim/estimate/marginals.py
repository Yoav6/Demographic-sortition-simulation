"""National marginals of the model's variables, for the "How unusual?" score.

The score (docs/methodology/unusual.md) compares the probability of each of a person's values
given their other traits with its national share. This step computes those shares exactly
from the frame and the distribution files, and writes model/marginals.json:

    {node id: {value or item id: share}}

Tables: P(value). Set-valued nodes: P(item included); for a set nested in another
(`subset_of`), P(item included | item in the enclosing set). Numeric nodes are skipped.
Hidden helpers are included: the score does not judge them, but uses their shares to tell
which of a person's traits made a value unlikely.

Most nodes use joint() directly. The media nodes all sit on the same base (political-news
frequency, vote, age, sector, sex, education, internet use), so that joint is computed once
and the media tables, sets and the preferred-source logit are evaluated on it; the seven
media frequencies are independent given the base, which lets the logit be averaged exactly
over their combinations.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .. import paths
from ..model_spec import ModelSpec, Node, load_spec
from .joint import _read_table, joint, resolve

OUT = paths.MODEL / "marginals.json"
# population per combination of a scored node's parents (<node>.csv: parents..., w), so the
# score's explanations can compare a value's probability across realistic reference groups
WEIGHTS = paths.MODEL / "parent_weights"

# the shared base of the media nodes (plus vote_2022 and news_frequency, whose own marginals
# are read off it)
BASE = ["vote_2022", "news_frequency", "media_age", "media_sector", "sex", "vote_education", "online"]


def targets(spec: ModelSpec) -> list[Node]:
    return [
        n
        for n in spec.nodes[1:]
        if n.type in ("table", "multi", "logit") and not n.raw.get("numeric")
    ]


def _read_multi(n: Node) -> pd.DataFrame:
    df = pd.read_csv(n.file, dtype=str, keep_default_na=False)
    df["p"] = df["p"].astype(float)
    return df.rename(columns={"item": "value"})


def _rows(n: Node, keys: pd.DataFrame) -> pd.DataFrame:
    """The distribution rows the sampler uses for each parent combination in keys."""
    cpt = _read_multi(n) if n.type == "multi" else _read_table(n)
    return resolve(cpt, n.parents, n.raw.get("backoff", []), keys, n.id)


def _table_shares(n: Node, df: pd.DataFrame) -> dict[str, float]:
    m = df.merge(_rows(n, df), on=n.parents, how="inner")
    m["w"] = m["w"] * m["p"]
    s = m.groupby("value")["w"].sum()
    return {v: float(s.get(v, 0.0) / s.sum()) for v in n.value_ids()}


def _multi_shares(n: Node, df: pd.DataFrame) -> dict[str, float]:
    m = df.merge(_rows(n, df), on=n.parents, how="inner")
    total = df["w"].sum()
    s = (m["w"] * m["p"]).groupby(m["value"]).sum()
    return {v: float(s.get(v, 0.0) / total) for v in n.value_ids()}


def _nested_shares(n: Node, outer: Node, df: pd.DataFrame) -> dict[str, float]:
    """P(item in n | item in outer); df holds the parents of both."""
    a = _rows(outer, df).rename(columns={"p": "p_outer"})
    b = _rows(n, df).rename(columns={"p": "p_inner"})
    m = df.merge(a, on=outer.parents, how="inner").merge(b, on=n.parents + ["value"], how="left")
    m["p_inner"] = m["p_inner"].fillna(0.0)
    has = (m["w"] * m["p_outer"]).groupby(m["value"]).sum()
    both = (m["w"] * m["p_outer"] * m["p_inner"]).groupby(m["value"]).sum()
    return {v: float(both.get(v, 0.0) / has[v]) if has.get(v, 0.0) > 0 else 0.0 for v in n.value_ids()}


def _with_lookups(spec: ModelSpec, df: pd.DataFrame) -> pd.DataFrame:
    """Adds every lookup whose parent is a column of df (e.g. vote_bloc from vote_2022)."""
    for n in spec.nodes[1:]:
        if n.type == "lookup" and n.parents[0] in df.columns and n.id not in df.columns:
            m = pd.read_csv(n.file, dtype=str, keep_default_na=False).rename(columns={"value": n.id})
            df = df.merge(m[[n.parents[0], n.id]], on=n.parents[0], how="left")
    return df


def _extend(df: pd.DataFrame, n: Node, keep: list[str]) -> pd.DataFrame:
    """Joint counts over `keep` after adding table node n (its parents are columns of df)."""
    m = df.merge(_rows(n, df).rename(columns={"value": n.id}), on=n.parents, how="inner")
    m["w"] = m["w"] * m["p"]
    return m.groupby(keep, as_index=False)["w"].sum()


def _logit_shares(spec: ModelSpec, n: Node, base: pd.DataFrame) -> dict[str, float]:
    """Exact average of the logit's probabilities. Parents outside the base must be tables whose
    own parents are in the base: given a base row they are independent, so the average over
    their combinations is a product of their distributions."""
    raw = json.loads(n.file.read_text(encoding="utf-8"))
    vids = n.value_ids()
    k = len(vids)
    extra = [spec.node(p) for p in n.parents if p not in base.columns]
    for e in extra:
        if e.type != "table" or not set(e.parents) <= set(base.columns):
            raise ValueError(f"{n.id}: parent {e.id} must be a table on the media base")
    ctx = sorted({p for p in n.parents if p in base.columns} | {p for e in extra for p in e.parents})
    rows = base.groupby(ctx, as_index=False)["w"].sum()

    def coef(parent: str, value: str) -> np.ndarray:
        t = raw.get("coef", {}).get(parent, {}).get(value, {})
        return np.array([float(t.get(v, 0.0)) for v in vids])

    intercept = np.array([float(raw["intercept"].get(v, 0.0)) for v in vids])
    dists = []  # per extra parent: DataFrame ctx + value, p
    for e in extra:
        dists.append(_rows(e, rows))
    # per extra parent and value: the coefficient vector
    coefs = [{v: coef(e.id, v) for v in e.value_ids()} for e in extra]

    acc = np.zeros(k)
    for r in rows.itertuples(index=False):
        rd = r._asdict()
        score = intercept.copy()
        for p in n.parents:
            if p in base.columns:
                score = score + coef(p, rd[p])
        probs, scores = [], []
        for e, d, c in zip(extra, dists, coefs):
            sel = d
            for p in e.parents:
                sel = sel[sel[p] == rd[p]]
            probs.append(sel["p"].to_numpy())
            scores.append(np.stack([c[v] for v in sel["value"]]))
        # broadcast: total score over the product of the extra parents' values
        dims = len(extra)
        s = score.reshape((1,) * dims + (k,))
        w = np.ones((1,) * dims)
        for i, (pv, sv) in enumerate(zip(probs, scores)):
            shape = [1] * dims
            shape[i] = len(pv)
            w = w * pv.reshape(shape)
            s = s + sv.reshape(shape + [k])
        s = s - s.max(axis=-1, keepdims=True)
        e_ = np.exp(s)
        sm = e_ / e_.sum(axis=-1, keepdims=True)
        acc += rd["w"] * (sm * w[..., None]).reshape(-1, k).sum(axis=0)
    acc /= acc.sum()
    return {v: float(x) for v, x in zip(vids, acc)}


def _on_base(spec: ModelSpec, base: pd.DataFrame, need: list[str]) -> pd.DataFrame | None:
    """Joint counts over `need` built on the media base, or None if `need` is not reachable from
    it (every variable must be a base column or a table whose parents are base columns)."""
    extras = [p for p in need if p not in base.columns]
    if any(spec.node(p).type != "table" or not set(spec.node(p).parents) <= set(base.columns) for p in extras):
        return None
    df = base
    for i, p in enumerate(extras):
        later = set().union(*[set(spec.node(q).parents) for q in extras[i + 1 :]])
        keep = sorted((set(need) | later) & (set(df.columns) | {p}) - {"w"})
        df = _extend(df, spec.node(p), keep)
    return df.groupby(need, as_index=False)["w"].sum()


def compute(spec: ModelSpec | None = None, log=print) -> dict[str, dict[str, float]]:
    spec = spec or load_spec()
    base = _with_lookups(spec, joint(BASE, spec=spec))
    out: dict[str, dict[str, float]] = {}
    for n in targets(spec):
        outer = spec.node(n.raw["subset_of"]) if n.raw.get("subset_of") else None
        need = sorted(set(n.parents) | (set(outer.parents) if outer else set()))
        if n.id in base.columns:
            s = base.groupby(n.id)["w"].sum()
            out[n.id] = {v: float(s.get(v, 0.0) / s.sum()) for v in n.value_ids()}
        elif n.type == "logit":
            out[n.id] = _logit_shares(spec, n, base)
        elif (df := _on_base(spec, base, need)) is not None:
            if outer:
                out[n.id] = _nested_shares(n, outer, df)
            else:
                out[n.id] = _multi_shares(n, df) if n.type == "multi" else _table_shares(n, df)
        elif outer:
            out[n.id] = _nested_shares(n, outer, joint(need, spec=spec))
        elif n.type == "table":
            s = joint([n.id], spec=spec).set_index(n.id)["w"]
            out[n.id] = {v: float(s.get(v, 0.0) / s.sum()) for v in n.value_ids()}
        else:
            out[n.id] = _multi_shares(n, joint(n.parents, spec=spec))
        log(f"  {n.id}")
    return out


def explained(spec: ModelSpec) -> list[Node]:
    """Nodes whose surprises are explained with reference groups: the scored tables and sets.
    (The preferred-source logit has too many parent combinations; the first name is not scored.)"""
    return [n for n in targets(spec) if not n.raw.get("hidden") and n.type != "logit" and n.id != "first_name"]


def parent_weights(spec: ModelSpec | None = None, log=print) -> dict[str, pd.DataFrame]:
    """People per combination of each explained node's parents (combinations with nobody are
    left out)."""
    spec = spec or load_spec()
    base = _with_lookups(spec, joint(BASE, spec=spec))
    out = {}
    for n in explained(spec):
        df = _on_base(spec, base, list(n.parents))
        if df is None:
            df = joint(list(n.parents), spec=spec)
        df = df[df["w"] > 0].sort_values(list(n.parents)).reset_index(drop=True)
        out[n.id] = df[list(n.parents) + ["w"]]
        log(f"  weights {n.id}: {len(df)} combinations")
    return out


def build(log=print) -> None:
    out = {k: {v: float(f"{x:.6g}") for v, x in d.items()} for k, d in compute(log=log).items()}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    WEIGHTS.mkdir(exist_ok=True)
    for old in WEIGHTS.glob("*.csv"):
        old.unlink()
    for node_id, df in parent_weights(log=log).items():
        df = df.copy()
        df["w"] = df["w"].map(lambda x: f"{x:.4g}")
        df.to_csv(WEIGHTS / f"{node_id}.csv", index=False)
