"""Fields of study: of the highest academic degree, and of current academic studies. See
docs/methodology/fields.md.

    degree_field <- education, sex, occupation, media_age, media_sector    (CBS Social Survey)
    study_field  <- studying, sex, degree_field                    (Council for Higher Education)

degree_field: the Social Survey's field of the highest academic degree, by occupation and sex,
by diploma and age group, and by religiosity (or Arab) and sex, combined over the model's own
population of degree holders (common.combine, twice).

study_field: the CHE's students by field, degree and sex (2023/24). Bachelor's students get
the field mix of their sex. Graduate students' fields are tied to the field of the degree they
hold: in each sex, the table of degree field x study field is fitted by IPF to the model's
graduate students by degree field and to the CHE's graduate students by field, from a seed
that makes staying in one's field more likely, so that STAY_SHARE of graduate students study in
the field of their degree (an assumption: no source gives this).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .common import combine, ipf
from .joint import joint
from .media import SECTOR_OF
from .socioeconomic import STRENGTH, write_cpt
from .students import _file, _rows
from .survey import AGE_BAND_TO_SURVEY, load, main_effects

FIELDS = ["humanities", "education", "social_sciences", "business", "law", "medicine", "paramedical", "math_cs",
          "physical_sciences", "biological_sciences", "agriculture", "engineering"]
DEGREES = ["ba", "ma", "phd"]
STAY_SHARE = 0.6
CHE_FIELD = {"Humanities": "humanities", "Education": "education", "Social sciences": "social_sciences",
             "Business": "business", "Law": "law", "Medicine": "medicine", "Para-medical": "paramedical",
             "Mathematics": "math_cs", "Physical": "physical_sciences", "Biological": "biological_sciences",
             "Agriculture": "agriculture", "Engineering": "engineering"}
SECTOR_OF_RELIGIOSITY = {"haredi": "haredi", "dati": "religious", "masorti_dati": "traditional", "masorti": "traditional",
                         "hiloni": "secular"}


def _shares(df: pd.DataFrame, rows: list[str]) -> pd.DataFrame:
    return main_effects(df, "field", rows, None, FIELDS, STRENGTH)


def survey_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """P(field | occupation, sex), P(field | diploma, age group), P(field | sector, sex)."""
    occ = load("field_by_occupation", codes={"occupation": {"99": "none"}})
    A = _shares(occ, ["occupation", "sex"])
    dip = load("field_by_diploma_age").rename(columns={"diploma": "education"})
    B = _shares(dip[dip["education"].isin(DEGREES)], ["education", "age_s"])
    j = load("field_jews")
    j["media_sector"] = j["religiosity"].map(SECTOR_OF_RELIGIOSITY)
    o = load("field_others").assign(media_sector="secular")
    a = load("field_arabs").assign(media_sector="arab")
    C = _shares(pd.concat([j, o, a], ignore_index=True), ["media_sector", "sex"])
    return A, B, C


def build_degree_field(log=print) -> None:
    A, B, C = survey_tables()
    W = joint(["education", "sex", "occupation", "age_band", "religiosity"], where={"education": DEGREES})
    W = W[W["w"] > 0].copy()
    W["age_s"] = W["age_band"].map(AGE_BAND_TO_SURVEY)
    W["media_sector"] = W["religiosity"].map(SECTOR_OF)
    from .media import media_age_of

    band_age = {b: media_age_of(int(b[:2])) for b in W["age_band"].unique()}
    W["media_age"] = W["age_band"].map(band_age)

    # 1. occupation x sex with diploma x age group
    W["a"] = W["occupation"] + "|" + W["sex"]
    W["b"] = W["education"] + "|" + W["age_s"]
    A1 = A.assign(a=A["occupation"] + "|" + A["sex"])[["a", "field", "p"]]
    B1 = B.assign(b=B["education"] + "|" + B["age_s"])[["b", "field", "p"]]
    W1 = W.groupby(["a", "b"], as_index=False)["w"].sum()
    P1 = combine(W1, "a", "b", A1, B1, "field", FIELDS).rename(columns={"p": "p1"})
    # 2. ... with sector x sex
    W["a2"] = W["a"] + "|" + W["b"]
    W["b2"] = W["media_sector"] + "|" + W["sex"]
    A2 = P1.assign(a2=P1["a"] + "|" + P1["b"]).rename(columns={"p1": "p"})[["a2", "field", "p"]]
    C2 = C.assign(b2=C["media_sector"] + "|" + C["sex"])[["b2", "field", "p"]]
    W2 = W.groupby(["a2", "b2"], as_index=False)["w"].sum()
    P2 = combine(W2, "a2", "b2", A2, C2, "field", FIELDS)

    # onto the node's parents, weighting finer cells by their population
    cells = W.groupby(["a2", "b2", "education", "sex", "occupation", "media_age", "media_sector"], as_index=False)["w"].sum()
    x = cells.merge(P2, on=["a2", "b2"]).assign(x=lambda f: f["w"] * f["p"])
    keys = ["education", "sex", "occupation", "media_age", "media_sector"]
    t = x.groupby(keys + ["field"], as_index=False)["x"].sum()
    t["p"] = t["x"] / t.groupby(keys)["x"].transform("sum")
    t = t.rename(columns={"field": "value"})[keys + ["value", "p"]]
    others = [e for e in ("no_diploma", "primary", "secondary", "bagrut", "post_secondary", "other_diploma")]
    rows = pd.DataFrame([(e, "*", "*", "*", "*", "none", 1.0) for e in others], columns=keys + ["value", "p"])
    write_cpt(pd.concat([t, rows], ignore_index=True), "degree_field")
    log(f"  degree_field ({len(t) // len(FIELDS)} cells of degree holders)")


# --- current studies ------------------------------------------------------------------------

def che_fields() -> dict[str, pd.DataFrame]:
    """CHE table 14: students by field and sex, for the bachelor's degree and for master's and
    doctorates together. Returns {first, graduate}: [field, sex, students]."""
    out: dict[str, list] = {"first": [], "graduate": []}
    degree = None
    for label, nums in _rows(_file("che_fields_2024", "che_table14.xlsx")):
        for key, name in (("Bachelor", "first"), ("Master", "graduate"), ("Doctorate", "graduate"), ("Diploma", None)):
            if label.startswith(key) and not nums:
                degree = name
        field = next((f for k, f in CHE_FIELD.items() if label.startswith(k)), None)
        if degree and field and len(nums) >= 8:
            total, women = nums[6], nums[7]
            out[degree] += [(field, "female", women), (field, "male", total - women)]
    return {k: pd.DataFrame(v, columns=["field", "sex", "students"]).groupby(["field", "sex"], as_index=False)["students"].sum()
            for k, v in out.items()}


def build_study_field(log=print) -> None:
    che = che_fields()
    rows = []
    first = che["first"]
    for sex, g in first.groupby("sex"):
        d = g.set_index("field")["students"].reindex(FIELDS).fillna(0.0)
        rows += [("first_degree", sex, "*", f, p) for f, p in (d / d.sum()).items()]

    G = joint(["studying", "sex", "degree_field"], where={"studying": ["graduate"]})
    stays = []
    for sex, g in che["graduate"].groupby("sex"):
        target = g.set_index("field")["students"].reindex(FIELDS).fillna(0.0)
        held = G[G["sex"] == sex].set_index("degree_field")["w"].reindex(FIELDS).fillna(0.0)
        target = target / target.sum() * held.sum()

        def fit(k: float) -> np.ndarray:
            seed = np.ones((len(FIELDS), len(FIELDS))) + k * np.eye(len(FIELDS))
            return ipf(seed, [((0,), held.to_numpy()), ((1,), target.to_numpy())], iters=500)

        lo, hi = 0.0, 1000.0
        for _ in range(60):  # the persistence that gives STAY_SHARE of students in their field
            mid = (lo + hi) / 2
            T = fit(mid)
            if np.trace(T) / T.sum() < STAY_SHARE:
                lo = mid
            else:
                hi = mid
        T = fit((lo + hi) / 2)
        stays.append(np.trace(T) / T.sum())
        cond = T / np.where(T.sum(axis=1, keepdims=True) > 0, T.sum(axis=1, keepdims=True), 1.0)
        for i, held_f in enumerate(FIELDS):
            if held[held_f] <= 0:
                cond[i] = target / target.sum()
            rows += [("graduate", sex, held_f, f, cond[i, j]) for j, f in enumerate(FIELDS)]
    rows += [(s, "*", "*", "none", 1.0) for s in ("none", "yeshiva", "post_secondary", "other")]
    write_cpt(pd.DataFrame(rows, columns=["studying", "sex", "degree_field", "value", "p"]), "study_field")
    log(f"  study_field (CHE 2023/24; graduate students in the field of their degree: {np.mean(stays):.0%})")
