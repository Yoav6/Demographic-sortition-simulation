"""Origin (country of origin x generation) and, for third-generation Israelis, self-identified
ancestry.  See docs/methodology/origin.md.

Jews: IPF over age band x religiosity x immigrant-share bucket x origin, with margins
  * the frame's Jewish adults by age band, religiosity and bucket;
  * CBS Jews by country of origin, generation and age (2020, aged forward to 2024);
  * INES 2022: religiosity x continent group (Asia-Africa / Europe-America / FSU / Israel),
    raked to the CBS continent totals;
  * the share of 1990+ immigrants in each bucket of localities (CBS local-authorities file),
    applied to FSU-born immigrants and rescaled to their national total.
Others: FSU-born immigrants or their Israeli-born children, split by age like FSU-origin Jews.
Arabs and Druze: "native" (no origin attribute).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .. import paths
from .common import AGE_BAND_IDS, AGE_BANDS, MAX_AGE, ipf
from .frame import load_authorities

AA = ["morocco", "iraq", "iran", "yemen", "ethiopia", "algeria_tunisia", "libya", "egypt", "turkey", "india", "syria_lebanon", "asia_other", "africa_other"]
EA = ["poland", "romania", "bulgaria_greece", "germany_austria", "czech_hungary", "france", "uk", "europe_other", "north_america", "argentina", "latin_america_other"]
COUNTRIES = ["fsu"] + AA + EA
GROUP_OF = {**{c: "AA" for c in AA}, **{c: "EA" for c in EA}, "fsu": "FSU", "israel": "IL3"}
CGROUPS = ["AA", "EA", "FSU", "IL3"]
REL = ["haredi", "dati", "masorti_dati", "masorti", "hiloni"]
BUCKET_CUTS = [5, 10, 20, 30]  # percent of 1990+ immigrants in the local authority
BUCKETS = ["imm_lt5", "imm_5_10", "imm_10_20", "imm_20_30", "imm_30plus"]
YEARS_SINCE_TABLE = 4  # table is the 2020 average, the model refers to the end of 2024

ORIGIN_IDS = ["israel_3gen"] + [f"{c}_{g}" for c in COUNTRIES for g in ("immigrant", "second_gen")] + ["native"]


def origin_id(origin: str, generation: str) -> str:
    return "israel_3gen" if origin == "israel" else f"{origin}_{generation}"


def country_of(origin_id_: str) -> str:
    if origin_id_ == "israel_3gen":
        return "israel"
    for suffix in ("_immigrant", "_second_gen"):
        if origin_id_.endswith(suffix):
            return origin_id_[: -len(suffix)]
    return origin_id_


def _adult_band_shares(df: pd.DataFrame) -> np.ndarray:
    """Persons in a set of (age_from, age_to) bands -> counts in the frame bands after ageing."""
    dens = np.zeros(MAX_AGE + 1)
    for r in df.itertuples(index=False):
        hi = MAX_AGE if pd.isna(r.age_to) else int(r.age_to)
        ages = np.arange(int(r.age_from), hi + 1)
        w = np.ones(len(ages)) if not pd.isna(r.age_to) else 0.85 ** (ages - ages[0])
        dens[ages] += r.thousands * w / w.sum()
    shifted = np.zeros(MAX_AGE + 1)
    shifted[YEARS_SINCE_TABLE:] = dens[: MAX_AGE + 1 - YEARS_SINCE_TABLE]
    shifted[MAX_AGE] += dens[MAX_AGE + 1 - YEARS_SINCE_TABLE :].sum()
    return np.array([shifted[lo : min(hi, MAX_AGE) + 1].sum() for lo, hi in AGE_BANDS])


def national_origin_by_band() -> pd.DataFrame:
    tab = pd.read_csv(paths.interim_path("cbs_origin_age"))
    rows = {}
    for (o, g), d in tab.groupby(["origin", "generation"]):
        rows[origin_id(o, g)] = _adult_band_shares(d)
    return pd.DataFrame(rows, index=AGE_BAND_IDS).fillna(0.0)  # thousands, by band x origin id


def bucket_of(pct: float) -> str:
    if pd.isna(pct):
        return BUCKETS[0]
    return BUCKETS[int(np.digitize(pct, BUCKET_CUTS))]


def jewish_adults_by_band_rel_bucket(frame: pd.DataFrame, bucket_of_loc: pd.Series) -> np.ndarray:
    cpt = pd.read_csv(paths.CPTS / "religiosity.csv")
    prof = pd.read_csv(paths.MODEL / "lookups" / "locality_profile.csv", dtype={"locality": str})
    jf = frame[frame["group"] == "jewish"].copy()
    jf["locality_profile"] = jf["locality"].map(dict(zip(prof["locality"], prof["value"])))
    jf["bucket"] = jf["locality"].map(bucket_of_loc).fillna(BUCKETS[0])
    jc = cpt[cpt["group"] == "jewish"]
    exact = jc[jc["locality_profile"] != "*"]
    m = jf.merge(exact, on=["sex", "age_band", "locality_profile"], how="left", suffixes=("", "_c"))
    missing = m["value"].isna()
    if missing.any():
        back = jc[jc["locality_profile"] == "*"]
        fill = jf[jf.index.isin(m[missing].index)].merge(back.drop(columns=["locality_profile"]), on=["sex", "age_band"])
        m = pd.concat([m[~missing], fill], ignore_index=True)
    m["n"] = m["count"] * m["p"]
    t = m.groupby(["age_band", "value", "bucket"])["n"].sum()
    out = np.zeros((len(AGE_BAND_IDS), len(REL), len(BUCKETS)))
    for (a, r, b), v in t.items():
        out[AGE_BAND_IDS.index(a), REL.index(r), BUCKETS.index(b)] = v
    return out


def ines_rel_by_group(nat_group_totals: np.ndarray, rel_totals: np.ndarray) -> np.ndarray:
    ines = pd.read_csv(paths.interim_path("ines_2022"))
    j = ines[(ines["group"] == "jewish") & ines["religiosity"].isin(REL) & ines["birthplace"].notna()]
    to_group = {
        "asia_africa": "AA",
        "israel_father_asia_africa": "AA",
        "europe_america": "EA",
        "israel_father_europe_america": "EA",
        "fsu": "FSU",
        "israel_father_fsu": "FSU",
        "israel_father_israel": "IL3",
    }
    j = j.assign(cg=j["birthplace"].map(to_group))
    t = j.pivot_table(index="religiosity", columns="cg", values="w_panel1", aggfunc="sum", fill_value=0.0)
    t = t.reindex(index=REL, columns=CGROUPS, fill_value=0.0).values + 2.0  # smoothing
    # keep INES's association, impose the model's religiosity totals and CBS group totals
    return ipf(t, [((0,), rel_totals), ((1,), nat_group_totals / nat_group_totals.sum() * rel_totals.sum())])


def build(log=print) -> None:
    frame = pd.read_csv(paths.MODEL / "frame.csv", dtype={"locality": str})
    loc = pd.read_csv(paths.MODEL / "domains" / "locality.csv", dtype={"id": str})
    la = load_authorities().set_index("code")
    pct = loc["authority"].map(lambda a: la["pct_immigrants_1990"].get(int(a)) if str(a).strip() not in ("", "nan") else np.nan)
    bucket_of_loc = pd.Series([bucket_of(p) for p in pct], index=loc["id"])
    lk = paths.MODEL / "lookups"
    pd.DataFrame({"locality": loc["id"], "value": bucket_of_loc.values}).to_csv(lk / "immigrant_bucket.csv", index=False)
    pd.DataFrame({"id": BUCKETS, "en": BUCKETS, "he": BUCKETS}).to_csv(paths.MODEL / "domains" / "immigrant_bucket.csv", index=False)

    N = jewish_adults_by_band_rel_bucket(frame, bucket_of_loc)  # [a, r, b]
    nat = national_origin_by_band()  # thousands [band, origin id]
    og = [o for o in ORIGIN_IDS if o in nat.columns]
    nat = nat[og]
    nat_counts = nat.div(nat.sum(axis=1), axis=0).mul(N.sum(axis=(1, 2)), axis=0).values  # [a, og]

    og_group = np.array([CGROUPS.index(GROUP_OF[country_of(o)]) for o in og])
    fsu_imm = np.array([o == "fsu_immigrant" for o in og])
    group_totals = np.array([nat_counts[:, og_group == k].sum() for k in range(4)])
    M = ines_rel_by_group(group_totals, N.sum(axis=(0, 2)))  # [r, cg]

    # bucket margin for FSU-born immigrants: proportional to adults x immigrant share
    shares = pd.DataFrame({"bucket": bucket_of_loc, "pct": pct.values}).groupby("bucket")["pct"].mean().reindex(BUCKETS).fillna(0) / 100
    fsu_total = nat_counts[:, fsu_imm].sum()
    raw = N.sum(axis=(0, 1)) * shares.values
    t_fsu = raw / raw.sum() * fsu_total
    T = np.stack([N.sum(axis=(0, 1)) - t_fsu, t_fsu], axis=1)  # [b, fi]

    A, R, B, G, O = N.shape[0], N.shape[1], N.shape[2], 4, len(og)
    seed = np.zeros((A, R, B, G, 2, O))
    p_og_given_a = nat_counts / nat_counts.sum(axis=1, keepdims=True)
    for k in range(O):
        seed[:, :, :, og_group[k], int(fsu_imm[k]), k] = N * p_og_given_a[:, k][:, None, None]
    fitted = ipf(
        seed,
        [((0, 1, 2), N), ((0, 5), nat_counts), ((1, 3), M), ((2, 4), T)],
        iters=1000,
    )
    cond = fitted.sum(axis=(3, 4))  # [a, r, b, og]
    rows = []
    for ai, a in enumerate(AGE_BAND_IDS):
        for ri, r in enumerate(REL):
            for bi, b in enumerate(BUCKETS):
                cell = cond[ai, ri, bi]
                if cell.sum() <= 0:
                    cell = p_og_given_a[ai]
                cell = cell / cell.sum()
                for k, o in enumerate(og):
                    if cell[k] > 1e-7:
                        rows.append(("jewish", a, r, b, o, cell[k]))

    # Others: FSU-born or Israeli-born children of FSU-born parents, by age like FSU Jews
    fsu_imm_band = nat["fsu_immigrant"].values
    fsu_2nd_band = nat["fsu_second_gen"].values
    for ai, a in enumerate(AGE_BAND_IDS):
        tot = fsu_imm_band[ai] + fsu_2nd_band[ai]
        p_imm = fsu_imm_band[ai] / tot if tot > 0 else 1.0
        rows.append(("other", a, "*", "*", "fsu_immigrant", p_imm))
        if p_imm < 1:
            rows.append(("other", a, "*", "*", "fsu_second_gen", 1 - p_imm))
    for g in ("muslim", "christian_arab", "druze"):
        rows.append((g, "*", "*", "*", "native", 1.0))
    cpt = pd.DataFrame(rows, columns=["group", "age_band", "religiosity", "immigrant_bucket", "value", "p"])
    cpt.to_csv(paths.CPTS / "origin.csv", index=False)
    write_origin_domain()
    build_ancestry(log)
    imp = fitted.sum(axis=(0, 1, 2, 3, 4))
    top = sorted(zip(og, imp / imp.sum()), key=lambda x: -x[1])[:6]
    log("  origin: " + ", ".join(f"{o} {p:.3f}" for o, p in top))


ANCESTRY = ["ashkenazi", "mizrahi", "mixed", "israeli_only", "not_applicable"]

# country id -> (Hebrew name, Hebrew origin adjective, English name, English adjective)
COUNTRY_NAMES = {
    "fsu": ("ברית המועצות לשעבר", "ברית המועצות לשעבר", "the former USSR", "former-Soviet"),
    "morocco": ("מרוקו", "מרוקאי", "Morocco", "Moroccan"),
    "iraq": ("עיראק", "עיראקי", "Iraq", "Iraqi"),
    "iran": ("איראן", "פרסי", "Iran", "Iranian"),
    "yemen": ("תימן", "תימני", "Yemen", "Yemenite"),
    "ethiopia": ("אתיופיה", "אתיופי", "Ethiopia", "Ethiopian"),
    "algeria_tunisia": ("תוניסיה או אלג'יריה", "תוניסאי-אלג'יראי", "Tunisia or Algeria", "Tunisian or Algerian"),
    "libya": ("לוב", "לובי", "Libya", "Libyan"),
    "egypt": ("מצרים", "מצרי", "Egypt", "Egyptian"),
    "turkey": ("טורקיה", "טורקי", "Turkey", "Turkish"),
    "india": ("הודו", "הודי", "India", "Indian"),
    "syria_lebanon": ("סוריה או לבנון", "סורי-לבנוני", "Syria or Lebanon", "Syrian or Lebanese"),
    "asia_other": ("ארץ אחרת באסיה", "אסייתי", "another Asian country", "Asian"),
    "africa_other": ("ארץ אחרת באפריקה", "אפריקאי", "another African country", "African"),
    "poland": ("פולין", "פולני", "Poland", "Polish"),
    "romania": ("רומניה", "רומני", "Romania", "Romanian"),
    "bulgaria_greece": ("בולגריה או יוון", "בולגרי-יווני", "Bulgaria or Greece", "Bulgarian or Greek"),
    "germany_austria": ("גרמניה או אוסטריה", "גרמני-אוסטרי", "Germany or Austria", "German or Austrian"),
    "czech_hungary": ("צ'כיה, סלובקיה או הונגריה", "מרכז-אירופי", "Czechia, Slovakia or Hungary", "Central European"),
    "france": ("צרפת", "צרפתי", "France", "French"),
    "uk": ("בריטניה", "בריטי", "the UK", "British"),
    "europe_other": ("ארץ אחרת באירופה", "אירופי", "another European country", "European"),
    "north_america": ("צפון אמריקה", "אמריקאי", "North America", "North American"),
    "argentina": ("ארגנטינה", "ארגנטינאי", "Argentina", "Argentine"),
    "latin_america_other": ("ארץ אחרת באמריקה הלטינית", "לטינו-אמריקאי", "another Latin American country", "Latin American"),
}


def write_origin_domain() -> None:
    rows = [{"id": "israel_3gen", "en": "third-generation Israeli", "he": "דור שלישי בישראל", "he_f": "", "country": "israel", "generation": "third_gen"}]
    for c in COUNTRIES:
        he, adj, en, adj_en = COUNTRY_NAMES[c]
        rows.append({"id": f"{c}_immigrant", "en": f"immigrant from {en}", "he": f"עולה מ{he}", "he_f": "", "country": c, "generation": "immigrant"})
        rows.append({"id": f"{c}_second_gen", "en": f"Israeli-born, of {adj_en} origin", "he": f"יליד ישראל, ממוצא {adj}", "he_f": f"ילידת ישראל, ממוצא {adj}", "country": c, "generation": "second_gen"})
    rows.append({"id": "native", "en": "not applicable", "he": "לא רלוונטי", "he_f": "", "country": "", "generation": "native"})
    pd.DataFrame(rows).to_csv(paths.MODEL / "domains" / "origin.csv", index=False)
    gen = pd.DataFrame({"origin": [r["id"] for r in rows], "value": [r["generation"] for r in rows]})
    gen.to_csv(paths.MODEL / "lookups" / "generation.csv", index=False)


def build_ancestry(log=print) -> None:
    """Self-identified ancestry of third-generation Israeli Jews (INES 2022), by religiosity;
    everyone else gets 'not_applicable' (their origin country is shown instead)."""
    ines = pd.read_csv(paths.interim_path("ines_2022"))
    t3 = ines[(ines["birthplace"] == "israel_father_israel") & ines["religiosity"].isin(REL)]
    t3 = t3.assign(anc=t3["ancestry"].where(t3["ancestry"].isin(["ashkenazi", "mizrahi", "mixed", "israeli_only"]), None)).dropna(subset=["anc"])
    overall = t3.groupby("anc")["w_panel1"].sum().reindex(ANCESTRY[:4]).fillna(0)
    rows = []
    for r in REL:
        cell = t3[t3["religiosity"] == r].groupby("anc")["w_panel1"].sum().reindex(ANCESTRY[:4]).fillna(0)
        p = (cell + 15 * overall / overall.sum()) / (cell.sum() + 15)
        for a, v in p.items():
            rows.append(("israel_3gen", r, a, float(v)))
    rows.append(("*", "*", "not_applicable", 1.0))
    pd.DataFrame(rows, columns=["origin", "religiosity", "value", "p"]).to_csv(paths.CPTS / "ancestry.csv", index=False)
