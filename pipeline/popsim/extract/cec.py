"""Central Elections Committee results, 25th Knesset (2022) -> tidy tables.

data/interim/cec2022_localities.csv  one row per locality and stratum:
    locality, stratum (all | arab_stations | other_stations), eligible, voters, invalid,
    valid, <party id> votes...
Polling stations in which Arab parties won a majority of valid votes are "arab_stations";
splitting mixed cities this way lets Jewish and Arab voting patterns be calibrated separately.
"""

from __future__ import annotations

import pandas as pd

from .. import paths
from ..sources import load_sources

ARAB_PARTIES = ["hadash_taal", "raam", "balad"]
DOUBLE_ENVELOPES = 9999  # "מעטפות חיצוניות": soldiers, diplomats, hospitals, prisons...


def party_map() -> pd.DataFrame:
    return pd.read_csv(paths.MANUAL / "elections" / "knesset25_parties.csv")


def _tidy(df: pd.DataFrame, letter_to_party: dict[str, str]) -> pd.DataFrame:
    base = {
        "locality": df["סמל ישוב"].astype(int),
        "eligible": df["בזב"],
        "voters": df["מצביעים"],
        "invalid": df["פסולים"],
        "valid": df["כשרים"],
    }
    out = pd.DataFrame(base)
    letters = [c for c in df.columns if c not in ("סמל ועדה", "ברזל", "שם ישוב", "סמל ישוב", "קלפי", "ריכוז", "שופט", "בזב", "מצביעים", "פסולים", "כשרים")]
    for party in sorted(set(letter_to_party.values())) + ["other_party"]:
        cols = [c for c in letters if letter_to_party.get(c, "other_party") == party]
        out[party] = df[cols].sum(axis=1) if cols else 0
    return out


def extract() -> pd.DataFrame:
    src = load_sources()["cec_knesset25"]
    raw = {f.path: src.raw_path(f) for f in src.files}
    pm = party_map()
    letter_to_party = dict(zip(pm["letter"], pm["party"]))
    b = pd.read_csv(raw["expb.csv"], encoding="utf-8-sig")
    stations = _tidy(b, letter_to_party)
    stations = stations[stations["locality"] != DOUBLE_ENVELOPES]
    arab = stations[ARAB_PARTIES].sum(axis=1) > 0.5 * stations["valid"].clip(lower=1)
    stations["stratum"] = arab.map({True: "arab_stations", False: "other_stations"})
    num = [c for c in stations.columns if c not in ("locality", "stratum")]
    by_stratum = stations.groupby(["locality", "stratum"], as_index=False)[num].sum()
    total = stations.groupby("locality", as_index=False)[num].sum()
    total["stratum"] = "all"
    out = pd.concat([total, by_stratum], ignore_index=True).sort_values(["locality", "stratum"])
    out.to_csv(paths.interim_path("cec2022_localities"), index=False)

    c = pd.read_csv(raw["expc.csv"], encoding="utf-8-sig")
    nat = _tidy(c, letter_to_party)
    national = nat.drop(columns=["locality"]).sum()
    national.to_frame("value").to_csv(paths.interim_path("cec2022_national"))
    return out
