"""Ecological inference of each locality's Jewish religiosity mix from its 2022 vote.

How religious a locality's Jewish population is cannot be read from any published table
below the district level, but it leaves a strong footprint in election results
(UTJ and Shas for Haredim, Religious Zionism for Datiim, Yesh Atid/Labor/Meretz for the
secular...). With INES 2022 giving P(party | religiosity) for Jewish voters, each
locality's vote is a mixture of five known party profiles, and the mixture weights
(the religiosity shares among *voters*) are estimated by EM with a Dirichlet prior
centred on the national mix:

    r[k, p] = x[k] M[k, p] / sum_k' x[k'] M[k', p]
    x[k]   <- (sum_p v[p] r[k, p] + a * prior[k]) / (sum_p v[p] + a)

Voter shares are converted to adult-population shares by dividing by INES turnout by
religiosity and renormalising. Output: data/interim/religiosity_by_locality.csv.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .. import paths

JEWISH_RELIGIOSITY = ["haredi", "dati", "masorti_dati", "masorti", "hiloni"]
PARTIES = [
    "likud",
    "yesh_atid",
    "national_unity",
    "religious_zionism",
    "shas",
    "utj",
    "yisrael_beiteinu",
    "labor",
    "meretz",
    "jewish_home",
    "other",
]
ARAB_PARTIES = ["hadash_taal", "raam", "balad"]
PRIOR_STRENGTH = 50.0  # pseudo-voters pulling each locality toward the national mix
# Party profiles differ between places (secular voters in Beer Sheva vote Likud more than in
# Tel Aviv), so the mixture model is misspecified and would be overconfident for big
# localities. The likelihood is tempered: at most MAX_EFFECTIVE_VOTES count as data.
MAX_EFFECTIVE_VOTES = 200.0
PROFILE_PSEUDOCOUNT = 0.5


def party_profiles(ines: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """M[k, p] = P(party p | religiosity k) among Jewish voters; turnout[k]; national voter mix."""
    j = ines[(ines["sector"] == "jewish") & ines["religiosity"].isin(JEWISH_RELIGIOSITY) & ines["w_panel2"].notna()].copy()
    j["party"] = j["vote_2022"].map(lambda v: v if v in PARTIES else ("other" if isinstance(v, str) and v not in ("did_not_vote", "blank") else None))
    voters = j[j["party"].notna()]
    m = (
        voters.groupby(["religiosity", "party"])["w_panel2"].sum().unstack(fill_value=0.0)
        .reindex(index=JEWISH_RELIGIOSITY, columns=PARTIES, fill_value=0.0)
    )
    m = m + PROFILE_PSEUDOCOUNT
    M = (m.T / m.sum(axis=1)).T.values
    t = j[j["turnout_2022"].notna()]
    turnout = (
        t.assign(v=(t["turnout_2022"] == "voted").astype(float) * t["w_panel2"])
        .groupby("religiosity")[["v", "w_panel2"]].sum()
        .reindex(JEWISH_RELIGIOSITY)
    )
    turnout = (turnout["v"] / turnout["w_panel2"]).values
    national_voters = voters.groupby("religiosity")["w_panel2"].sum().reindex(JEWISH_RELIGIOSITY).values
    return M, turnout, national_voters / national_voters.sum()


def em_mixture(v: np.ndarray, M: np.ndarray, prior: np.ndarray, strength: float = PRIOR_STRENGTH, iters: int = 500) -> np.ndarray:
    x = prior.copy()
    n = v.sum()
    for _ in range(iters):
        mix = x @ M  # P(party) under current x
        r = (x[:, None] * M) / np.where(mix > 0, mix, 1)[None, :]
        new = (r @ v + strength * prior) / (n + strength)
        if np.abs(new - x).max() < 1e-10:
            x = new
            break
        x = new
    return x


def build(log=print) -> pd.DataFrame:
    ines = pd.read_csv(paths.interim_path("ines_2022"))
    cec = pd.read_csv(paths.interim_path("cec2022_localities"))
    M, turnout, national_voters = party_profiles(ines)

    strata = cec.pivot_table(index="locality", columns="stratum", values="valid", aggfunc="sum").fillna(0)
    has_arab = strata.get("arab_stations", pd.Series(0, index=strata.index)) > 0
    rows = []
    for loc, g in cec.groupby("locality"):
        pick = "other_stations" if has_arab.get(loc, False) else "all"
        r = g[g["stratum"] == pick]
        if r.empty:
            continue
        r = r.iloc[0]
        v = np.array([r[p] for p in PARTIES[:-1]] + [r["other_party"] + sum(r[a] for a in ARAB_PARTIES)], dtype=float)
        if v.sum() < 20:  # tiny or Arab-only localities carry no usable signal
            continue
        v_eff = v * min(1.0, MAX_EFFECTIVE_VOTES / v.sum())
        x_voters = em_mixture(v_eff, M, national_voters)
        pop = x_voters / turnout
        pop /= pop.sum()
        rows.append({"locality": int(loc), "jewish_valid_votes": v.sum(), **dict(zip(JEWISH_RELIGIOSITY, pop))})
    out = pd.DataFrame(rows)
    out.to_csv(paths.interim_path("religiosity_by_locality"), index=False)
    pd.DataFrame(M, index=JEWISH_RELIGIOSITY, columns=PARTIES).to_csv(paths.interim_path("ines_party_profiles"))
    pd.Series(turnout, index=JEWISH_RELIGIOSITY).to_csv(paths.interim_path("ines_turnout_by_religiosity"))
    log(f"  religiosity EI: {len(out)} localities")
    return out
