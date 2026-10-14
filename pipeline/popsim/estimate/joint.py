"""Exact model-implied joint distributions.

Some estimators need population weights over several model variables at once - e.g. how
many Jewish women aged 30-34 are Haredi *and* born in Africa - to combine survey tables
that condition on different variables. joint() computes such weights exactly from the
frame and the distribution files already written, following the sampler's rules (lookups,
"*" wildcards and back-off), and sums variables out as soon as nothing downstream needs them.
The validation report uses the same function for model-implied totals.
"""

from __future__ import annotations

import pandas as pd

from ..model_spec import Node, load_spec


def _read_table(node: Node) -> pd.DataFrame:
    df = pd.read_csv(node.file, dtype=str, keep_default_na=False)
    df["p"] = df["p"].astype(float)
    return df[df["p"] > 0]


def resolve(cpt: pd.DataFrame, parents: list[str], backoff: list[str], keys: pd.DataFrame, node_id: str = "") -> pd.DataFrame:
    """The CPT rows the sampler uses for each parent combination in `keys`:
    the exact row if present, else the row with the back-off parents set to "*"
    (cumulatively, in order). Returns parents (original values) + value, p."""
    keys = keys[parents].drop_duplicates().reset_index(drop=True)
    probe = keys.copy()
    found = []
    for step in [None, *backoff]:
        if step is not None:
            probe[step] = "*"
        m = probe.reset_index().merge(cpt[parents + ["value", "p"]], on=parents, how="inner")
        if len(m):
            hit = m["index"].unique()
            found.append(m[["index", "value", "p"]].merge(keys, left_on="index", right_index=True).drop(columns=["index"]))
            probe = probe.drop(index=hit)
        if probe.empty:
            break
    if not probe.empty:
        missing = keys.loc[probe.index].head(3).to_dict("records")
        raise ValueError(f"{node_id}: no distribution for {len(probe)} parent combinations, e.g. {missing}")
    return pd.concat(found, ignore_index=True)[parents + ["value", "p"]]


def joint(keep: list[str], where: dict[str, list[str]] | None = None, spec=None) -> pd.DataFrame:
    """Joint distribution (people counts `w`) over the variables in `keep`.

    where: optional filters {variable: allowed value ids}, applied as soon as the variable
    is available (they restrict the population, they are not conditioning weights).
    """
    spec = spec or load_spec()
    where = where or {}
    frame = spec.nodes[0]
    frame_vars = [v.id for v in frame.vars]
    by_id = {n.id: n for n in spec.nodes[1:]}

    # nodes needed: ancestors of keep and of the filtered variables
    needed: set[str] = set()
    stack = [v for v in list(keep) + list(where) if v not in frame_vars]
    while stack:
        v = stack.pop()
        if v in needed:
            continue
        if v not in by_id:
            raise KeyError(f"unknown variable {v!r}")
        needed.add(v)
        stack.extend(p for p in by_id[v].parents if p not in frame_vars)
    order = [n for n in spec.nodes[1:] if n.id in needed]
    for n in order:
        if n.type not in ("table", "lookup"):
            raise ValueError(f"joint(): node type {n.type!r} ({n.id}) is not supported")

    df = pd.read_csv(frame.file, dtype=str, keep_default_na=False)
    df["w"] = df["count"].astype(float)
    df = df.drop(columns=["count"])

    def apply_filters(d: pd.DataFrame) -> pd.DataFrame:
        for var, allowed in where.items():
            if var in d.columns:
                d = d[d[var].isin(allowed)]
        return d

    def live(rest: list[Node]) -> set[str]:
        out = set(keep) | set(where)
        for m in rest:
            out |= set(m.parents)
        return out

    def compact(d: pd.DataFrame, live: set[str]) -> pd.DataFrame:
        cols = [c for c in d.columns if c != "w" and c in live]
        if len(cols) == len(d.columns) - 1:
            return d
        return d.groupby(cols, sort=False, as_index=False)["w"].sum()

    pending = list(order)
    df = compact(apply_filters(df), live(pending))
    while pending:
        # Any node whose parents are known can be evaluated (the DAG order is only a sufficient
        # schedule). Prefer the one that lets the most columns be summed out afterwards (e.g. the
        # helpers of `locality`, so the 1,200 localities do not ride along), then the one that
        # multiplies the table least (lookups first).
        ready = [n for n in pending if all(p in df.columns for p in n.parents)]

        def score(n: Node) -> tuple[int, int, int]:
            after = live([m for m in pending if m is not n])
            freed = sum(1 for c in df.columns if c != "w" and c not in after)
            size = 1 if n.type == "lookup" else max(len(n.values), 2)
            return (-freed, size, order.index(n))

        n = min(ready, key=score)
        pending.remove(n)
        if n.type == "lookup":
            m = pd.read_csv(n.file, dtype=str, keep_default_na=False).rename(columns={"value": n.id})
            df = df.merge(m[[n.parents[0], n.id]], on=n.parents[0], how="left")
            if df[n.id].isna().any():
                raise ValueError(f"{n.id}: lookup has no value for some {n.parents[0]}")
        else:
            cpt = _read_table(n)
            rows = resolve(cpt, n.parents, n.raw.get("backoff", []), df, n.id).rename(columns={"value": n.id})
            df = df.merge(rows, on=n.parents, how="inner")
            df["w"] = df["w"] * df["p"]
            df = df.drop(columns=["p"])
        df = compact(apply_filters(df), live(pending))
    if not keep:
        return pd.DataFrame({"w": [df["w"].sum()]})
    return df.groupby(list(keep), as_index=False)["w"].sum()


def shares(df: pd.DataFrame, by: list[str], col: str = "w") -> pd.Series:
    """Within-group shares of `col`."""
    tot = df.groupby(by)[col].transform("sum")
    return df[col] / tot

