"""The population frame: eligible citizens (18+, living in Israel) by
locality x population group x sex x age band.  See docs/methodology/frame.md.

Steps
 1. Locality populations (CBS localities file, end of 2024): Jews-and-others and Arabs.
 2. Split each into Jews/others and Muslims/Christian Arabs/Druze with the shares of the
    locality's local authority (CBS local-authorities file 2024).
 3. Age-sex structure per local authority and group, by IPF: seed = national single-year
    age-sex profile of the group (Statistical Abstract table 2.3); margins = the authority's
    group totals, its age-group shares and its men/women totals.
 4. Citizenship: East Jerusalem Arabs and Golan Druze are mostly permanent residents,
    not citizens. Their adult counts are replaced by eligible voters on the 2022 roll
    (Arab-majority polling stations in Jerusalem; the four Golan Druze villages).
 5. Bedouin "tribe" localities have no CBS population; their adults are the 2022 eligible
    voters, with the age-sex profile of the Bedouin regional councils.
 6. Keep ages 18+ and aggregate to the frame's age bands.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pyproj import Transformer

from .. import paths
from ..sources import load_sources
from .common import AGE_BAND_IDS, AGE_BANDS, GROUPS, MAX_AGE, SEXES, age_to_band, ipf

AGES = np.arange(0, MAX_AGE + 1)
GOLAN_DRUZE = {4201: "מג'דל שמס", 4203: "מסעדה", 4001: "בוקעאתא", 4502: "עין קנייא"}
JERUSALEM = 3000
ARAB_PARTIES_2022 = ["ום", "עם", "ד"]  # Hadash-Ta'al, Ra'am, Balad
BEDOUIN_COUNCILS = {"אל קסום", "נווה מדבר"}

# Age groups in the local-authorities file and the ages they cover.
LA_AGE_GROUPS = [
    ("בני 4-0", 0, 4),
    ("בני 9-5", 5, 9),
    ("בני 14-10", 10, 14),
    ("בני 19-15", 15, 19),
    ("בני 29-20", 20, 29),
    ("בני 44-30", 30, 44),
    ("בני 59-45", 45, 59),
    ("בני 64-60", 60, 64),
    ("בני 65 ומעלה", 65, MAX_AGE),
]


# ---------------------------------------------------------------------------
# national single-year profiles


def _single_year(df: pd.DataFrame, population: str, sex: str, shape_from: np.ndarray | None = None) -> np.ndarray:
    """Persons (thousands) by single year 0..MAX_AGE for one population and sex."""
    d = df[(df.population == population) & (df.sex == sex)]
    out = np.full(len(AGES), np.nan)
    singles = d[d.age_from == d.age_to]
    out[singles.age_from.values] = singles.thousands.values
    # fill open-ended / missing ages from the bands
    for r in d[d.age_from != d.age_to].itertuples():
        hi = MAX_AGE if pd.isna(r.age_to) else int(r.age_to)
        ages = np.arange(int(r.age_from), hi + 1)
        known = ~np.isnan(out[ages])
        if known.all():
            continue
        remaining = r.thousands - np.nansum(out[ages][known])
        missing = ages[~known]
        if shape_from is not None and shape_from[missing].sum() > 0:
            w = shape_from[missing]
        else:  # geometric decline over the open-ended tail
            w = 0.82 ** (missing - missing[0])
        out[missing] = max(remaining, 0) * w / w.sum()
    return np.nan_to_num(out)


def national_profiles(pop_age: pd.DataFrame) -> dict[str, np.ndarray]:
    """group -> array [sex, age] of persons (thousands), 2024 average."""
    total_shape = {s: _single_year(pop_age, "total", s) for s in SEXES}
    out = {}
    for group, population in [("jewish", "jews"), ("muslim", "muslims"), ("christian_arab", "arab_christians"), ("druze", "druze")]:
        out[group] = np.stack([_single_year(pop_age, population, s, total_shape[s]) for s in SEXES])
    jo = np.stack([_single_year(pop_age, "jews_and_others", s, total_shape[s]) for s in SEXES])
    out["other"] = np.clip(jo - out["jewish"], 0, None)
    return out


# ---------------------------------------------------------------------------
# inputs


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def load_localities() -> pd.DataFrame:
    src = load_sources()["cbs_localities_2024"]
    df = pd.read_excel(src.raw_path(src.files[0]))
    out = pd.DataFrame(
        {
            "code": df["סמל יישוב"].astype(int),
            "name_he": df["שם יישוב"].astype(str).str.strip().str.replace(r"\s*-\s*", "-", regex=True).str.replace(r"\s+", " ", regex=True),
            "name_en": df["שם יישוב באנגלית"].astype(str).str.strip().str.replace(r"\s*-\s*", "-", regex=True).str.replace(r"\s+", " ", regex=True),
            "district_code": _num(df["סמל מחוז"]),
            "district_he": df["שם מחוז"].astype(str).str.strip(),
            "subdistrict_code": _num(df["סמל נפה"]),
            "subdistrict_he": df["שם נפה"].astype(str).str.strip(),
            "natural_region": _num(df["אזור טבעי"]),
            "municipal_status": df["שם מעמד מונציפאלי"].astype(str).str.strip(),
            "locality_religion": _num(df["דת יישוב"]),
            "locality_form": _num(df["צורת יישוב שוטפת"]),
            "israelis": _num(df["סך הכל ישראלים 2024"]).fillna(0),
            "jews_and_others": _num(df["יהודים ואחרים"]).fillna(0),
            "arabs": _num(df["ערבים"]).fillna(0),
            "coords": df["קואורדינטות"],
            "authority_code": _num(df["סמל רשות מקומית"]),
            "authority_he": df["שם רשות מקומית"].astype(str).str.strip(),
        }
    )
    # coordinates are ITM east/north concatenated (6+6 digits)
    xy = out["coords"].dropna().astype("int64").astype(str).str.zfill(12)
    out.loc[xy.index, "itm_x"] = xy.str[:6].astype(float)
    out.loc[xy.index, "itm_y"] = xy.str[6:].astype(float)
    tr = Transformer.from_crs("EPSG:2039", "EPSG:4326", always_xy=True)
    ok = out["itm_x"].notna()
    lon, lat = tr.transform(out.loc[ok, "itm_x"].values, out.loc[ok, "itm_y"].values)
    out.loc[ok, "lat"] = np.round(lat, 5)
    out.loc[ok, "lon"] = np.round(lon, 5)
    return out.drop(columns=["coords"])


def _squash(s: str) -> str:
    return " ".join(str(s).split())


def _find_col(header_rows: list[tuple], *needles: str) -> int:
    """Index of the first column whose (multi-row) header contains all needles.

    Header rows hold group titles only above a group's first column, so the group title
    is carried forward across the group.
    """
    carried = [""] * len(header_rows)
    last = len(header_rows) - 1
    for j in range(len(header_rows[0])):
        parts = []
        for i, r in enumerate(header_rows):
            v = r[j]
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                if i < last:
                    carried[i] = _squash(v)
                    # a new upper-level title resets the carried lower-level titles
                    for k in range(i + 1, last):
                        carried[k] = ""
                parts.append(_squash(v))
            elif i < last and carried[i]:
                parts.append(carried[i])
        text = " ".join(parts)
        if all(_squash(n) in text for n in needles):
            return j
    raise KeyError(f"column with {needles} not found")


def load_authorities() -> pd.DataFrame:
    src = load_sources()["cbs_local_authorities_2024"]
    raw = pd.read_excel(src.raw_path(src.files[0]), sheet_name="נתונים פיזיים ונתוני אוכלוסייה ", header=None)
    hdr = [tuple(raw.iloc[i]) for i in (1, 3, 4)]
    cols = {
        "code": _find_col(hdr, "סמל הרשות"),
        "israelis": _find_col(hdr, "סך כל הישראלים"),
        "pct_jo": _find_col(hdr, "יהודים ואחרים (אחוזים"),
        "pct_jews_of_jo": _find_col(hdr, "יהודים  (אחוזים מתוך יהודים ואחרים)"),
        "pct_arabs": _find_col(hdr, "ערבים (אחוזים"),
        "pct_muslim_of_arabs": _find_col(hdr, "מוסלמים (אחוזים"),
        "pct_christian_of_arabs": _find_col(hdr, "נוצרים (אחוזים"),
        "pct_druze_of_arabs": _find_col(hdr, "דרוזים (אחוזים"),
        "men": _find_col(hdr, 'סה"כ גברים בסוף השנה'),
        "women": _find_col(hdr, 'סה"כ נשים בסוף השנה'),
        "ses_cluster": _find_col(hdr, "מדד חברתי-כלכלי", "אשכול"),
        "periphery_cluster": _find_col(hdr, "מדד פריפריאליות", "אשכול"),
        "avg_wage": _find_col(hdr, "כלל בעלי הכנסה", "שכר ממוצע"),
        "pct_immigrants_1990": _find_col(hdr, "אחוז עולי 1990"),
    }
    for label, _lo, _hi in LA_AGE_GROUPS:
        cols[f"age:{label}"] = _find_col(hdr, label)
    for k, label in [("single", "רווקים"), ("married", "נשואים"), ("divorced", "גרושים"), ("widowed", "אלמנים")]:
        cols[f"marital:{k}"] = _find_col(hdr, "מצב משפחתי", label)
    data = raw.iloc[5:, list(cols.values())]
    data.columns = list(cols.keys())
    data = data[_num(data["code"]).notna()].copy()
    for c in data.columns:
        data[c] = _num(data[c])
    data["code"] = data["code"].astype(int)
    return data.reset_index(drop=True)


def cec_special_counts() -> dict:
    """Eligible voters (2022 roll) used for the citizenship adjustments."""
    src = load_sources()["cec_knesset25"]
    raw = {f.path: src.raw_path(f) for f in src.files}
    c = pd.read_csv(raw["expc.csv"], encoding="utf-8-sig")
    b = pd.read_csv(raw["expb.csv"], encoding="utf-8-sig")
    jlm = b[b["סמל ישוב"] == JERUSALEM].copy()
    jlm["arab_votes"] = jlm[ARAB_PARTIES_2022].sum(axis=1)
    arab_boxes = jlm[jlm["arab_votes"] > 0.5 * jlm["כשרים"].clip(lower=1)]
    # Arab citizens also vote outside Arab-majority stations; scale up by the share of
    # Arab-party votes cast in the Arab stations.
    share_in_boxes = arab_boxes["arab_votes"].sum() / jlm["arab_votes"].sum()
    jerusalem_arab_eligible = arab_boxes["בזב"].sum() / share_in_boxes
    golan = {code: int(c.loc[c["סמל ישוב"] == code, "בזב"].sum()) for code in GOLAN_DRUZE}
    tribes = c[c["שם ישוב"].astype(str).str.contains("שבט")][["סמל ישוב", "שם ישוב", "בזב"]]
    return {
        "jerusalem_arab_eligible": float(jerusalem_arab_eligible),
        "golan_druze_eligible": golan,
        "tribes": dict(zip(tribes["סמל ישוב"].astype(int), tribes["בזב"].astype(int))),
    }


# ---------------------------------------------------------------------------
# estimation


def group_counts(loc: pd.DataFrame, la: pd.DataFrame) -> pd.DataFrame:
    """Persons (all ages) by locality and group."""
    m = loc.merge(la, left_on="authority_code", right_on="code", how="left", suffixes=("", "_la"))
    jews_share = (m["pct_jews_of_jo"] / 100).fillna(1.0).clip(0, 1)
    arab_shares = m[["pct_muslim_of_arabs", "pct_christian_of_arabs", "pct_druze_of_arabs"]].fillna(0) / 100
    tot = arab_shares.sum(axis=1)
    arab_shares = arab_shares.div(tot.where(tot > 0, 1.0), axis=0)
    arab_shares.loc[tot == 0, "pct_muslim_of_arabs"] = 1.0
    out = pd.DataFrame(
        {
            "code": m["code"],
            "jewish": m["jews_and_others"] * jews_share,
            "other": m["jews_and_others"] * (1 - jews_share),
            "muslim": m["arabs"] * arab_shares["pct_muslim_of_arabs"],
            "christian_arab": m["arabs"] * arab_shares["pct_christian_of_arabs"],
            "druze": m["arabs"] * arab_shares["pct_druze_of_arabs"],
        }
    )
    return out


def authority_profiles(gc: pd.DataFrame, loc: pd.DataFrame, la: pd.DataFrame, nat: dict[str, np.ndarray]) -> dict:
    """authority code -> {group: array[sex, age] of shares summing to 1}."""
    nat_share = {g: a / a.sum() for g, a in nat.items()}
    gc = gc.merge(loc[["code", "authority_code"]], on="code")
    totals = gc.groupby("authority_code")[GROUPS].sum()
    la = la.set_index("code")
    out = {}
    for auth, row in totals.iterrows():
        present = [g for g in GROUPS if row[g] > 0.5]
        if not present:
            continue
        seed = np.stack([row[g] * nat_share[g] for g in present])  # [g, sex, age]
        margins: list = [((0,), np.array([row[g] for g in present]))]
        total = seed.sum()
        info = la.loc[auth] if auth in la.index else None
        if info is not None:
            pcts = np.array([info[f"age:{lbl}"] for lbl, _, _ in LA_AGE_GROUPS], dtype=float)
            if np.isfinite(pcts).all() and pcts.sum() > 0:
                band_of_age = np.zeros(len(AGES), dtype=int)
                for k, (_, lo, hi) in enumerate(LA_AGE_GROUPS):
                    band_of_age[lo : hi + 1] = k
                # aggregate cells into the authority's age groups via an extra axis
                target = pcts / pcts.sum() * total
                seed4 = np.zeros(seed.shape + (len(LA_AGE_GROUPS),))
                for k in range(len(LA_AGE_GROUPS)):
                    mask = band_of_age == k
                    seed4[:, :, mask, k] = seed[:, :, mask]
                men, women = info["men"], info["women"]
                ms = [((0,), margins[0][1]), ((3,), target)]
                if np.isfinite(men) and np.isfinite(women) and men + women > 0:
                    ms.append(((1,), np.array([men, women]) / (men + women) * total))
                fitted = ipf(seed4, ms).sum(axis=3)
                seed = fitted
        out[int(auth)] = {g: seed[i] / seed[i].sum() for i, g in enumerate(present)}
    return out


def build(log=print) -> pd.DataFrame:
    pop_age = pd.read_csv(paths.interim_path("cbs_pop_age"))
    nat = national_profiles(pop_age)
    loc = load_localities()
    la = load_authorities()
    special = cec_special_counts()
    gc = group_counts(loc, la)
    prof = authority_profiles(gc, loc, la, nat)
    nat_share = {g: a / a.sum() for g, a in nat.items()}

    bedouin_auth = set(loc.loc[loc["authority_he"].isin(BEDOUIN_COUNCILS), "authority_code"].dropna().astype(int))
    bedouin_profile = None
    for a in bedouin_auth:
        if a in prof and "muslim" in prof[a]:
            p = prof[a]["muslim"]
            bedouin_profile = p if bedouin_profile is None else bedouin_profile + p
    bedouin_profile = bedouin_profile / bedouin_profile.sum()

    adult = AGES >= 18
    band_index = {b: i for i, b in enumerate(AGE_BAND_IDS)}
    band_of_age = np.array([band_index[age_to_band(a)] if a >= 18 else -1 for a in AGES])

    def adult_bands(profile: np.ndarray, persons: float) -> np.ndarray:
        """[sex, band] adults from an all-ages profile scaled to `persons` (all ages)."""
        cells = profile * persons
        out = np.zeros((2, len(AGE_BANDS)))
        for s in range(2):
            np.add.at(out[s], band_of_age[adult], cells[s, adult])
        return out

    records = []
    loc_i = loc.set_index("code")
    for r in gc.itertuples(index=False):
        auth = loc_i.at[r.code, "authority_code"]
        auth = int(auth) if pd.notna(auth) else None
        for g in GROUPS:
            persons = getattr(r, g)
            if persons <= 0.5:
                continue
            profile = prof.get(auth, {}).get(g, nat_share[g])
            cells = adult_bands(profile, persons)
            adults = cells.sum()
            # citizenship adjustments
            if r.code == JERUSALEM and g in ("muslim", "christian_arab"):
                arab_adults_total = sum(
                    adult_bands(prof[auth][gg], getattr(r, gg)).sum() for gg in ("muslim", "christian_arab")
                )
                cells *= special["jerusalem_arab_eligible"] / arab_adults_total
            elif r.code in GOLAN_DRUZE and g == "druze":
                cells *= special["golan_druze_eligible"][r.code] / adults
            for s, sex in enumerate(SEXES):
                for k, band in enumerate(AGE_BAND_IDS):
                    if cells[s, k] > 0:
                        records.append((str(r.code), g, sex, band, cells[s, k]))

    # Bedouin tribe localities: adults = eligible voters (2022), Bedouin age-sex profile
    adult_profile = np.zeros((2, len(AGE_BANDS)))
    for s in range(2):
        np.add.at(adult_profile[s], band_of_age[adult], bedouin_profile[s, adult])
    adult_profile /= adult_profile.sum()
    tribe_codes = set(loc.loc[loc["locality_form"] == 460, "code"])
    for code, eligible in special["tribes"].items():
        if code not in tribe_codes:
            continue
        for s, sex in enumerate(SEXES):
            for k, band in enumerate(AGE_BAND_IDS):
                records.append((str(code), "muslim", sex, band, eligible * adult_profile[s, k]))

    frame = pd.DataFrame(records, columns=["locality", "group", "sex", "age_band", "count"])
    frame["count"] = frame["count"].round(3)
    frame = frame[frame["count"] > 0]

    out = paths.MODEL / "frame.csv"
    frame.to_csv(out, index=False)
    log(f"  frame: {len(frame):,} rows, {frame['count'].sum():,.0f} eligible citizens, {frame['locality'].nunique()} localities")
    _write_locality_domain(loc, la, set(frame["locality"]), bedouin_auth)
    pd.DataFrame(
        [{"key": "jerusalem_arab_eligible", "value": special["jerusalem_arab_eligible"]}]
        + [{"key": f"golan_druze_eligible:{k}", "value": v} for k, v in special["golan_druze_eligible"].items()]
    ).to_csv(paths.interim_path("frame_adjustments"), index=False)
    return frame


def _write_locality_domain(loc: pd.DataFrame, la: pd.DataFrame, used: set[str], bedouin_auth: set[int]) -> None:
    sector = pd.read_csv(paths.MANUAL / "localities" / "sector_localities.csv", dtype={"code": int})
    sector_of = dict(zip(sector["code"], sector["sector"]))
    la_i = la.set_index("code")
    rows = []
    for r in loc.itertuples(index=False):
        if str(r.code) not in used:
            continue
        auth = int(r.authority_code) if pd.notna(r.authority_code) else None
        info = la_i.loc[auth] if auth in la_i.index else None
        bedouin = r.locality_form == 460 or (auth in bedouin_auth) or sector_of.get(r.code) == "bedouin"
        name_en = r.name_en.title() if r.name_en.isupper() else r.name_en
        rows.append(
            {
                "id": str(r.code),
                "en": name_en,
                "he": r.name_he,
                "district": int(r.district_code) if pd.notna(r.district_code) else "",
                "subdistrict": int(r.subdistrict_code) if pd.notna(r.subdistrict_code) else "",
                "form": int(r.locality_form) if pd.notna(r.locality_form) else "",
                "authority": auth or "",
                "authority_he": r.authority_he if auth else "",
                "ses_cluster": int(info["ses_cluster"]) if info is not None and pd.notna(info["ses_cluster"]) else "",
                "periphery_cluster": int(info["periphery_cluster"]) if info is not None and pd.notna(info["periphery_cluster"]) else "",
                "special": "bedouin" if bedouin else sector_of.get(r.code, ""),
                "lat": r.lat if pd.notna(r.lat) else "",
                "lon": r.lon if pd.notna(r.lon) else "",
            }
        )
    out = paths.MODEL / "domains" / "locality.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values("id", key=lambda s: s.astype(int)).to_csv(out, index=False)
