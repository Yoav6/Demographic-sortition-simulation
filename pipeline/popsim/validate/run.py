"""Validation: does the model reproduce the figures it was built from, and is it coherent?

Three kinds of checks, written to reports/validation.json (and, through `popsim docs`, to the
generated sections of the methodology docs):

1. Survey margins. The distribution the model implies for a variable - computed exactly from
   the frame and the distribution files (joint.joint) for the survey's universe (ages 20+) - is
   compared with the CBS Social Survey's weighted shares at cuts *coarser* than the ones used
   in estimation (e.g. by religiosity and sex, pooling ages). These catch errors in combining
   tables, in shrinkage and in the model's population weights. Metric: the largest absolute
   difference between model and survey shares in any cell.
2. Sampler. A sample drawn by the TypeScript sampler (the code the website runs) must reproduce
   the exact model shares of every categorical variable within sampling error.
3. Constraints. The sample must contain no combination forbidden in model/constraints.yaml.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .. import paths
from ..estimate.joint import joint
from ..estimate.socioeconomic import ARAB_RELIGION, service_table
from ..estimate.survey import AGE_BAND_TO_SURVEY, load
from ..model_spec import load_spec

ADULT_20 = [b for b in AGE_BAND_TO_SURVEY if b != "18-19"]
MIN_RESPONDENTS = 30  # cells reported in "max abs. difference"
REPORT = paths.REPORTS / "validation.json"


@dataclass
class Check:
    name: str
    nodes: list[str]
    source: str
    tolerance: float
    max_abs_error: float = float("nan")
    # survey checks: largest difference beyond twice the survey's own standard error
    max_excess: float | None = None
    passed: bool = False
    detail: list[dict] = field(default_factory=list)

    def to_json(self) -> dict:
        out = {
            "name": self.name,
            "nodes": self.nodes,
            "source": self.source,
            "tolerance": self.tolerance,
            "max_abs_error": round(float(self.max_abs_error), 5),
            "passed": bool(self.passed),
            "detail": self.detail,
        }
        if self.max_excess is not None:
            out["max_excess"] = round(float(self.max_excess), 5)
        return out


def _neff(g: pd.DataFrame) -> float:
    ok = (g["count"] > 0) & (g["rse"] > 0) & (g["rse"] < 1)
    return float((1.0 / g.loc[ok, "rse"] ** 2).sum())


def compare(model: pd.DataFrame, target: pd.DataFrame, by: list[str], var: str, standardize: str | None = "age_s") -> tuple[float, float, list[dict]]:
    """Shares of `var` within `by` cells: model (column w) vs survey (columns count, rse).

    standardize: the model's shares within each (by, age group) are weighted by the survey's
    age distribution of that cell, so the comparison tests the estimated conditionals rather
    than differences in age composition (checked separately). Returns (max abs difference,
    max difference beyond 2 standard errors of the survey share - computed as if the model were
    right - and the worst cells).
    """
    t = target[target[var].isin(model[var].unique())]
    if standardize and standardize in model.columns and standardize in t.columns:
        pm = model.groupby(by + [standardize, var], as_index=False)["w"].sum()
        pm["p"] = pm["w"] / pm.groupby(by + [standardize])["w"].transform("sum")
        ages = t.groupby(by + [standardize], as_index=False)["count"].sum().rename(columns={"count": "n_age"})
        pm = pm.merge(ages, on=by + [standardize])
        pm["w"] = pm["p"] * pm["n_age"]
        m = pm.groupby(by + [var], as_index=False)["w"].sum()
    else:
        m = model.groupby(by + [var], as_index=False)["w"].sum()
    m["model"] = m["w"] / m.groupby(by)["w"].transform("sum")
    tt = t.groupby(by + [var], as_index=False)["count"].sum()
    tt["target"] = tt["count"] / tt.groupby(by)["count"].transform("sum")
    n = t.groupby(by).apply(_neff, include_groups=False).rename("n").reset_index()
    x = m[by + [var, "model"]].merge(tt[by + [var, "target"]], on=by + [var], how="outer").fillna(0.0).merge(n, on=by, how="left")
    x["err"] = (x["model"] - x["target"]).abs()
    # standard error of the survey share if the model were right (binomial, n = respondents)
    se = np.sqrt(np.clip(x["model"] * (1 - x["model"]), 0.0025, None) / x["n"].clip(lower=1))
    x["excess"] = (x["err"] - 2 * se).clip(lower=0)
    worst = x.sort_values("excess", ascending=False).head(5)
    detail = [{**{k: r[k] for k in by + [var]}, "model": round(r["model"], 4), "survey": round(r["target"], 4), "respondents": int(r["n"])}
              for _, r in worst.iterrows()]
    big = x[x["n"] >= MIN_RESPONDENTS]
    return float(big["err"].max()) if len(big) else float("nan"), float(x["excess"].max()), detail


# ---------------------------------------------------------------------------
# survey-margin checks

def _model(keep: list[str], where: dict | None = None) -> pd.DataFrame:
    """Model counts over `keep` plus the survey age group, for the survey's universe (20+)."""
    w = {"age_band": ADULT_20, **(where or {})}
    m = joint(keep + ["age_band"], where=w)
    m["age_s"] = m["age_band"].map(AGE_BAND_TO_SURVEY)
    return m.drop(columns=["age_band"])


def _jews(var: str, survey_var: str, table: str, where: dict | None = None, mapper: Callable | None = None,
          loader: Callable = load, extra: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    extra = extra or {}
    m = _model(["religiosity", "sex", var, *extra], {"group": ["jewish"], **(where or {})}).rename(columns={var: survey_var, **extra})
    if mapper:
        m = mapper(m, survey_var)
    t = loader(table)
    return m, t


def _arabs(var: str, survey_var: str, table: str, where: dict | None = None, mapper: Callable | None = None,
           loader: Callable = load, extra: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    extra = extra or {}
    m = _model(["group", "sex", var, *extra], {"group": list(ARAB_RELIGION), **(where or {})}).rename(columns={var: survey_var, **extra})
    m["religion"] = m["group"].map(ARAB_RELIGION)
    if mapper:
        m = mapper(m, survey_var)
    t = loader(table)
    t = t[t["religion"].isin(ARAB_RELIGION.values())]
    return m, t


def _labour_to_survey(m: pd.DataFrame, col: str) -> pd.DataFrame:
    m = m[m[col] != "compulsory_service"].copy()
    m[col] = m[col].replace({"retired": "not_in_labour_force"})
    return m


def survey_checks() -> list[Check]:
    specs = [
        # (name, nodes, table, model var, survey var, population, by, tolerance, extra kwargs)
        ("Marital status of Jews by religiosity and sex (20+)", ["marital_status"], "marital_jews", "marital_status", "marital", "jews", ["religiosity", "sex"], 0.03, {}),
        ("Marital status of Arabs by religion and sex (20+)", ["marital_status"], "marital_arabs", "marital_status", "marital", "arabs", ["religion", "sex"], 0.03, {}),
        ("Children of Jews by religiosity and sex (20+)", ["children"], "children_jews", "children", "children", "jews", ["religiosity", "sex"], 0.03, {}),
        ("Children of Arabs by religion and sex (20+)", ["children"], "children_arabs", "children", "children", "arabs", ["religion", "sex"], 0.04, {}),
        ("Highest diploma of Jews by religiosity and sex (20+)", ["education"], "diploma_jews", "education", "diploma", "jews", ["religiosity", "sex"], 0.03, {}),
        ("Highest diploma of Arabs by religion and sex (20+)", ["education"], "diploma_arabs", "education", "diploma", "arabs", ["religion", "sex"], 0.04, {}),
        ("Military/national service of Jews by religiosity and sex (20+)", ["military_service"], "service_jews", "military_service", "service", "jews", ["religiosity", "sex"], 0.03, {"loader": service_table}),
        ("Military/national service of Arabs by religion and sex (20+)", ["military_service"], "service_arabs", "military_service", "service", "arabs", ["religion", "sex"], 0.04, {"loader": service_table}),
        ("Labour-force status of Jews by religiosity and sex (20+)", ["labour_status"], "employment_jews", "labour_status", "employment", "jews", ["religiosity", "sex"], 0.03, {"mapper": _labour_to_survey}),
        ("Labour-force status of Arabs by religion and sex (20+)", ["labour_status"], "employment_arabs", "labour_status", "employment", "arabs", ["religion", "sex"], 0.04, {"mapper": _labour_to_survey}),
        ("Self-rated health of Jews by religiosity and sex (20+)", ["health"], "health_jews", "health", "health", "jews", ["religiosity", "sex"], 0.03, {}),
        ("Self-rated health of Arabs by religion and sex (20+)", ["health"], "health_arabs", "health", "health", "arabs", ["religion", "sex"], 0.04, {}),
        ("Chronic illness of Jews by religiosity and sex (20+)", ["chronic"], "chronic_jews", "chronic", "chronic", "jews", ["religiosity", "sex"], 0.03, {}),
        ("Chronic illness of Arabs by religion and sex (20+)", ["chronic"], "chronic_arabs", "chronic", "chronic", "arabs", ["religion", "sex"], 0.04, {}),
        ("Severe disability of Jews by religiosity and sex (20+)", ["disability"], "disability_jews", "disability", "disability", "jews", ["religiosity", "sex"], 0.03, {}),
        ("Severe disability of Arabs by religion and sex (20+)", ["disability"], "disability_arabs", "disability", "disability", "arabs", ["religion", "sex"], 0.04, {}),
        ("Occupation of employed Jews by religiosity and sex (20+)", ["occupation"], "occupation_jews", "occupation", "occupation", "jews", ["religiosity", "sex"], 0.03,
         {"where": {"labour_status": ["employed"]}, "extra": {"education": "diploma"}, "std": "diploma"}),
        ("Occupation of employed Arabs by religion and sex (20+)", ["occupation"], "occupation_arabs", "occupation", "occupation", "arabs", ["religion", "sex"], 0.04,
         {"where": {"labour_status": ["employed"]}, "extra": {"education": "diploma"}, "std": "diploma"}),
    ]
    out = []
    for name, nodes, table, var, svar, pop, by, tol, kw in specs:
        c = Check(name, nodes, "cbs_social_survey_2024", tol)
        std = kw.pop("std", "age_s")
        m, t = (_jews if pop == "jews" else _arabs)(var, svar, table, **kw)
        if std != "age_s":
            m = m.groupby([col for col in m.columns if col not in ("w", "age_s")], as_index=False)["w"].sum()
        c.max_abs_error, c.max_excess, c.detail = compare(m, t, by, svar, standardize=std)
        c.passed = c.max_excess <= tol
        out.append(c)

    # composition: the model's population vs the survey's, by religiosity (religion), sex and age
    for name, table, by, pop in (
        ("Age composition of Jews by religiosity and sex (20+)", "marital_jews", ["religiosity", "sex"], "jews"),
        ("Age composition of Arabs by religion and sex (20+)", "marital_arabs", ["religion", "sex"], "arabs"),
    ):
        c = Check(name, ["frame", "religiosity"], "cbs_social_survey_2024", 0.03)
        m, t = (_jews if pop == "jews" else _arabs)("marital_status", "marital", table)
        c.max_abs_error, c.max_excess, c.detail = compare(m, t, by, "age_s", standardize=None)
        c.passed = c.max_excess <= c.tolerance
        out.append(c)

    # education and service by continent of birth (Jews)
    for name, nodes, table, var, svar, loader in (
        ("Highest diploma of Jews by continent of birth and sex (20+)", ["education", "birth_region"], "diploma_by_birth_jews", "education", "diploma", load),
        ("Military/national service of Jews by continent of birth and sex (20+)", ["military_service", "birth_region"], "service_by_birth_jews", "military_service", "service", service_table),
    ):
        c = Check(name, nodes, "cbs_social_survey_2024", 0.03)
        m = _model(["birth_region", "sex", var], {"group": ["jewish"]}).rename(columns={var: svar})
        t = loader(table).rename(columns={"birth_continent": "birth_region"})
        c.max_abs_error, c.max_excess, c.detail = compare(m, t, ["birth_region", "sex"], svar)
        c.passed = c.max_excess <= c.tolerance
        out.append(c)

    # earnings, household income and home ownership: Jews-and-others vs Arabs
    pg = {"jewish": "jo", "other": "jo", "muslim": "arabs", "christian_arab": "arabs", "druze": "arabs"}
    for name, nodes, table, var, svar, by_model, by_survey, where in (
        ("Earnings bracket of the employed by occupation and sex (20+)", ["income"], "income_by_occupation", "income", "income", ["occupation", "sex"], ["occupation", "sex"], {"labour_status": ["employed"]}),
        ("Household income bracket by labour-force status (20+)", ["household_income"], "household_income_by_status", "household_income", "hh_income", ["labour_status"], ["employment"], None),
        ("Home ownership by household income bracket (20+)", ["home_ownership"], "home_ownership", "home_ownership", "owns_home", ["household_income"], ["hh_income"], None),
    ):
        for suffix in ("jo", "arabs"):
            c = Check(f"{name} - {'Jews and others' if suffix == 'jo' else 'Arabs'}", nodes, "cbs_social_survey_2024", 0.03 if suffix == "jo" else 0.04)
            groups = [g for g, p in pg.items() if p == suffix]
            m = _model(by_model + [var], {"group": groups, **(where or {})}).rename(columns={var: svar})
            m = m.rename(columns=dict(zip(by_model, by_survey)))
            if "employment" in by_survey:
                m = _labour_to_survey(m, "employment")
            t = load(f"{table}_{suffix}")
            c.max_abs_error, c.max_excess, c.detail = compare(m, t, by_survey, svar)
            c.passed = c.max_excess <= c.tolerance
            out.append(c)
    return out


def vote_check() -> Check:
    """National result of the 2022 election: the model's party shares among its voters vs the
    official shares of valid votes (polling stations and double envelopes)."""
    from ..estimate.vote import PARTIES

    j = joint(["vote_2022"]).set_index("vote_2022")["w"]
    model = j.reindex(PARTIES).fillna(0.0)
    official = pd.read_csv(paths.interim_path("cec2022_national"), index_col=0)["value"].reindex(PARTIES).astype(float)
    m, o = model / model.sum(), official / official.sum()
    c = Check("2022 election: national vote shares", ["vote_2022"], "cec_knesset25", 0.005)
    diff = (m - o).abs()
    c.max_abs_error = float(diff.max())
    c.passed = c.max_abs_error <= c.tolerance
    eligible = j.drop("too_young", errors="ignore").sum()
    c.detail = [{"party": k, "model": round(float(m[k]), 4), "official": round(float(o[k]), 4)} for k in diff.sort_values(ascending=False).index[:5]]
    c.detail.append({"turnout_among_eligible_residents": round(float(model.sum() / eligible), 4)})
    return c


def literacy_checks() -> list[Check]:
    """PIAAC figures the literacy model was *not* fitted to: the national distribution over
    proficiency levels, and the share of low performers (level 1 or below) by age group,
    education and gender. Model population aged 18-64 (PIAAC: residents aged 16-65)."""
    from ..estimate.skills import AGE5, EDU3, piaac_israel

    t = piaac_israel()
    m = joint(["literacy_level", "age_band", "education", "sex"])
    m = m[m["age_band"].isin(list(AGE5))]
    m["age5"] = m["age_band"].map(AGE5)
    m["edu3"] = m["education"].map(EDU3)
    out = []
    lv = m.groupby("literacy_level")["w"].sum()
    lv = lv / lv.sum()
    pub = t["levels"]
    pub = {"below1": pub["below1"], "level1": pub["level1"], "level2": pub["level2"], "level3": pub["level3"], "level4_5": pub["level4"] + pub["level5"]}
    c = Check("Literacy: national distribution over proficiency levels (18-64)", ["literacy_level"], "oecd_piaac_2023_tables", 0.04)
    c.max_abs_error = max(abs(float(lv.get(k, 0.0)) - v / 100) for k, v in pub.items())
    c.detail = [{"level": k, "model": round(float(lv.get(k, 0.0)), 4), "published": round(v / 100, 4)} for k, v in pub.items()]
    c.passed = c.max_abs_error <= c.tolerance
    out.append(c)
    m["low"] = m["literacy_level"].isin(["below1", "level1"])
    for name, col, key, sub in (("age group", "age5", "low_by_age", m), ("education (25-65)", "edu3", "low_by_education", m[m["age5"] != "16-24"]),
                                ("gender", "sex", "low_by_sex", m)):
        share = sub[sub["low"]].groupby(col)["w"].sum() / sub.groupby(col)["w"].sum()
        c = Check(f"Literacy: share of low performers (level 1 or below) by {name}", ["literacy_level"], "oecd_piaac_2023_tables", 0.06)
        diffs = {k: float(share.get(k, float("nan"))) - v / 100 for k, v in t[key].items()}
        c.max_abs_error = max(abs(d) for d in diffs.values())
        c.detail = [{col: k, "model": round(float(share.get(k, float("nan"))), 4), "published": round(v / 100, 4)} for k, v in t[key].items()]
        c.passed = c.max_abs_error <= c.tolerance
        out.append(c)
    return out


# ---------------------------------------------------------------------------
# sampler and constraints

def draw_sample(n: int, seed: int) -> pd.DataFrame:
    model = paths.BUILD / "model.json"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "sample.csv"
        cmd = [
            "npx", "--prefix", str(paths.ROOT / "packages" / "sampler"), "tsx",
            str(paths.ROOT / "packages" / "sampler" / "src" / "cli.ts"),
            "--model", str(model), "--seed", str(seed), "--n", str(n), "--format", "csv", "--out", str(out),
        ]
        subprocess.run(cmd, check=True, cwd=paths.ROOT)
        return pd.read_csv(out, dtype=str, keep_default_na=False)


def _chi2_p(observed: np.ndarray, expected: np.ndarray) -> float:
    """Chi-square goodness-of-fit p-value, with categories expected fewer than 5 times pooled."""
    from scipy.stats import chi2

    rare = expected < 5
    e = np.append(expected[~rare], expected[rare].sum()) if rare.any() else expected
    o = np.append(observed[~rare], observed[rare].sum()) if rare.any() else observed
    keep = e > 0
    if (~keep & (o > 0)).any():
        return 0.0  # a value the table says is impossible was drawn
    e, o = e[keep], o[keep]
    if len(e) < 2:
        return 1.0
    return float(chi2.sf(((o - e) ** 2 / e).sum(), len(e) - 1))


def sampler_check(sample: pd.DataFrame, min_n: int = 2000, combos: int = 25) -> Check:
    """The TypeScript sampler against the model files, node by node. For each table node and
    each of its most common parent combinations (at least `min_n` people), a chi-square test
    compares the sampled values with the table row the sampler should use (back-off
    included); the frame variables are tested against the frame's counts; lookups must map
    exactly. The check passes when the smallest p-value, Bonferroni-adjusted for the number of
    tests, is above 0.001."""
    from ..estimate.joint import _read_table, resolve

    spec = load_spec()
    n = len(sample)
    c = Check(f"Sampler reproduces every table given its parents (n = {n:,}; tolerance: adjusted p-value)", [], "model", 0.001)
    tests: list[tuple[float, float, str, str]] = []  # (p-value, max abs diff in shares, node, parents)
    frame = pd.read_csv(spec.nodes[0].file, dtype=str, keep_default_na=False)
    frame["count"] = frame["count"].astype(float)
    for var in ("group", "sex", "age_band"):
        exact = frame.groupby(var)["count"].sum() / frame["count"].sum()
        obs = sample[var].value_counts().reindex(exact.index).fillna(0.0)
        tests.append((_chi2_p(obs.to_numpy(), exact.to_numpy() * n), float((obs / n - exact).abs().max()), var, "frame"))
        c.nodes.append(var)
    for node in spec.nodes[1:]:
        if node.type == "lookup":
            m = pd.read_csv(node.file, dtype=str, keep_default_na=False).set_index(node.parents[0])["value"]
            bad = int((sample[node.parents[0]].map(m) != sample[node.id]).sum())
            tests.append((0.0 if bad else 1.0, bad / n, node.id, f"{bad} people mis-mapped"))
            c.nodes.append(node.id)
            continue
        if node.type != "table" or node.raw.get("numeric"):
            continue
        cpt = _read_table(node)
        counts = sample.groupby(node.parents, dropna=False).size().sort_values(ascending=False)
        counts = counts[counts >= min_n].head(combos)
        if counts.empty:
            continue
        rows = resolve(cpt, node.parents, node.raw.get("backoff", []), counts.index.to_frame(index=False), node.id)
        for key, cnt in counts.items():
            key = key if isinstance(key, tuple) else (key,)
            sel = np.ones(n, dtype=bool)
            r = rows
            for p_, v in zip(node.parents, key):
                sel &= (sample[p_] == v).to_numpy()
                r = r[r[p_] == v]
            exact = r.set_index("value")["p"]
            exact = exact / exact.sum()
            obs = sample.loc[sel, node.id].value_counts()
            idx = exact.index.union(obs.index)
            e, o = exact.reindex(idx).fillna(0.0), obs.reindex(idx).fillna(0.0)
            tests.append((_chi2_p(o.to_numpy(), e.to_numpy() * cnt), float((o / cnt - e).abs().max()), node.id, " / ".join(map(str, key))))
        c.nodes.append(node.id)
    tests.sort()
    adjusted = min(1.0, tests[0][0] * len(tests))
    c.max_abs_error = max(t[1] for t in tests)
    c.detail = [{"tests": len(tests), "smallest_adjusted_p": round(adjusted, 4)}] + [
        {"node": nid, "parents": det, "p_value": round(pv, 6), "max_abs_diff": round(d, 5)} for pv, d, nid, det in tests[:5]]
    c.passed = adjusted >= c.tolerance
    return c


def percentile_checks(sample: pd.DataFrame) -> list[Check]:
    """A percentile must be uniform over the people it applies to: each tenth of the 0-100 scale
    should hold 10% of them. (Decile shares rather than a Kolmogorov-Smirnov distance, because
    tied values - e.g. households with no income - share one mid-rank percentile.)"""
    out = []
    for var, who in (("income_percentile", "employed citizens"), ("household_income_percentile", "adult citizens"),
                     ("literacy_percentile", "adult citizens")):
        if var not in sample:
            continue
        x = pd.to_numeric(sample[var], errors="coerce").dropna().to_numpy()
        shares = np.histogram(np.clip(x, 0, 99.999), bins=np.arange(0, 101, 10))[0] / len(x)
        c = Check(f"Percentile is uniform among {who} (n = {len(x):,})", [var], "model", 0.01)
        c.max_abs_error = float(np.abs(shares - 0.1).max())
        c.passed = c.max_abs_error <= c.tolerance
        c.detail = [{"decile_shares": [round(float(v), 4) for v in shares]}]
        out.append(c)
    return out


def constraint_checks(sample: pd.DataFrame) -> list[Check]:
    spec = yaml.safe_load((paths.MODEL / "constraints.yaml").read_text(encoding="utf-8"))
    num = sample.copy()
    for col in ("age", "income_amount", "household_income_amount", "income_percentile", "household_income_percentile"):
        if col in num:
            num[col] = pd.to_numeric(num[col], errors="coerce")
    out = []
    for con in spec["constraints"]:
        c = Check(f"Constraint: {con['description']}", con["nodes"], "model/constraints.yaml", 0.0)
        mask = pd.Series(True, index=num.index)
        for var, vals in (con.get("when") or {}).items():
            mask &= num[var].isin([str(v) for v in vals])
        bad = pd.Series(False, index=num.index)
        for var, vals in (con.get("forbid") or {}).items():
            bad |= num[var].isin([str(v) for v in vals])
        for var, vals in (con.get("require") or {}).items():
            bad |= ~num[var].isin([str(v) for v in vals])
        if con.get("expr"):
            ok = num.eval(con["expr"]).astype(bool)
            # a number that does not apply (NaN) satisfies the expression
            used = [col for col in num.columns if col in con["expr"] and num[col].dtype.kind == "f"]
            na = num[used].isna().any(axis=1) if used else pd.Series(False, index=num.index)
            bad |= ~(ok | na)
        n_bad = int((mask & bad).sum())
        c.max_abs_error = n_bad / len(num)
        c.passed = n_bad == 0
        c.detail = [{"violations": n_bad}]
        out.append(c)
    return out


def validate(n: int = 200_000, seed: int = 1, log=print) -> bool:
    spec = load_spec()
    checks = survey_checks()
    checks.append(vote_check())
    checks += literacy_checks()
    sample = draw_sample(n, seed)
    checks.append(sampler_check(sample))
    checks += percentile_checks(sample)
    checks += constraint_checks(sample)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "model_version": spec.version,
        "sample_size": n,
        "seed": seed,
        "checks": [c.to_json() for c in checks],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for c in checks:
        log(f"  {'✓' if c.passed else '✗'} {c.name}: max abs error {c.max_abs_error:.4f} (tolerance {c.tolerance})")
    failed = [c for c in checks if not c.passed]
    log(f"{len(checks) - len(failed)}/{len(checks)} checks passed; report: {REPORT.relative_to(paths.ROOT)}")
    return not failed
