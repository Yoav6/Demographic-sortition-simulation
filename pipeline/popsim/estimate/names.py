"""First names: P(name | group, sex, birth cohort).

Sources
* CBS release 391/2025, table 1: current residents born 1949-2024 by sex, population group
  (Jews, Muslims, Christian Arabs, Druze), first name and year of birth. Cells under 5 are
  suppressed (".."); each name's suppressed cells share its residual (total - shown) equally.
  It covers immigrants too (names are the current registry names of everyone born that year).
* IGRA population-registry tables for religion "Other" (no birth years). Each name's age
  profile is borrowed from the CBS Jewish table when the name appears there:
      P(name | other, sex, cohort) ∝ count_IGRA(name) * share_CBS-Jewish(cohort | name) / share_CBS-Jewish(cohort)

People born before 1949 (aged 76+) use the 1949-1953 cohort - an approximation.
Per (group, sex, cohort) the most common names covering COVERAGE of people are kept.
"""

from __future__ import annotations

import json

import numpy as np
import openpyxl
import pandas as pd

from .. import paths
from ..sources import load_sources

REFERENCE_YEAR = 2024  # ages in the model refer to the end of 2024
COVERAGE = 0.97
MAX_NAMES = 600

SHEETS = {
    ("jewish", "female"): "בנות יהודיות",
    ("jewish", "male"): "בנים יהודים",
    ("muslim", "female"): "בנות מוסלמיות",
    ("muslim", "male"): "בנים מוסלמים",
    ("christian_arab", "female"): "בנות נוצריות-ערביות",
    ("christian_arab", "male"): "בנים נוצרים-ערבים",
    ("druze", "female"): "בנות דרוזיות",
    ("druze", "male"): "בנים דרוזים",
}

# Birth cohorts (inclusive). Everyone born before 1949 uses the first cohort.
COHORTS = [(1949, 1953)] + [(y, y + 4) for y in range(1954, 2004, 5)] + [(2004, REFERENCE_YEAR - 18)]


def cohort_id(lo: int, hi: int) -> str:
    return f"{lo}-{hi}"


COHORT_IDS = [cohort_id(lo, hi) for lo, hi in COHORTS]


def cohort_of_birth_year(y: int) -> str:
    for lo, hi in COHORTS:
        if y <= hi and (y >= lo or lo == 1949):
            return cohort_id(lo, hi)
    return COHORT_IDS[-1]


def _num(x) -> float | None:
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.replace(",", "").strip()
        if s == "..":
            return None
        try:
            return float(s)
        except ValueError:
            return 0.0
    return 0.0


def read_cbs_names() -> pd.DataFrame:
    """Long table: group, sex, name, year, count (suppressed cells imputed)."""
    src = load_sources()["cbs_names"]
    wb = openpyxl.load_workbook(src.raw_path(src.files[0]), read_only=True, data_only=True)
    out = []
    for (group, sex), sheet in SHEETS.items():
        years = None
        for row in wb[sheet].iter_rows(values_only=True):
            if row[0] == "prati1":
                years = [int(y) for y in row[2:] if y is not None]
                continue
            if years is None or not isinstance(row[0], str) or not row[0].strip():
                continue
            name = row[0].strip().replace("'", "'")
            total = _num(row[1]) or 0.0
            cells = [_num(c) for c in row[2 : 2 + len(years)]]
            shown = sum(c for c in cells if c is not None)
            n_supp = sum(1 for c in cells if c is None)
            fill = max(total - shown, 0.0) / n_supp if n_supp else 0.0
            fill = min(fill, 4.0)
            for y, c in zip(years, cells):
                v = fill if c is None else c
                if v > 0:
                    out.append((group, sex, name, y, v))
    return pd.DataFrame(out, columns=["group", "sex", "name", "year", "count"])


def read_igra(sex: str) -> pd.DataFrame:
    src = load_sources()["igra_registry_names"]
    f = next(f for f in src.files if f.path == f"other-{sex}.json")
    data = json.loads(src.raw_path(f).read_text(encoding="utf-8"))
    return pd.DataFrame(data)[["name", "first"]].rename(columns={"first": "count"})


def _top(d: pd.DataFrame) -> pd.DataFrame:
    d = d.sort_values("count", ascending=False)
    cum = d["count"].cumsum() / d["count"].sum()
    keep = d[(cum.shift(fill_value=0) < COVERAGE)].head(MAX_NAMES)
    return keep.assign(p=keep["count"] / keep["count"].sum())


ARAB_GROUPS = {"muslim", "christian_arab", "druze"}
ARAB_PREFIX = "ar:"


def name_id(group: str, name: str) -> str:
    """Names of Arab and Druze citizens get their own ids ("ar:עומר"), because the same Hebrew
    spelling is often written differently in English (Omar vs Omer, Yusuf vs Yosef)."""
    return ARAB_PREFIX + name if group in ARAB_GROUPS else name


def build(log=print) -> None:
    cbs = read_cbs_names()
    cbs["cohort"] = cbs["year"].map(cohort_of_birth_year)
    rows = []
    for (group, sex, cohort), d in cbs.groupby(["group", "sex", "cohort"]):
        agg = d.groupby("name", as_index=False)["count"].sum()
        for r in _top(agg).itertuples(index=False):
            rows.append((group, sex, cohort, name_id(group, r.name), r.p))

    # "Other": IGRA registry counts x age profile borrowed from the Jewish table
    jew = cbs[cbs["group"] == "jewish"]
    for sex in ("female", "male"):
        igra = read_igra(sex)
        js = jew[jew["sex"] == sex]
        cohort_share = js.groupby("cohort")["count"].sum()
        cohort_share /= cohort_share.sum()
        by_name = js.pivot_table(index="name", columns="cohort", values="count", aggfunc="sum", fill_value=0)
        profile = by_name.div(by_name.sum(axis=1), axis=0).div(cohort_share, axis=1)
        for cohort in COHORT_IDS:
            prof = profile[cohort] if cohort in profile.columns else pd.Series(dtype=float)
            w = igra.assign(count=igra["count"] * igra["name"].map(prof).fillna(1.0))
            for r in _top(w[w["count"] > 0]).itertuples(index=False):
                rows.append(("other", sex, cohort, r.name, r.p))

    cpt = pd.DataFrame(rows, columns=["group", "sex", "birth_cohort", "value", "p"])
    cpt.to_csv(paths.CPTS / "first_name.csv", index=False)

    ids = sorted(cpt["value"].unique())
    sexw = cpt.groupby(["value", "sex"])["p"].sum().unstack(fill_value=0)
    cands = wikidata_candidates()
    ov = pd.read_csv(paths.MANUAL / "names" / "english_overrides.csv", dtype=str, keep_default_na=False)
    overrides = {(r.he, r.style): (r.en, r.en_f) for r in ov.itertuples(index=False)}
    rows = []
    for i in ids:
        he = i.removeprefix(ARAB_PREFIX)
        style = "arabic" if i.startswith(ARAB_PREFIX) else "hebrew"
        found = overrides.get((he, style)) or overrides.get((he, ""))
        if found:
            en, en_f = found
            source = "curated"
        else:
            rule = transliterate(he, style)
            male_c = cands.get((he, "male"), [])
            female_c = cands.get((he, "female"), [])
            any_c = cands.get((he, "any"), [])
            male = closest(male_c or any_c, rule)
            female = closest(female_c or any_c, rule)
            if male or female:
                # `en` is the masculine (or only) form; `en_f` a different feminine form
                mostly_female = i in sexw.index and sexw.loc[i].get("female", 0) > sexw.loc[i].get("male", 0)
                en = male or female
                if mostly_female and not male_c:
                    en = female
                en_f = female if (female and female != en) else ""
                source = "wikidata"
            else:
                en, en_f, source = rule, "", "rule"
        rows.append({"id": i, "he": he, "en": en, "en_f": en_f, "en_source": source})
    pd.DataFrame(rows).to_csv(paths.MODEL / "domains" / "first_name.csv", index=False)

    # birth cohort lookup from single-year age
    ages = np.arange(18, 101)
    pd.DataFrame({"age": ages.astype(str), "value": [cohort_of_birth_year(REFERENCE_YEAR - a) for a in ages]}).to_csv(
        paths.MODEL / "lookups" / "birth_cohort.csv", index=False
    )
    pd.DataFrame({"id": COHORT_IDS, "en": COHORT_IDS, "he": COHORT_IDS}).to_csv(paths.MODEL / "domains" / "birth_cohort.csv", index=False)
    log(f"  first names: {len(cpt):,} rows, {len(ids):,} distinct names")


# ---------------------------------------------------------------------------
# English forms

WD_MALE, WD_FEMALE = "Q12308941", "Q11879590"


def wikidata_candidates() -> dict[tuple[str, str], list[tuple[str, int, int]]]:
    """(Hebrew name, sex | 'any') -> English labels of Wikidata given-name items with that
    Hebrew label, as (label without accents, number of items, smallest Q number)."""
    import unicodedata

    src = load_sources()["wikidata_given_names"]
    path = src.raw_path(src.files[0])
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    df = pd.DataFrame(data).dropna(subset=["en"])
    df["en_ascii"] = df["en"].map(lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode())
    df = df[df["en_ascii"].str.fullmatch(r"[A-Za-z][A-Za-z' -]*")]
    df["q"] = df["item"].str[1:].astype(int)
    df["sex"] = df["type"].map({WD_MALE: "male", WD_FEMALE: "female"}).fillna("any")
    out = {}
    for (he, sex), g in pd.concat([df, df.assign(sex="any")]).groupby(["he", "sex"]):
        c = g.groupby("en_ascii").agg(n=("q", "size"), q=("q", "min"))
        out[(he, sex)] = [(lbl, int(r.n), int(r.q)) for lbl, r in c.iterrows()]
    return out


def _lev(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def closest(cands: list[tuple[str, int, int]], target: str) -> str | None:
    """The candidate spelling nearest the rule-based transliteration (edit distance relative to
    length; ties: more Wikidata items, then the oldest item). This prefers Israeli forms
    (Yehuda, Moshe, Yaakov) over English biblical ones (Judah, Moses, Jacob) for Hebrew names,
    and Arabic forms (Omar, Yusuf) for names of Arab citizens."""
    if not cands:
        return None
    norm = lambda x: x.lower().replace("'", "").replace(" ", "").replace("-", "")  # noqa: E731
    t = norm(target)
    return min(cands, key=lambda c: (_lev(norm(c[0]), t) / max(len(t), 1), -c[1], c[2]))[0]


# Fallback Hebrew -> Latin transliteration for names without a Wikidata form.

_MAP = {
    "א": "", "ב": "v", "ג": "g", "ד": "d", "ה": "h", "ו": "o", "ז": "z", "ח": "ch", "ט": "t",
    "י": "y", "כ": "ch", "ך": "ch", "ל": "l", "מ": "m", "ם": "m", "נ": "n", "ן": "n", "ס": "s",
    "ע": "", "פ": "f", "ף": "f", "צ": "tz", "ץ": "tz", "ק": "k", "ר": "r", "ש": "sh", "ת": "t",
}


_VOWELS = set("aeiou")


def transliterate(name: str, style: str = "hebrew") -> str:
    """Rough unvocalised transliteration: letters map to consonants, ו/י between consonants
    become o/i, a final ה/א is "a", and a default vowel ("e" for Hebrew names, "a" for
    Arabic names written in Hebrew) is inserted between consonants that would otherwise
    touch. Used only when Wikidata has no English form."""
    s = name.replace("'", "'")
    s = s.replace("ג'", "J").replace("ז'", "Zh").replace("צ'", "Ch").replace("ח'", "Kh").replace("ד'", "Dh").replace("ת'", "Th")
    default_vowel = "a" if style == "arabic" else "e"
    chunks: list[str] = []
    for i, ch in enumerate(s):
        last = i == len(s) - 1
        nxt = s[i + 1] if not last else ""
        if ch in "JZCKDT" and ch.isupper():
            chunks.append(ch.lower() if ch not in "ZCKDT" else {"Z": "zh", "C": "ch", "K": "kh", "D": "dh", "T": "th"}[ch])
        elif ch == "h":
            continue
        elif ch == "ב":
            chunks.append("b" if i == 0 else "v")
        elif ch == "כ":
            chunks.append("k" if i == 0 else "ch")
        elif ch == "פ":
            chunks.append("p" if i == 0 else "f")
        elif ch == "ו":
            if i == 0 or nxt == "ו" or (i > 0 and s[i - 1] == "ו"):
                chunks.append("w" if style == "arabic" else "v")
            else:
                chunks.append("u" if style == "arabic" else "o")
        elif ch == "י":
            chunks.append("y" if i == 0 or nxt == "י" else "i")
        elif ch in "אע":
            chunks.append("a" if i == 0 or last or style == "arabic" else "")
        elif ch == "ה":
            chunks.append("a" if last else "h")
        else:
            chunks.append(_MAP.get(ch, ch if ch.isascii() else ""))
    out = ""
    for c in chunks:
        if not c:
            continue
        if out and out[-1] not in _VOWELS and c[0] not in _VOWELS and not (out.endswith("y") or c == "y"):
            out += default_vowel
        out += c
    out = out.replace("vv", "v").replace("ii", "i").replace("oo", "o")
    return out[:1].upper() + out[1:] if out else name
