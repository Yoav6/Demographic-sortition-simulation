"""Statistical Abstract 2021, table 2.8: Jews by country of origin and age (2020 average).

Origin is the person's country of birth if born abroad, the father's country of birth if
born in Israel; Israel-born people with Israel-born fathers are the "third generation".
Output data/interim/cbs_origin_age.csv:
    origin, generation (immigrant | second_gen | third_gen), age_from, age_to, thousands
"""

from __future__ import annotations

import re

import pandas as pd

from .. import paths
from ..sources import load_sources

COUNTRY = {
    "Turkey": "turkey",
    "Iraq": "iraq",
    "Yemen": "yemen",
    "Iran": "iran",
    "India and Pakistan": "india",
    "Syria and Lebanon": "syria_lebanon",
    "Morocco": "morocco",
    "Algeria and Tunisia": "algeria_tunisia",
    "Libya": "libya",
    "Egypt": "egypt",
    "Ethiopia": "ethiopia",
    "USSR (former)": "fsu",
    "Poland": "poland",
    "Romania": "romania",
    "Bulgaria and Greece": "bulgaria_greece",
    "Germany and Austria": "germany_austria",
    "Czech Republic, Slov": "czech_hungary",
    "France": "france",
    "United Kingdom": "uk",
    "Europe, other": "europe_other",
    "North America and Oc": "north_america",
    "Argentina": "argentina",
    "Latin America, other": "latin_america_other",
}
CONTINENT_OTHER = {"Asia - total": "asia_other", "Africa - total": "africa_other"}


def _band(label: str) -> tuple[int, int | None]:
    s = str(label).strip()
    m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r"(\d+)\+", s)
    if m:
        return int(m.group(1)), None
    raise ValueError(s)


def extract() -> pd.DataFrame:
    src = load_sources()["cbs_abstract_2021_origin"]
    df = pd.read_excel(src.raw_path(src.files[0]), header=None)
    header = df.iloc[4].tolist()
    # columns: born abroad bands ... "Total", then Israeli-born bands ... "Total"
    cols: list[tuple[int, str, tuple[int, int | None]]] = []
    section = "immigrant"
    for j, h in enumerate(header):
        if not isinstance(h, str):
            continue
        if h.strip() == "Total":
            section = "second_gen"
            continue
        try:
            cols.append((j, section, _band(h)))
        except ValueError:
            continue
    rows = []
    others = {}
    for i in range(5, len(df)):
        name = str(df.iloc[i, 0]).strip()
        values = {j: pd.to_numeric(df.iloc[i, j], errors="coerce") for j, _, _ in cols}
        if name.startswith("Israeli born - father born in Israel"):
            for j, section, (lo, hi) in cols:
                if section == "second_gen" and pd.notna(values[j]):
                    rows.append(("israel", "third_gen", lo, hi, float(values[j])))
            continue
        key = next((v for k, v in COUNTRY.items() if name.startswith(k)), None)
        if key is None and name in CONTINENT_OTHER:
            others[name] = values
            continue
        if key is None:
            continue
        for j, section, (lo, hi) in cols:
            v = values[j]
            if pd.notna(v):
                rows.append((key, section, lo, hi, float(v)))
    out = pd.DataFrame(rows, columns=["origin", "generation", "age_from", "age_to", "thousands"])
    # "other" countries of each continent = continent total minus the listed countries
    asia = ["turkey", "iraq", "yemen", "iran", "india", "syria_lebanon"]
    africa = ["morocco", "algeria_tunisia", "libya", "egypt", "ethiopia"]
    for name, members in (("Asia - total", asia), ("Africa - total", africa)):
        vals = others.get(name, {})
        for j, section, (lo, hi) in cols:
            tot = vals.get(j)
            if tot is None or pd.isna(tot):
                continue
            listed = out[(out.origin.isin(members)) & (out.generation == section) & (out.age_from == lo)]["thousands"].sum()
            rows.append((CONTINENT_OTHER[name], section, lo, hi, max(float(tot) - listed, 0.0)))
    out = pd.DataFrame(rows, columns=["origin", "generation", "age_from", "age_to", "thousands"])
    out.to_csv(paths.interim_path("cbs_origin_age"), index=False)
    return out
