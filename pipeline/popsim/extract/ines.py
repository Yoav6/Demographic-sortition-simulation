"""INES 2022 (Israel National Election Studies) microdata -> tidy, harmonised table.

Output data/interim/ines_2022.csv, one row per respondent, with our category ids:
  sector (jewish/arab), group (jewish/muslim/christian_or_other/unknown), sex,
  age, age_group (INES bands), education (INES 9 levels -> our ids),
  religiosity (INES v144: same 5-point scale for Jews and Arabs),
  birthplace (v513), ancestry (self-identification v131, Jews only),
  immigration_year, spending (v139, household spending relative to average),
  turnout_2022 / vote_2022 (post-election wave F1/F2),
  news_freq (v601b), social_news_freq (v506), weights.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyreadstat

from .. import paths
from ..sources import load_sources

RELIGIOSITY_JEWS = {1: "haredi", 2: "dati", 3: "masorti_dati", 4: "masorti", 5: "hiloni"}
RELIGIOSITY_ARABS = {1: "very_religious", 2: "religious", 3: "religious", 4: "not_so_religious", 5: "not_religious"}
EDUCATION = {
    1: "none_primary",
    2: "none_primary",
    3: "partial_secondary",
    4: "secondary_no_bagrut",
    5: "bagrut",
    6: "post_secondary",
    7: "post_secondary",  # partial academic degree
    8: "ba",
    9: "ma_plus",
}
BIRTHPLACE = {
    1: "asia_africa",
    2: "europe_america",
    3: "fsu",
    4: "israel_father_israel",
    5: "israel_father_asia_africa",
    6: "israel_father_europe_america",
    7: "israel_father_fsu",
}
ANCESTRY = {1: "ashkenazi", 2: "mizrahi", 3: "mizrahi", 5: "mixed", 24: "russian", 28: "ethiopian", 30: "mizrahi", 31: "mizrahi", 36: "mizrahi"}
VOTE_2022 = {
    1: "likud",
    2: "yesh_atid",
    3: "national_unity",
    4: "religious_zionism",
    5: "shas",
    6: "utj",
    7: "yisrael_beiteinu",
    8: "labor",
    9: "meretz",
    10: "jewish_home",
    11: "hadash_taal",
    12: "raam",
    13: "balad",
    16: "other_party",
    17: "other_party",
    18: "other_party",
    19: "other_party",
    20: "other_party",
    21: "other_party",
    96: "blank",
}
FREQ = {1: "never", 2: "weekly", 3: "few_times_week", 4: "daily", 5: "several_daily"}


def extract() -> pd.DataFrame:
    src = load_sources()["ines_2022"]
    df, _meta = pyreadstat.read_sav(src.raw_path(next(f for f in src.files if f.path.endswith(".sav"))))
    out = pd.DataFrame({"id": df["ID"].astype(int)})
    out["sector"] = df["sector"].map({1: "jewish", 2: "arab"})
    religion = df["v143_code"].map({1: "jewish", 2: "muslim", 5: "christian_or_other"})
    out["group"] = np.where(out["sector"] == "jewish", "jewish", religion.fillna("unknown"))
    out.loc[(out["sector"] == "jewish") & (religion == "christian_or_other"), "group"] = "other"
    out["sex"] = df["sex"].map({1: "male", 2: "female"})
    out["age"] = pd.to_numeric(df["age"], errors="coerce")
    out["age_group"] = df["age_group"].map({1: "18-22", 2: "23-29", 3: "30-39", 4: "40-49", 5: "50-59", 6: "60-69", 7: "70-79", 8: "80+"})
    out["education"] = df["educ"].map(EDUCATION)
    rel = df["v144"]
    out["religiosity"] = np.where(out["sector"] == "jewish", rel.map(RELIGIOSITY_JEWS), rel.map(RELIGIOSITY_ARABS))
    out["birthplace"] = df["v513"].map(BIRTHPLACE)
    out["ancestry"] = df["v131"].map(ANCESTRY).where(out["sector"] == "jewish")
    out.loc[(out["sector"] == "jewish") & df["v131"].isin([6, 10, 11, 12, 14]), "ancestry"] = "israeli_only"
    out["immigration_year"] = pd.to_numeric(df["v134"], errors="coerce")
    out["spending"] = df["v139"].map({1: "much_below", 2: "below", 3: "average", 4: "above", 5: "much_above"})
    out["turnout_2022"] = df["F1"].map({1: "voted", 2: "did_not_vote", 3: "voted"})
    out["vote_2022"] = df["F2"].map(VOTE_2022)
    out.loc[out["turnout_2022"] == "did_not_vote", "vote_2022"] = "did_not_vote"
    out["news_freq"] = df["v601b"].map(FREQ)
    out["social_news_freq"] = df["v506"].map({0: "no_social_media", **FREQ})
    out["religious_school"] = df["v137"].map({1: False, 2: True})
    for w in ("w_panel1", "w_panel2"):
        out[w] = pd.to_numeric(df[w], errors="coerce")
    out.to_csv(paths.interim_path("ines_2022"), index=False)
    return out


# INES 2025 (off-cycle study, March-April 2025): media questions v612-v614
SOURCES_2025 = {1: "sites", 2: "tv", 3: "radio", 4: "print", 5: "facebook", 6: "instagram", 7: "tiktok", 8: "whatsapp", 9: "telegram", 10: "x"}
CHANNELS_2025 = {1: "kan11", 2: "news12", 3: "news13", 4: "channel14", 5: "al_jazeera", 6: "makan33", 7: "none", 8: "other"}


def extract_2025() -> pd.DataFrame:
    """Output data/interim/ines_2025.csv: sector, sex, age group, education, religiosity (as for
    2022), 2022 vote (recalled, v706), political news frequency (v612), the sources used in the
    past week (v613: src_<source>, 0/1) and the TV channels watched regularly (v614: ch_<channel>,
    0/1). Sources and channels were asked only of people who follow the news at all."""
    src = load_sources()["ines_2025"]
    df, _meta = pyreadstat.read_sav(src.raw_path(next(f for f in src.files if f.path.endswith(".sav"))))
    out = pd.DataFrame({"id": df["resp_id"]})
    out["sector"] = df["sector"].map({1: "jewish", 2: "arab"})
    out["sex"] = df["gender"].map({1: "male", 2: "female"})
    out["age"] = pd.to_numeric(df["age"], errors="coerce")
    out["age_group"] = df["agegroup5"].map({1: "18-29", 2: "30-39", 3: "40-49", 4: "50-59", 5: "60+"})
    out["education"] = df["educ"].map(EDUCATION)
    rel = df["religiosity"]
    out["religiosity"] = np.where(out["sector"] == "jewish", rel.map(RELIGIOSITY_JEWS), rel.map(RELIGIOSITY_ARABS))
    out["vote_2022"] = df["v706"].map({**VOTE_2022, 30: "other_party", 94: "did_not_vote", 95: "too_young"})
    out["news_freq"] = df["v612"].map(FREQ)
    asked = out["news_freq"].isin(["weekly", "few_times_week", "daily", "several_daily"])
    for k, name in SOURCES_2025.items():
        out[f"src_{name}"] = np.where(asked, df[f"v613_{k}"].notna().astype(int), np.where(out["news_freq"] == "never", 0, np.nan))
    for k, name in CHANNELS_2025.items():
        out[f"ch_{name}"] = np.where(asked, df[f"v614_{k}"].notna().astype(int), np.nan)
    out["mode"] = df["SURVEY_MODE"].map({1: "online", 2: "phone"})
    out["w"] = pd.to_numeric(df["w_sample"], errors="coerce")
    out.to_csv(paths.interim_path("ines_2025"), index=False)
    return out
