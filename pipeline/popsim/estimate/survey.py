"""Loading CBS Social Survey generator tables and turning them into smoothed conditionals.

Generator tables (data/manual/cbs_ss/<id>.csv) hold weighted counts and relative standard
errors (RSE) per cell. Survey cells can be thin (e.g. Haredi men aged 75+), so conditional
distributions are estimated hierarchically: each row is shrunk toward the same distribution
computed on fewer parents,

    P(t | row) = (n_eff * share(t | row) + k * P(t | parent row)) / (n_eff + k)

where n_eff is the row's effective sample size, estimated from the cells' RSEs. The generator
reports the RSE of each cell's weighted *count*; for a cell that is a small part of the whole
survey, RSE^2 ~ 1 / n_cell (n_cell = respondents in the cell, design effect included), so
n_eff(row) = sum over its cells of 1 / RSE^2.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from .. import paths
from .common import AGE_BAND_IDS, ipf

SS_DIR = paths.MANUAL / "cbs_ss"

# survey variable id -> our column name
VARS = {
    571: "sex",
    577: "age_s",
    1629: "religion",
    6752: "popgroup",
    1694: "religiosity",
    1649: "religiosity_a",
    101: "marital",
    1599: "children",
    1567: "had_children",
    519: "hh_type",
    491: "with_partner",
    1881: "diploma",
    2031: "idf",
    2054: "national_service",
    6808: "employment",
    4124: "occupation",
    4097: "industry",
    4251: "work_status",
    4385: "hours",
    3115: "income",
    3177: "hh_income",
    6876: "owns_home",
    1350: "health",
    1376: "chronic",
    7000: "disability",
    2169: "internet",
    2341: "social_networks",
    1831: "study",
    1905: "field",
    2: "birth_continent",
}

CODES = {
    "sex": {"1": "male", "2": "female"},
    "age_s": {str(i): a for i, a in enumerate(["20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65-74", "75+"], start=1)},
    "religion": {"1": "jewish", "2": "muslim", "3": "christian", "4": "druze", "5": "other_religion", "6": "no_religion"},
    "popgroup": {"1": "jews_and_others", "2": "arabs"},
    "religiosity": {"1": "haredi", "2": "dati", "3": "masorti_dati", "4": "masorti", "5": "hiloni"},
    "religiosity_a": {"1": "very_religious", "2": "religious", "3": "not_so_religious", "4": "not_religious"},
    "marital": {"1": "married", "2": "married", "3": "divorced", "4": "widowed", "5": "never_married"},
    "children": {str(i): str(i) for i in range(8)},
    "had_children": {"1": "yes", "2": "no"},
    # household = people sharing a dwelling and a food budget (flatmates who buy food separately
    # are separate one-person households)
    "hh_type": {"1": "one_person", "2": "non_family", "3": "one_family", "4": "family_and_others"},
    "with_partner": {"1": "yes", "2": "no"},
    "diploma": {"0": "no_diploma", "9": "no_diploma", "1": "primary", "2": "secondary", "3": "bagrut", "4": "post_secondary", "5": "ba", "6": "ma", "7": "phd", "8": "other_diploma"},
    "idf": {"1": "yes", "2": "no"},
    "national_service": {"1": "yes", "2": "no"},
    "employment": {"1": "employed", "2": "unemployed", "3": "not_in_labour_force"},
    "occupation": {"1": "managers", "2": "professionals", "3": "technicians", "4": "clerical", "5": "sales_services", "6": "skilled_workers", "9": "unskilled"},
    "industry": {
        "1": "agriculture", "3": "manufacturing", "4": "utilities", "5": "utilities", "6": "construction", "7": "trade",
        "8": "transport", "9": "hospitality", "10": "ict", "11": "finance", "12": "real_estate", "13": "professional",
        "14": "admin_support", "15": "public_admin", "16": "education", "17": "health_welfare", "18": "arts_other",
        "19": "arts_other", "20": "households", "21": "extraterritorial",
    },
    "work_status": {"1": "employee", "2": "self_employed", "3": "company_owner", "4": "cooperative_member", "5": "kibbutz_member", "6": "unpaid_family"},
    "hours": {"1": "1-4", "2": "5-9", "3": "10-19", "4": "20-34", "5": "35-42", "6": "43-49", "7": "50-59", "8": "60+", "9": "irregular"},
    # asked only of employed persons (99 = not employed); 11 "no income" is rare among them and dropped
    "income": {str(i): f"b{i:02d}" for i in range(1, 11)},
    "hh_income": {str(i): f"h{i:02d}" for i in range(1, 11)} | {"11": "none"},
    "owns_home": {"1": "yes", "2": "no"},
    "health": {"1": "very_good", "2": "good", "3": "not_so_good", "4": "not_good"},
    "chronic": {"1": "yes", "2": "no"},
    "disability": {"1": "yes", "2": "no"},
    "internet": {"1": "yes", "2": "no"},
    "social_networks": {"1": "yes", "2": "no", "3": "no_internet"},
    "study": {"1": "no", "2": "yes", "3": "no"},
    # field of the highest academic degree, in the Council for Higher Education's groups (14,
    # "special and miscellaneous programmes", about 1%, is dropped)
    "field": {"0": "humanities", "1": "humanities", "3": "humanities", "2": "education", "4": "social_sciences",
              "5": "business", "6": "law", "7": "medicine", "8": "paramedical", "9": "math_cs", "10": "physical_sciences",
              "11": "biological_sciences", "12": "agriculture", "13": "engineering"},  # studied in the past / studies now (incl. vacation) / never
    "birth_continent": {"1": "israel", "2": "europe_america", "3": "asia", "4": "africa"},
}

# Frame age band -> survey age group (the survey covers ages 20+; 18-19 borrow 20-24).
AGE_BAND_TO_SURVEY = {
    "18-19": "20-24", "20-24": "20-24", "25-29": "25-29", "30-34": "30-34", "35-39": "35-39", "40-44": "40-44",
    "45-49": "45-49", "50-54": "50-54", "55-59": "55-59", "60-64": "60-64", "65-69": "65-74", "70-74": "65-74",
    "75-79": "75+", "80-84": "75+", "85+": "75+",
}
assert set(AGE_BAND_TO_SURVEY) == set(AGE_BAND_IDS)

# Keys whose every value must get a row even when a table has no respondents in it
# (e.g. employed Arabs aged 75+): such rows take their parent level's distribution.
FULL_DOMAINS = {"age_s": sorted(set(AGE_BAND_TO_SURVEY.values())), "sex": ["female", "male"]}


def load(name: str, codes: dict[str, dict[str, str]] | None = None) -> pd.DataFrame:
    """A generator table with logical column names and our category ids.
    Rows with unknown/not-relevant categories (codes 88/99 or unmapped) are dropped.
    codes: extra codes per variable for this table (e.g. occupation 99 = not employed)."""
    raw = pd.read_csv(SS_DIR / f"{name}.csv", dtype=str)
    out = pd.DataFrame({"count": pd.to_numeric(raw["count"], errors="coerce").fillna(0.0), "rse": pd.to_numeric(raw["rse"], errors="coerce")})
    for col in raw.columns:
        if col.endswith("_code"):
            var = int(col[: -len("_code")])
            name_ = VARS[var]
            out[name_] = raw[col].astype(str).str.replace(r"\.0$", "", regex=True).map(CODES[name_] | (codes or {}).get(name_, {}))
    keep = out.drop(columns=["count", "rse"]).notna().all(axis=1)
    return out[keep].reset_index(drop=True)


def _row_neff(g: pd.DataFrame) -> float:
    """Respondents behind a row: sum of 1/RSE^2 over its non-empty cells (a cell without a usable
    RSE counts as one respondent)."""
    nonzero = g["count"] > 0
    ok = nonzero & (g["rse"] > 0) & (g["rse"] < 1)
    n = float((1.0 / g.loc[ok, "rse"] ** 2).sum()) + float((nonzero & ~ok).sum())
    return min(n, 20000.0)


def hierarchical(df: pd.DataFrame, target: str, levels: list[list[str]], strength: float = 20.0, values: list[str] | None = None) -> pd.DataFrame:
    """P(target | levels[0]) with each level shrunk toward the next (coarser) one.

    levels: most specific first, ending with the coarsest (may be [] for the overall mix).
    Rows cover every combination of the key values seen in the table (a combination with no
    respondents gets its parent's distribution).
    Returns a long DataFrame: levels[0] columns + [target, p, n_eff].
    """
    values = values or sorted(df[target].unique())
    parent: pd.DataFrame | None = None
    for keys in reversed(levels):
        agg = df.groupby(keys + [target], dropna=False)[["count"]].sum().reset_index() if keys else df.groupby([target])[["count"]].sum().reset_index()
        # effective n per row, from the finest cells inside it
        if keys:
            neff = df.groupby(keys).apply(_row_neff, include_groups=False).rename("n_eff").reset_index()
        else:
            neff = pd.DataFrame({"n_eff": [_row_neff(df)]})
        # complete grid: every combination of key values x every target value
        grid = pd.DataFrame({target: values})
        for k in reversed(keys):
            seen = set(df[k].unique()) | set(FULL_DOMAINS.get(k, []))
            grid = pd.DataFrame({k: sorted(seen)}).merge(grid, how="cross")
        grid = grid.merge(agg, on=keys + [target], how="left").fillna({"count": 0.0})
        tot = grid.groupby(keys)["count"].transform("sum") if keys else grid["count"].sum()
        grid["share"] = np.where(tot > 0, grid["count"] / tot, 0.0)
        grid = grid.merge(neff, on=keys, how="left").fillna({"n_eff": 0.0}) if keys else grid.assign(n_eff=float(neff["n_eff"].iloc[0]))
        if parent is None:
            # coarsest level: plain shares (uniform for an empty row)
            empty = (tot == 0) if keys else pd.Series(tot == 0, index=grid.index)
            grid["p"] = np.where(empty, 1.0 / len(values), grid["share"])
        else:
            pkeys = [c for c in parent.columns if c not in (target, "p", "n_eff", "share", "count")]
            grid = grid.merge(parent[pkeys + [target, "p"]].rename(columns={"p": "p_parent"}), on=pkeys + [target], how="left")
            grid["p_parent"] = grid["p_parent"].fillna(1.0 / len(values))
            grid["p"] = (grid["n_eff"] * grid["share"] + strength * grid["p_parent"]) / (grid["n_eff"] + strength)
            grid = grid.drop(columns=["p_parent"])
        parent = grid[keys + [target, "p", "n_eff"]]
    out = parent.copy()
    s = out.groupby(levels[0])["p"].transform("sum") if levels[0] else out["p"].sum()
    out["p"] = out["p"] / s
    return out


def main_effects(
    df: pd.DataFrame,
    target: str,
    rows: list[str],
    by: list[str] | None = None,
    values: list[str] | None = None,
    strength: float = 10.0,
) -> pd.DataFrame:
    """P(target | by, rows[0], rows[1]), each row shrunk toward a main-effects fit.

    Within each `by` slice (e.g. sex), the parent of row (r1, r2) - e.g. (religiosity, age) -
    is the IPF fit of the slice's counts to the margins (r1, target), (r2, target) and (r1, r2):
    the model in which r1 and r2 each shift the distribution of the target but do not interact.
    A thin row (Haredi men aged 20-24) thus borrows from Haredi men of all ages *and* from the
    age pattern of everyone, instead of from all men of that age. Each row is then

        p = (n_eff * share + k * parent) / (n_eff + k),   k = strength,

    with n_eff = respondents behind the row (sum of 1/RSE^2). Rows and slices without
    respondents get the parent (or, for an empty slice, the fit pooled over all slices).
    Returns by + rows + [target, p, n_eff].
    """
    by = by or []
    values = values or sorted(df[target].unique())
    r1, r2 = rows
    v1 = sorted(set(df[r1]) | set(FULL_DOMAINS.get(r1, [])))
    v2 = sorted(set(df[r2]) | set(FULL_DOMAINS.get(r2, [])))
    i1, i2, it = ({v: i for i, v in enumerate(x)} for x in (v1, v2, values))
    df = df[df[target].isin(values)]
    overall = df.groupby(target)["count"].sum().reindex(values).fillna(0.0).to_numpy()
    overall = overall / overall.sum() if overall.sum() > 0 else np.full(len(values), 1 / len(values))

    def fit(g: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        C = np.zeros((len(v1), len(v2), len(values)))
        np.add.at(C, (g[r1].map(i1).to_numpy(), g[r2].map(i2).to_numpy(), g[target].map(it).to_numpy()), g["count"].to_numpy())
        N = np.zeros((len(v1), len(v2)))
        for (a, b), gg in g.groupby([r1, r2]):
            N[i1[a], i2[b]] = _row_neff(gg)
        # half a pseudo-respondent per row, spread like the whole table, so that a category no
        # respondent of a small group happened to report (e.g. divorced Christian men) stays
        # possible, just rare
        per_respondent = C.sum() / max(N.sum(), 1.0)
        Ce = C + 0.5 * per_respondent * overall[None, None, :] + 1e-9 * max(C.sum(), 1.0) / C.size
        M = ipf(np.ones_like(Ce), [((0, 2), Ce.sum(axis=1)), ((1, 2), Ce.sum(axis=0)), ((0, 1), Ce.sum(axis=2))], iters=300)
        parent = M / M.sum(axis=2, keepdims=True)
        return C, N, parent

    pooled = fit(df)[2]
    by_vals = [sorted(set(df[k]) | set(FULL_DOMAINS.get(k, []))) for k in by]
    out = []
    for key in (itertools.product(*by_vals) if by else [()]):
        g = df
        for k, v in zip(by, key):
            g = g[g[k] == v]
        if g["count"].sum() > 0:
            C, N, parent = fit(g)
        else:
            C, N, parent = np.zeros((len(v1), len(v2), len(values))), np.zeros((len(v1), len(v2))), pooled
        tot = C.sum(axis=2, keepdims=True)
        share = np.where(tot > 0, C / np.where(tot > 0, tot, 1.0), parent)
        p = (N[:, :, None] * share + strength * parent) / (N[:, :, None] + strength)
        for a, b, t in itertools.product(range(len(v1)), range(len(v2)), range(len(values))):
            out.append((*key, v1[a], v2[b], values[t], p[a, b, t], N[a, b]))
    res = pd.DataFrame(out, columns=by + [r1, r2, target, "p", "n_eff"])
    res["p"] = res["p"] / res.groupby(by + [r1, r2])["p"].transform("sum")
    return res
