"""Small deterministic/derived nodes built from the frame inputs.

* age          P(single-year age | group, sex, age band) from the national profiles.
* district     lookup locality -> CBS district.
* locality_type lookup locality -> coarse settlement type.
* sector       group + locality -> the "sector" shown to users (Bedouin and Circassian
               Muslims are identified by their locality; see data/manual/localities).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .. import paths
from .common import AGE_BANDS, GROUPS, MAX_AGE, SEXES, band_id
from .frame import AGES, national_profiles

DISTRICTS = {1: "jerusalem", 2: "north", 3: "haifa", 4: "center", 5: "tel_aviv", 6: "south", 7: "judea_samaria"}


def build_age(log=print) -> None:
    nat = national_profiles(pd.read_csv(paths.interim_path("cbs_pop_age")))
    rows = []
    for g in GROUPS:
        for s_i, s in enumerate(SEXES):
            prof = nat[g][s_i]
            for lo, hi in AGE_BANDS:
                ages = np.arange(lo, min(hi, MAX_AGE) + 1)
                w = prof[ages]
                if w.sum() <= 0:
                    w = np.ones_like(ages, dtype=float)
                w = w / w.sum()
                for a, p in zip(ages, w):
                    if p > 0:
                        rows.append((g, s, band_id(lo, hi), str(a), p))
    pd.DataFrame(rows, columns=["group", "sex", "age_band", "value", "p"]).to_csv(paths.CPTS / "age.csv", index=False)
    ages = [str(a) for a in range(18, MAX_AGE + 1)]
    (paths.MODEL / "domains").mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"id": ages, "en": ages, "he": ages}).to_csv(paths.MODEL / "domains" / "age.csv", index=False)
    log(f"  age: {len(rows)} rows")


def locality_type(form: int | str) -> str:
    try:
        f = int(form)
    except (TypeError, ValueError):
        return "other"
    if f in (120, 130, 140):
        return "large_city"
    if f in (150, 160):
        return "city"
    if 170 <= f <= 193:
        return "town"
    if f in (250, 260):
        return "arab_city"
    if f in (270, 280, 290, 440, 450):
        return "arab_town"
    if f in (310, 320):
        return "moshav"
    if f == 330:
        return "kibbutz"
    if f == 370:
        return "community"
    if f == 460:
        return "bedouin_tribe"
    return "rural_other"


def build_lookups(log=print) -> None:
    loc = pd.read_csv(paths.MODEL / "domains" / "locality.csv", dtype={"id": str})
    lk = paths.MODEL / "lookups"
    lk.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"locality": loc["id"], "value": loc["district"].map(lambda d: DISTRICTS[int(d)])}).to_csv(lk / "district.csv", index=False)
    pd.DataFrame({"locality": loc["id"], "value": loc["form"].map(locality_type)}).to_csv(lk / "locality_type.csv", index=False)
    # sector: Bedouin / Circassian Muslims by locality, otherwise by group
    rows = [
        ("jewish", "*", "jewish"),
        ("muslim", "*", "arab_muslim"),
        ("christian_arab", "*", "arab_christian"),
        ("druze", "*", "druze"),
        ("other", "*", "other"),
    ]
    for r in loc.itertuples(index=False):
        if r.special in ("bedouin", "circassian"):
            rows.append(("muslim", r.id, r.special))
    pd.DataFrame([(g, l, v, 1.0) for g, l, v in rows], columns=["group", "locality", "value", "p"]).to_csv(
        paths.CPTS / "sector.csv", index=False
    )
    log(f"  lookups: {len(loc)} localities; sector rows {len(rows)}")
