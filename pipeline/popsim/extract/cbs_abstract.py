"""Statistical Abstract of Israel 2025, table 2.3: population of Israelis by population
group, religion, sex and age (thousands, 2024 annual average).

The workbook has six sheets with three population columns each (females, males, total),
right-to-left. Rows are single years of age or bands ("15-19", "95+"); some religion
sheets only have bands. Output (data/interim/cbs_pop_age.csv):
    population, sex, age_from, age_to, thousands
where population is one of: arabs, jews_and_others, total, christians, muslims, jews,
no_religion, druze, arab_christians; age_to is inclusive (None for open-ended bands).
"""

from __future__ import annotations

import re

import openpyxl
import pandas as pd

from .. import paths
from ..sources import load_sources

# column groups per sheet, in sheet order (each: females, males, total)
SHEET_POPULATIONS = {
    "ST02-03a": ["arabs", "jews_and_others", "total"],
    "ST02-03b": ["arabs", "jews_and_others", "total"],
    "ST02-03c": ["christians", "muslims", "jews"],
    "ST02-03d": ["christians", "muslims", "jews"],
    "ST02-03e": ["no_religion", "druze", "arab_christians"],
    "ST02-03f": ["no_religion", "druze", "arab_christians"],
}


def _age(cell) -> tuple[int, int | None] | None:
    if isinstance(cell, (int, float)) and not isinstance(cell, bool):
        return int(cell), int(cell)
    if not isinstance(cell, str):
        return None
    s = cell.strip()
    m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r"(\d+)\+", s)
    if m:
        return int(m.group(1)), None
    if s.isdigit():
        return int(s), int(s)
    return None


def extract() -> pd.DataFrame:
    src = load_sources()["cbs_abstract_2025_population"]
    path = src.raw_path(next(f for f in src.files if f.path == "st02_03.xlsx"))
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = []
    for sheet, pops in SHEET_POPULATIONS.items():
        for row in wb[sheet].iter_rows(values_only=True):
            age = _age(row[0])
            if age is None:
                continue
            nums = [c for c in row[1:] if isinstance(c, (int, float))]
            if len(nums) < 9:
                continue
            for k, pop in enumerate(pops):
                f, m, _t = nums[3 * k : 3 * k + 3]
                rows.append((pop, "female", age[0], age[1], float(f)))
                rows.append((pop, "male", age[0], age[1], float(m)))
    df = pd.DataFrame(rows, columns=["population", "sex", "age_from", "age_to", "thousands"])
    df = df.drop_duplicates(["population", "sex", "age_from", "age_to"])
    out = paths.interim_path("cbs_pop_age")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df
