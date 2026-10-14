"""Current studies: whether the person is studying and in what kind of framework. See
docs/methodology/studies.md.

    studying <- group, religiosity, sex, age band, labour status, education

1. Whether: the Social Survey's "studying now" (including vacations) by religiosity or
   religion, sex, age group and labour-force status, combined over the model's own population
   with "studying now" by highest diploma, sex and age group (common.combine).
2. What: the model's students in each cell are split between a bachelor's degree, a
   master's or doctorate, a yeshiva or kollel (or, for women, a midrasha), post-secondary
   education and other courses, by IPF to the counts of the CBS (students by degree, age, sex
   and population group; yeshiva students by age; post-secondary students by sex and age), the
   Council for Higher Education (Arab students by degree and sex) and the Israel Democracy
   Institute (Haredi students by degree), from a seed that allows only what the person's
   diploma, sex and religiosity allow. "Other courses" takes the remainder.
"""

from __future__ import annotations

import numpy as np
import openpyxl
import pandas as pd

from .. import paths
from ..sources import load_sources
from .common import combine
from .joint import joint
from .socioeconomic import ARAB_RELIGION, POPGROUP, STRENGTH, by_population, smooth_ages, write_cpt
from .survey import AGE_BAND_TO_SURVEY, load, main_effects

STUDY = ["yes", "no"]
TYPES = ["first_degree", "graduate", "yeshiva", "post_secondary", "other"]
VALUES = ["none"] + TYPES
EMPLOYMENT_OF = {"employed": "employed", "unemployed": "unemployed", "not_in_labour_force": "not_in_labour_force",
                 "retired": "not_in_labour_force"}
NO_BAGRUT = {"no_diploma", "primary", "secondary"}


# --- published counts ----------------------------------------------------------------------

def _rows(path) -> list[tuple[str, list[float]]]:
    """(first English label, numbers) for every row of a CBS/CHE sheet."""
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    out = []
    for row in ws.iter_rows(values_only=True):
        texts = [c.strip() for c in row if isinstance(c, str) and c.strip()]
        # ".." (fewer than 5 cases, suppressed) and "-" (none) count as zero
        nums = [float(c) if isinstance(c, (int, float)) else 0.0 for c in row
                if isinstance(c, (int, float)) or (isinstance(c, str) and c.strip() in ("..", "-", ". ."))]
        label = next((t for t in texts if t.isascii()), texts[0] if texts else "")
        out.append((label, nums))
    return out


def _file(source: str, name: str):
    src = load_sources()[source]
    return src.raw_path(next(f for f in src.files if f.path == name))


def counts() -> dict:
    """The published counts the split is fitted to, keyed by type."""
    # students by degree, 2024/25 (table 4.31): first rows of the grand total
    t31 = _rows(_file("cbs_abstract_education", "st04_31_2025.xlsx"))
    total = {}
    for label, nums in t31:
        for key, name in (("First degree", "first"), ("Second degree", "second"), ("Third degree", "third")):
            if label.startswith(key) and name not in total:
                total[name] = nums[2]
    # composition by age, sex and population group, 2022/23 (table 4.73)
    comp: dict[str, dict[str, float]] = {"first": {}, "second": {}, "third": {}}
    section = None
    for label, nums in _rows(_file("cbs_abstract_education", "st04_73_2024.xlsx")):
        for key, name in (("FIRST DEGREE", "first"), ("SECOND DEGREE", "second"), ("THIRD DEGREE", "third")):
            if label.startswith(key):
                section = name
        if section is None or not nums:
            continue
        idx = 1 if section == "third" else 3  # the all-institutions column
        if len(nums) > idx and (label.startswith(("Up to", "Thereof: Women", "Arabs")) or label[:1].isdigit()):
            comp[section][label] = nums[idx]
    # Arab students by degree and sex, 2023/24 (CHE table 15)
    che: dict[str, dict[str, float]] = {}
    degree = None
    for label, nums in _rows(_file("che_arab_students_2024", "che_table15.xlsx")):
        for key, name in (("Bachelor", "first"), ("Master", "second"), ("Doctorate", "third")):
            if label.startswith(key):
                degree = name
        if degree and nums and degree not in che and label.startswith("Total"):
            che[degree] = {"total": nums[0]}
        elif degree and nums and degree in che and "women" not in che[degree] and label.startswith("Thereof: women"):
            che[degree]["women"] = nums[0]
    haredi = pd.read_csv(paths.MANUAL / "students" / "haredi_students.csv").set_index("degree")["students"]

    # yeshiva students, 2023/24 (table 4.17): columns midrasha for women, Haredi hesder,
    # hesder, kollel combining training, kollel, yeshiva encouraging service, higher yeshiva, total
    yes = {}
    for label, nums in _rows(_file("cbs_abstract_education", "st04_17_2025.xlsx")):
        if len(nums) == 8 and label not in yes:
            yes[label] = nums
    israeli = [i / t if t else 0.0 for i, t in zip(yes["Israeli"], yes["TOTAL"])]
    ages = ["Up to 19", "20-24", "25-29", "30-34", "35-39", "40-44", "45+"]
    men = {a: yes[a][4] * israeli[4] + yes[a][6] * israeli[6] for a in ages}  # kollel + higher yeshiva
    women = yes["TOTAL"][0] * israeli[0]  # midrasha (hesder students are serving soldiers in the model)

    # post-secondary students, 2023/24 (table 4.27): last column = all frameworks
    post = {}
    for label, nums in _rows(_file("cbs_abstract_education", "st04_27_2025.xlsx")):
        if nums and label in ("GRAND TOTAL", "Men", "Women", "Up to 24", "25-29", "30+") and label not in post:
            post[label] = nums[-1]
    return {"total": total, "comp": comp, "che": che, "haredi": haredi, "yeshiva_men": men, "yeshiva_women": women, "post": post}


# --- 1. studying at all ---------------------------------------------------------------------

def studying_now() -> pd.DataFrame:
    """P(studying | group, religiosity, sex, age band, labour status, education) for every
    combination the model's population has, with its population count."""
    A = by_population("studying", "study", STUDY, extra=["employment"])
    B = {pg: smooth_ages(main_effects(load(name).rename(columns={"diploma": "education"}), "study",
                                      ["education", "age_s"], ["sex"], STUDY, STRENGTH), "study")
         for pg, name in (("jews_and_others", "studying_by_diploma_jo"), ("arabs", "studying_by_diploma_arabs"))}
    W = joint(["group", "religiosity", "sex", "age_band", "labour_status", "education"])
    W = W[W["w"] > 0].copy()
    W["age_s"] = W["age_band"].map(AGE_BAND_TO_SURVEY)
    W["employment"] = W["labour_status"].map(EMPLOYMENT_OF)
    W["popgroup"] = W["group"].map(POPGROUP)

    def a_rows(r_group: str, sub: pd.DataFrame) -> pd.Series:
        """P(yes | a) for the a-keys (religiosity|employment) of one group."""
        if r_group == "jewish":
            t = A["jews"].rename(columns={"religiosity": "rel"})
        elif r_group == "other":
            t = A["others"].assign(rel="*")
        else:
            t = A["arabs"][A["arabs"]["religion"] == ARAB_RELIGION[r_group]].assign(rel="*")
        return t[t["study"] == "yes"]

    out = []
    for (pg, sex, band), w in W[W["employment"].notna()].groupby(["popgroup", "sex", "age_band"]):
        age_s = AGE_BAND_TO_SURVEY[band]
        w = w.copy()
        w["a"] = w["group"] + "|" + w["religiosity"] + "|" + w["employment"]
        rows = []
        for a in w["a"].unique():
            g, rel, emp = a.split("|")
            t = a_rows(g, w)
            t = t[(t["sex"] == sex) & (t["age_s"] == age_s) & (t["employment"] == emp)]
            if g == "jewish":
                t = t[t["rel"] == rel]
            p = float(t["p"].iloc[0])
            rows += [(a, "yes", p), (a, "no", 1 - p)]
        Ac = pd.DataFrame(rows, columns=["a", "study", "p"])
        Bc = B[pg][(B[pg]["sex"] == sex) & (B[pg]["age_s"] == age_s)][["education", "study", "p"]]
        Wc = w.groupby(["a", "education"], as_index=False)["w"].sum()
        c = combine(Wc, "a", "education", Ac, Bc, "study", STUDY)
        c = c[c["study"] == "yes"].rename(columns={"p": "p_study"})
        w = w.merge(c[["a", "education", "p_study"]], on=["a", "education"], how="left")
        out.append(w)
    df = pd.concat(out, ignore_index=True)
    serving = W[W["employment"].isna()].assign(p_study=0.0)  # compulsory service
    return pd.concat([df, serving], ignore_index=True)[
        ["group", "religiosity", "sex", "age_band", "labour_status", "education", "w", "p_study"]]


# --- 2. what they study ---------------------------------------------------------------------

def _band(age_band: str, cuts: dict[str, list[str]]) -> str | None:
    for name, bands in cuts.items():
        if age_band in bands:
            return name
    return None


OLD = ["35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85+"]
FIRST_AGES = {"Up to 19": ["18-19"], "20-24": ["20-24"], "25-29": ["25-29"], "30-34": ["30-34"], "35+": OLD}
GRAD_AGES = {"Up to 29": ["18-19", "20-24", "25-29"], "30-34": ["30-34"], "35-44": ["35-39", "40-44"], "45+": OLD[2:]}
YESHIVA_AGES = {"Up to 19": ["18-19"], "20-24": ["20-24"], "25-29": ["25-29"], "30-34": ["30-34"], "35-39": ["35-39"],
                "40-44": ["40-44"], "45+": OLD[2:]}
POST_AGES = {"Up to 24": ["18-19", "20-24"], "25-29": ["25-29"], "30+": ["30-34"] + OLD}


def seed(df: pd.DataFrame) -> np.ndarray:
    """What each kind of study allows: a first degree mostly after matriculation; a graduate
    degree after a first (or second) degree; a yeshiva or kollel for Haredi men (some
    religious men), a midrasha for religious women; post-secondary studies below a graduate
    degree; other courses for anyone."""
    edu, sex, rel = df["education"], df["sex"], df["religiosity"]
    s = np.zeros((len(df), len(TYPES)))
    s[:, 0] = np.select([edu.isin(["bagrut", "post_secondary", "other_diploma"]), edu.isin(NO_BAGRUT), edu == "ba"], [1.0, 0.1, 0.1], 0.02)
    s[:, 1] = np.select([edu.isin(["ba", "ma"]), edu == "phd"], [1.0, 0.3], 0.0) * (df["age_band"] != "18-19")
    yeshiva = ((sex == "male") & (rel == "haredi")) * 1.0 + ((sex == "male") & rel.isin(["dati", "masorti_dati"])) * 0.15 \
        + ((sex == "female") & rel.isin(["dati", "masorti_dati"])) * 0.2
    s[:, 2] = yeshiva * (df["group"] == "jewish")
    s[:, 3] = np.select([edu.isin(["ma", "phd"]), edu == "ba"], [0.0, 0.3], 1.0)
    s[:, 4] = 1.0
    return s


def constraints(df: pd.DataFrame, c: dict) -> list[tuple[str, np.ndarray, list[int], float]]:
    """The published counts as (name, cells, kinds of study, count), for cells with columns
    group, religiosity, sex and age_band."""
    arab = df["group"].isin(list(ARAB_RELIGION)).to_numpy()
    haredi = (df["religiosity"] == "haredi").to_numpy()
    female = (df["sex"] == "female").to_numpy()
    male = ~female
    T = {t: i for i, t in enumerate(TYPES)}
    cons: list[tuple[str, np.ndarray, list[int], float]] = []

    def add(name: str, mask: np.ndarray, types: list[str], target: float) -> None:
        cons.append((name, mask, [T[t] for t in types], target))

    tot, comp, che = c["total"], c["comp"], c["che"]
    first = tot["first"]
    for label, bands in FIRST_AGES.items():
        share = sum(v for k, v in comp["first"].items() if k == label or (label == "20-24" and k in ("20-21", "22-24")))
        add(f"first degree, ages {label}", df["age_band"].isin(bands).to_numpy(), ["first_degree"], first * share / 100)
    add("first degree, women", female, ["first_degree"], first * comp["first"]["Thereof: Women"] / 100)
    add("first degree, Arabs", arab, ["first_degree"], che["first"]["total"])
    add("first degree, Arab women", arab & female, ["first_degree"], che["first"]["women"])
    add("first degree, Haredim", haredi, ["first_degree"], c["haredi"]["first"])

    second, third = tot["second"], tot["third"]
    grad_age = {"Up to 29": comp["second"]["Up to 24"] + comp["second"]["25-29"], "30-34": comp["second"]["30-34"],
                "35-44": comp["second"]["35-44"], "45+": comp["second"]["45+"]}
    third_age = {"Up to 29": comp["third"]["Up to 29"], "30-34": comp["third"]["30-34"], "35-44": comp["third"]["35-44"],
                 "45+": comp["third"]["45+"]}
    for label, bands in GRAD_AGES.items():
        add(f"graduate degree, ages {label}", df["age_band"].isin(bands).to_numpy(), ["graduate"],
            (second * grad_age[label] + third * third_age[label]) / 100)
    add("graduate degree, women", female, ["graduate"],
        (second * comp["second"]["Thereof: Women"] + third * comp["third"]["Thereof: Women"]) / 100)
    add("graduate degree, Arabs", arab, ["graduate"], che["second"]["total"] + che["third"]["total"])
    add("graduate degree, Haredim", haredi, ["graduate"], c["haredi"]["graduate"])

    for label, bands in YESHIVA_AGES.items():
        add(f"yeshiva or kollel (men), ages {label}", male & df["age_band"].isin(bands).to_numpy(), ["yeshiva"], c["yeshiva_men"][label])
    add("midrasha (women)", female, ["yeshiva"], c["yeshiva_women"])

    post = c["post"]
    for label, bands in POST_AGES.items():
        add(f"post-secondary, ages {label}", df["age_band"].isin(bands).to_numpy(), ["post_secondary"], post[label])
    add("post-secondary, women", female, ["post_secondary"], post["Women"])
    return cons


def split(df: pd.DataFrame, c: dict, iters: int = 500) -> tuple[np.ndarray, list[tuple[str, float, float]]]:
    """IPF of the students in each cell (rows) over the kinds of study (columns) to the
    published counts. Returns the counts and (constraint, target, fitted) for the report."""
    S = (df["w"] * df["p_study"]).to_numpy()
    X = seed(df) * S[:, None]
    X /= np.where(X.sum(axis=1, keepdims=True) > 0, X.sum(axis=1, keepdims=True), 1.0)
    X *= S[:, None]
    cons = constraints(df, c)
    for _ in range(iters):
        for _, mask, idx, target in cons:
            cur = X[np.ix_(mask, idx)].sum()
            if cur > 0:
                X[np.ix_(mask, idx)] *= target / cur
        tot_c = X.sum(axis=1)
        X *= np.where(tot_c > 0, S / np.where(tot_c > 0, tot_c, 1.0), 0.0)[:, None]
    report = [(name, target, float(X[np.ix_(mask, idx)].sum())) for name, mask, idx, target in cons]
    return X, report


def build(log=print) -> None:
    df = studying_now()
    c = counts()
    X, report = split(df, c)
    rep = pd.DataFrame(report, columns=["constraint", "published", "model"])
    rep.to_csv(paths.interim_path("students_fit"), index=False)
    W = df["w"].to_numpy()
    P = X / W[:, None]
    keys = ["group", "religiosity", "sex", "age_band", "labour_status", "education"]
    rows = []
    for i, r in enumerate(df[keys].itertuples(index=False)):
        rows.append((*r, "none", 1 - df["p_study"].iat[i]))
        rows += [(*r, t, P[i, j]) for j, t in enumerate(TYPES)]
    out = pd.DataFrame(rows, columns=keys + ["value", "p"])
    out["p"] = out["p"].clip(lower=0.0)
    # outside the Jewish group the rows do not depend on religiosity: one "*" row (weighted)
    w = df.set_index(keys)["w"].rename("w")
    out = out.merge(w.reset_index(), on=keys)
    jew = out[out["group"] == "jewish"]
    rest = out[out["group"] != "jewish"].assign(religiosity="*", x=lambda f: f["p"] * f["w"])
    rest = rest.groupby(keys + ["value"], as_index=False)[["x", "w"]].sum().assign(p=lambda f: f["x"] / f["w"])
    out = pd.concat([jew, rest], ignore_index=True)[keys + ["value", "p"]]
    write_cpt(out, "studying")
    worst = (rep["model"] / rep["published"] - 1).abs().max()
    students = X.sum(axis=0)
    log(f"  studying: {X.sum():,.0f} students ({', '.join(f'{t} {v:,.0f}' for t, v in zip(TYPES, students))}); "
        f"largest gap to a published count {worst:.1%}")
