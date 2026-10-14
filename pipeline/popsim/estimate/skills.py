"""Adult literacy proficiency (OECD Survey of Adult Skills, PIAAC 2022-23). See
docs/methodology/skills.md.

A person's literacy score is modelled as

    S = mu(cell) + e,   e ~ Normal(0, s_w^2),
    mu = base + group effect (Arab / Haredi / other Jewish) + age effect + education effect + sex effect,

with the effects fitted (weighted least squares) so that the model population's mean scores
reproduce the published means by age group, education (ages 25-65) and gender (OECD) and by
population group (Bank of Israel). s_w is the spread left within cells once the effects explain
part of the national standard deviation. The proficiency level follows from the normal CDF at the
PIAAC cut-offs (176, 226, 276, 326); a score is then drawn inside the level, and ranked among all
adult citizens in the model. PIAAC covers ages 16-65; for older people the age effect is
extrapolated (see AGE_CENTRE).
"""

from __future__ import annotations

import math

import numpy as np
import openpyxl
import pandas as pd

from .. import paths
from ..sources import load_sources
from .joint import joint
from .socioeconomic import write_cpt

LEVELS = ["below1", "level1", "level2", "level3", "level4_5"]
CUTS = [176.0, 226.0, 276.0, 326.0]
SCORE_RANGE = {"below1": (100, 175), "level1": (176, 225), "level2": (226, 275), "level3": (276, 325), "level4_5": (326, 400)}
AGE5 = {"18-19": "16-24", "20-24": "16-24", "25-29": "25-34", "30-34": "25-34", "35-39": "35-44", "40-44": "35-44",
        "45-49": "45-54", "50-54": "45-54", "55-59": "55-65", "60-64": "55-65"}
# centre of each age band past PIAAC's range (16-65), for extrapolating the age effect; held
# constant from 80
AGE_CENTRE = {"65-69": 67.0, "70-74": 72.0, "75-79": 77.0, "80-84": 80.0, "85+": 80.0}
EDU3 = {"no_diploma": "below_upper_secondary", "primary": "below_upper_secondary", "secondary": "upper_secondary",
        "bagrut": "upper_secondary", "other_diploma": "upper_secondary", "post_secondary": "tertiary", "ba": "tertiary",
        "ma": "tertiary", "phd": "tertiary"}
ARAB_GROUPS = {"muslim", "christian_arab", "druze"}


def _israel_numbers(path, sheet: str) -> list[float]:
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet]
    for row in ws.iter_rows(values_only=True):
        if row and isinstance(row[0], str) and row[0].strip() == "Israel":
            return [float(c) for c in row[1:] if isinstance(c, (int, float))]
    raise ValueError(f"no Israel row in {sheet}")


def piaac_israel() -> dict:
    """Israel's literacy figures from the OECD annex tables and the Bank of Israel note."""
    src = load_sources()["oecd_piaac_2023_tables"]
    ch2 = src.raw_path(next(f for f in src.files if f.path == "piaac_2023_chapter2_tables.xlsx"))
    ch3 = src.raw_path(next(f for f in src.files if f.path == "piaac_2023_chapter3_tables.xlsx"))
    a21 = _israel_numbers(ch2, "A.2.1 (L) ")
    a22 = _israel_numbers(ch2, "A.2.2 (L)")
    a24 = _israel_numbers(ch2, "A.2.4 (L)")
    a25 = _israel_numbers(ch2, "A.2.5 (L)")
    a27 = _israel_numbers(ch2, "A.2.7 (L)")
    a311 = _israel_numbers(ch3, "A.3.11 (L)")
    c2 = a311[a311.index(2023.0) + 1:]
    boi = pd.read_csv(paths.MANUAL / "piaac" / "boi_group_means.csv")
    lit = boi[boi["domain"] == "literacy"].set_index("group")["mean_score"]
    return {
        "mean": a21[0], "sd": a21[4],
        "percentiles": dict(zip([5, 10, 25, 50, 75, 90, 95], a21[6:20:2])),
        "levels": dict(zip(["below1", "level1", "level2", "level3", "level4", "level5"], a22[0:12:2])),
        "age": dict(zip(["16-24", "25-34", "35-44", "45-54", "55-65"], a24[2:12:2])),
        "low_by_age": dict(zip(["16-24", "25-34", "35-44", "45-54", "55-65"], a24[18:28:2])),
        "education": dict(zip(["below_upper_secondary", "upper_secondary", "tertiary"], a25[2:8:2])),
        "low_by_education": dict(zip(["below_upper_secondary", "upper_secondary", "tertiary"], a25[14:20:2])),
        "sex": {"male": a27[2], "female": a27[4]},
        "low_by_sex": {"male": a27[12], "female": a27[14]},
        "education_by_age": {  # cycle 2, excluding doorstep-only interviews
            ("below_upper_secondary", "25-44"): c2[2], ("below_upper_secondary", "45-65"): c2[4],
            ("upper_secondary", "25-44"): c2[8], ("upper_secondary", "45-65"): c2[10],
            ("tertiary", "25-44"): c2[14], ("tertiary", "45-65"): c2[16],
        },
        "group": {"other_jewish": float(lit["non_haredi_jews"]), "arab": float(lit["arabs"]), "haredi": float(lit["haredim"])},
    }


def group3(group: str, religiosity: str) -> str:
    if group in ARAB_GROUPS:
        return "arab"
    return "haredi" if religiosity == "haredi" else "other_jewish"


def model_cells() -> pd.DataFrame:
    c = joint(["group", "religiosity", "sex", "age_band", "education"])
    c["g3"] = [group3(g, r) for g, r in zip(c["group"], c["religiosity"])]
    c["age5"] = c["age_band"].map(AGE5)
    c["edu3"] = c["education"].map(EDU3)
    return c


PARAMS = ["base", "g:arab", "g:haredi", "a:16-24", "a:35-44", "a:45-54", "a:55-65", "e:below_upper_secondary", "e:tertiary", "s:female"]


def _design(c: pd.DataFrame) -> np.ndarray:
    """Indicator matrix of the cells (reference levels: other Jewish, 25-34, upper secondary, men)."""
    X = np.zeros((len(c), len(PARAMS)))
    X[:, 0] = 1.0
    for j, p in enumerate(PARAMS[1:], start=1):
        kind, val = p.split(":")
        col = {"g": "g3", "a": "age5", "e": "edu3", "s": "sex"}[kind]
        X[:, j] = (c[col] == val).to_numpy()
    return X


def fit(c: pd.DataFrame, t: dict) -> tuple[np.ndarray, float, pd.DataFrame]:
    """Effects reproducing the published means over the model's population aged 18-64."""
    fitc = c[c["age5"].notna()]
    X = _design(fitc)
    w = fitc["w"].to_numpy()
    rows, targets, names = [], [], []

    def add(mask: np.ndarray, target: float, name: str) -> None:
        ww = w * mask
        rows.append(ww @ X / ww.sum())
        targets.append(target)
        names.append(name)

    for a, v in t["age"].items():
        add((fitc["age5"] == a).to_numpy(), v, f"age {a}")
    adult = (fitc["age5"] != "16-24").to_numpy()
    for e, v in t["education"].items():
        add(adult & (fitc["edu3"] == e).to_numpy(), v, f"education {e} (25-65)")
    for s_, v in t["sex"].items():
        add((fitc["sex"] == s_).to_numpy(), v, f"sex {s_}")
    for g, v in t["group"].items():
        add((fitc["g3"] == g).to_numpy(), v, f"group {g}")
    A, b = np.array(rows), np.array(targets)
    beta, *_ = np.linalg.lstsq(A, b, rcond=None)
    report = pd.DataFrame({"target": names, "published": b, "model": A @ beta})
    mu = X @ beta
    mean = np.average(mu, weights=w)
    between = np.average((mu - mean) ** 2, weights=w)
    s_w = math.sqrt(max(t["sd"] ** 2 - between, 1.0))
    return beta, s_w, report


def cell_mean(beta: np.ndarray, g3: str, age_band: str, edu3: str, sex: str) -> float:
    coef = dict(zip(PARAMS, beta))
    mu = coef["base"] + coef.get(f"g:{g3}", 0.0) + coef.get(f"e:{edu3}", 0.0) + coef.get(f"s:{sex}", 0.0)
    if age_band in AGE5:
        mu += coef.get(f"a:{AGE5[age_band]}", 0.0)
    else:  # past 65: continue the 45-54 -> 55-65 decline (net of education) linearly
        slope = (coef["a:55-65"] - coef["a:45-54"]) / 10.5
        mu += coef["a:55-65"] + slope * (AGE_CENTRE[age_band] - 60.0)
    return mu


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def level_probs(mu: float, s_w: float) -> list[float]:
    cdf = [_phi((c - mu) / s_w) for c in CUTS]
    edges = [0.0] + cdf + [1.0]
    return [edges[i + 1] - edges[i] for i in range(len(LEVELS))]


def build(log=print) -> None:
    t = piaac_israel()
    c = model_cells()
    beta, s_w, report = fit(c, t)
    report.to_csv(paths.interim_path("piaac_fit"), index=False)

    rows = []
    groups = {"jewish": ["haredi", "dati", "masorti_dati", "masorti", "hiloni"], "other": ["*"], "muslim": ["*"], "christian_arab": ["*"], "druze": ["*"]}
    from .common import AGE_BAND_IDS, SEXES

    for g, rels in groups.items():
        for rel in rels:
            g3 = group3(g, rel)
            for sex in SEXES:
                for band in AGE_BAND_IDS:
                    for edu, e3 in EDU3.items():
                        mu = cell_mean(beta, g3, band, e3, sex)
                        for lvl, p in zip(LEVELS, level_probs(mu, s_w)):
                            rows.append((g, rel, sex, band, edu, lvl, p))
    df = pd.DataFrame(rows, columns=["group", "religiosity", "sex", "age_band", "education", "value", "p"])
    write_cpt(df, "literacy_level")
    pd.DataFrame([(k, lo, hi) for k, (lo, hi) in SCORE_RANGE.items()], columns=["literacy_level", "lo", "hi"]).to_csv(
        paths.CPTS / "literacy_score.csv", index=False
    )

    # percentile breakpoints: level shares in the model, uniform within a level (as drawn)
    shares = joint(["literacy_level"]).set_index("literacy_level")["w"].reindex(LEVELS).fillna(0.0)
    shares = shares / shares.sum()
    xs, fs, cum = [], [], 0.0
    for lvl in LEVELS:
        lo, hi = SCORE_RANGE[lvl]
        xs += [lo, hi]
        fs += [cum, cum + shares[lvl]]
        cum += shares[lvl]
    bps = [float(np.interp(q, fs, xs)) for q in np.linspace(0, 1, 101)]
    pd.DataFrame({"percentile": range(101), "value": np.round(bps, 2)}).to_csv(paths.CPTS / "literacy_percentile.csv", index=False)
    worst = (report["model"] - report["published"]).abs().max()
    log(f"  literacy: within-cell SD {s_w:.1f}; largest gap to a published mean {worst:.1f} points; "
        f"levels {', '.join(f'{k} {v:.1%}' for k, v in shares.items())}")
