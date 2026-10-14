"""ISOC-IL / Technion Media Consumption and Disinformation Survey 2024 -> tidy table.

Output data/interim/isoc_2024.csv, one row per respondent (805 Jewish, 200 Arab internet
users), with our category ids:
  sector (secular/traditional/religious/haredi/arab), religion (Arab respondents), sex,
  media_age (survey age groups), education (low/mid/academic, as vote_education),
  freq_<medium> for the seven media of question 1 (often/sometimes/rarely/never),
  preferred (question 2: the preferred one of the media the respondent uses),
  uses_<network> (question 3) and news_<network> (question 4) as 0/1, orientation (D5).
The first data row of each file holds the question wording and is dropped.
"""

from __future__ import annotations

import pandas as pd

from .. import paths
from ..sources import load_sources

MEDIA = {"Q1_1": "tv", "Q1_2": "radio", "Q1_3": "print", "Q1_4": "sites", "Q1_5": "social", "Q1_6": "search", "Q1_7": "podcasts"}
FREQ = {"אף פעם": "never", "לעיתים רחוקות": "rarely", "מדי פעם": "sometimes", "לעיתים קרובות": "often"}
NETWORKS = {1: "facebook", 2: "youtube", 3: "x", 4: "instagram", 5: "snapchat", 6: "whatsapp", 7: "linkedin", 8: "tiktok", 9: "telegram", 10: "pinterest"}
SECTOR = {"יהודי/ה חילוני/ת": "secular", "יהודי/ה מסורתי/ת": "traditional", "יהודי/ה דתי/ה": "religious", "יהודי/ה חרדי/ת": "haredi"}
RELIGION = {"ערבי/ה – מוסלמי/ת": "muslim", "ערבי/ה – נוצרי/ה": "christian_arab", "דרוזי/ת": "druze"}
AGE = {"18-24": "18_24", "25-30": "25_29", "31-39": "30_39", "40-49": "40_49", "50-64": "50_64", "65+": "65_plus"}
# yeshiva gedola / seminary: men as "no matriculation", women as post-secondary, as the model
# classifies Haredi men and women (see docs/methodology/media.md)
EDUCATION = {
    "בית ספר יסודי (עד כיתה ו׳)": "low",
    "חטיבת ביניים או בית ספר 8 שנתי (ח׳ או ט׳)": "low",
    "תיכונית, ללא תעודת בגרות": "low",
    "תיכונית, עם תעודת בגרות": "mid",
    "על תיכונית ללא תואר אקדמי": "mid",
    "תואר ראשון": "academic",
    "תואר שני או שלישי": "academic",
}
YESHIVA = "ישיבה גדולה או סמינר"
PREFERRED = {
    "טלוויזיה": "tv", "רדיו": "radio", "עיתונים מודפסים": "print", "אתרי אינטרנט או אפליקציות של ערוצי חדשות": "sites",
    "מדיה חברתית (כמו, פייסבוק, אינסטגרם, טיקטוק)": "social", "דרך גוגל או מנוע חיפוש אחר": "search", "פודקאסטים": "podcasts",
    "אחר (אנא פרט/י)": "other",
}
ORIENTATION = {"מאוד שמאלני/ת": 1, "-2": 2, "-3": 3, "-4": 4, "מאוד ימני/ת": 5}


def _read(path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", dtype=str).iloc[1:].reset_index(drop=True)


def extract() -> pd.DataFrame:
    src = load_sources()["isoc_media_survey_2024"]
    files = {f.path: src.raw_path(f) for f in src.files}
    parts = []
    for name in ("jewish.csv", "arab.csv"):
        d = _read(files[name])
        out = pd.DataFrame({"id": name[0] + d.iloc[:, 0].astype(str)})
        if name == "jewish.csv":
            out["sector"] = d["RELIGIOSITY"].map(SECTOR)
            out["religion"] = "jewish"
        else:
            out["sector"] = "arab"
            out["religion"] = d["RELIGIOSITY"].map(RELIGION)
        out["sex"] = d["D1"].map({"נקבה": "female", "זכר": "male"})
        out["media_age"] = d["AGEyears"].map(AGE)
        edu = d["D3"].map(EDUCATION)
        edu[d["D3"] == YESHIVA] = out["sex"].map({"male": "low", "female": "mid"})
        out["education"] = edu
        for q, m in MEDIA.items():
            out[f"freq_{m}"] = d[q].map(FREQ)
        out["preferred"] = d["Q2"].map(PREFERRED)
        for k, net in NETWORKS.items():
            out[f"uses_{net}"] = (d[f"Q3_{k}"] == "Checked").astype(int)
            out[f"news_{net}"] = (d[f"Q4_{k}"] == "Checked").astype(int)
        out["no_networks"] = (d["Q3_12"] == "Checked").astype(int)
        out["orientation"] = d["D5"].map(ORIENTATION)
        out["district"] = d["QquotaDistrict"]
        parts.append(out)
    out = pd.concat(parts, ignore_index=True)
    out.to_csv(paths.interim_path("isoc_2024"), index=False)
    return out
