"""Self-rated health, chronic illness and severe functional disability (CBS Social Survey 2024).

    health     <- group, religiosity, sex, age band, education
    chronic    <- group, religiosity, sex, age band, health
    disability <- group, religiosity, sex, age band, health, chronic

Each node combines the population table (by religiosity or religion, sex and age) with a
table by its other parent (diploma; self-rated health; health x chronic illness) through
socioeconomic.with_second(): IPF over the model's own joint counts, as for labour-force status.
See docs/methodology/health.md.
"""

from __future__ import annotations

import pandas as pd

from .joint import joint
from .socioeconomic import STRENGTH, by_diploma, by_population, smooth_ages, with_second, write_cpt
from .survey import load, main_effects

HEALTH = ["very_good", "good", "not_so_good", "not_good"]
YES_NO = ["yes", "no"]


def build_health(log=print) -> None:
    A = by_population("health", "health", HEALTH)
    B = by_diploma("health_by_diploma", "health", HEALTH)
    write_cpt(with_second(A, B, "education", "health", HEALTH), "health")
    log("  health")


def build_chronic(log=print) -> None:
    A = by_population("chronic", "chronic", YES_NO)
    B = smooth_ages(main_effects(load("chronic_by_health"), "chronic", ["health", "age_s"], ["sex"], YES_NO, STRENGTH), "chronic")
    write_cpt(with_second(A, B, "health", "chronic", YES_NO), "chronic")
    log("  chronic")


def build_disability(log=print) -> None:
    """The table by health x chronic illness has no sex: it is used for both sexes, and sex
    enters through the population table."""
    A = by_population("disability", "disability", YES_NO)
    t = load("disability_by_health")
    t["hc"] = t["health"] + "|" + t["chronic"]
    b = smooth_ages(main_effects(t, "disability", ["hc", "age_s"], [], YES_NO, STRENGTH), "disability")
    B = pd.concat([b.assign(sex="male"), b.assign(sex="female")], ignore_index=True)

    def W(keep: list[str], where: dict) -> pd.DataFrame:
        m = joint([k for k in keep if k != "hc"] + ["health", "chronic"], where=where)
        m["hc"] = m["health"] + "|" + m["chronic"]
        return m.groupby(keep, as_index=False)["w"].sum()

    df = with_second(A, B, "hc", "disability", YES_NO, W=W)
    df[["health", "chronic"]] = df["hc"].str.split("|", expand=True)
    write_cpt(df[["group", "religiosity", "sex", "age_band", "health", "chronic", "value", "p"]], "disability")
    log("  disability")
