"""Vote in the 2022 (25th) Knesset election, including abstention. See docs/methodology/vote.md.

Helper nodes (hidden): vote_age (age in 2022 group; under 18 then = too young), vote_education
(3 levels), vote_origin (continent of origin; third generation by self-identified ancestry),
vote_area (Jewish and "other" citizens: their locality's religiosity profile; Arab and Druze
citizens: their locality, or the Arab-majority polling stations of a mixed city).

Jewish and "other" citizens: a weighted multinomial logit on INES 2022 (religiosity, age,
education, origin) whose intercepts are then raked, for each locality profile, to the official
results of the Jewish polling stations in that profile's localities - abstention included, with
the profile's adults (20+ at the end of 2024, i.e. 18+ in November 2022) as the denominator.
Arab and Druze citizens: the official result of their own area, abstention included.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .. import paths
from ..model_spec import load_spec
from .joint import joint
from .socioeconomic import write_cpt

PARTIES = ["likud", "yesh_atid", "religious_zionism", "national_unity", "shas", "utj", "yisrael_beiteinu", "labor",
           "meretz", "jewish_home", "raam", "hadash_taal", "balad", "other_party"]
OUTCOMES = PARTIES + ["did_not_vote"]
VALUES = OUTCOMES + ["too_young"]
JEW_R = ["haredi", "dati", "masorti_dati", "masorti", "hiloni"]
AGES = ["y", "m", "o"]  # 18-29, 30-49, 50+ in November 2022 (20-31, 32-51, 52+ at the end of 2024)
EDU = ["low", "mid", "academic"]
ORIGINS = ["AA", "EA", "FSU", "IL3_ashkenazi", "IL3_mizrahi", "IL3_other"]
ARAB_GROUPS = ["muslim", "christian_arab", "druze"]
RIDGE = 1.0
MAX_TURNOUT = 0.97

EDU_OF = {"no_diploma": "low", "primary": "low", "secondary": "low", "bagrut": "mid", "post_secondary": "mid",
          "other_diploma": "mid", "ba": "academic", "ma": "academic", "phd": "academic"}
INES_EDU = {"none_primary": "low", "partial_secondary": "low", "secondary_no_bagrut": "low", "bagrut": "mid",
            "post_secondary": "mid", "ba": "academic", "ma_plus": "academic"}
INES_AGE = {"18-22": "y", "23-29": "y", "30-39": "m", "40-49": "m", "50-59": "o", "60-69": "o", "70-79": "o", "80+": "o"}
INES_ORIGIN = {"asia_africa": "AA", "israel_father_asia_africa": "AA", "europe_america": "EA",
               "israel_father_europe_america": "EA", "fsu": "FSU", "israel_father_fsu": "FSU"}
ANCESTRY_ORIGIN = {"ashkenazi": "IL3_ashkenazi", "mizrahi": "IL3_mizrahi"}


def vote_age(age: int) -> str:
    if age <= 19:
        return "too_young"
    return "y" if age <= 31 else "m" if age <= 51 else "o"


# ---------------------------------------------------------------------------
# helper nodes

def build_helpers(log=print) -> None:
    lk = paths.MODEL / "lookups"
    ages = np.arange(18, 101)
    pd.DataFrame({"age": ages.astype(str), "value": [vote_age(a) for a in ages]}).to_csv(lk / "vote_age.csv", index=False)
    pd.DataFrame(list(EDU_OF.items()), columns=["education", "value"]).to_csv(lk / "vote_education.csv", index=False)

    from .origin import AA, EA, country_of

    rows = []
    for o in load_spec().node("origin").value_ids():
        c = country_of(o)
        if o == "native":
            rows.append((o, "*", "native", 1.0))
        elif o == "israel_3gen":
            for anc in ("ashkenazi", "mizrahi", "mixed", "israeli_only", "not_applicable"):
                rows.append((o, anc, ANCESTRY_ORIGIN.get(anc, "IL3_other"), 1.0))
        else:
            rows.append((o, "*", "AA" if c in AA else "EA" if c in EA else "FSU", 1.0))
    pd.DataFrame(rows, columns=["origin", "ancestry", "value", "p"]).to_csv(paths.CPTS / "vote_origin.csv", index=False)

    areas = arab_areas()
    druze = set(druze_localities())
    frame = pd.read_csv(paths.MODEL / "frame.csv", dtype={"locality": str})
    prof = pd.read_csv(lk / "locality_profile.csv", dtype={"locality": str}).set_index("locality")["value"]
    combos = frame[["group", "locality"]].drop_duplicates()
    rows = []
    for r in combos.itertuples(index=False):
        if r.group == "druze" and int(r.locality) not in druze:
            # Druze outside Druze-majority localities vote like Druze, not like their Arab neighbours
            area = "a:druze"
        elif r.group in ARAB_GROUPS:
            area = f"a:{r.locality}" if int(r.locality) in areas.index else "a:national"
        else:
            area = f"j:{prof[r.locality]}"
        rows.append((r.group, r.locality, area, 1.0))
    va = pd.DataFrame(rows, columns=["group", "locality", "value", "p"])
    va.to_csv(paths.CPTS / "vote_area.csv", index=False)
    ids = sorted(va["value"].unique())
    pd.DataFrame({"id": ids, "en": ids, "he": ids}).to_csv(paths.MODEL / "domains" / "vote_area.csv", index=False)
    log(f"  vote helpers ({len(ids)} vote areas)")


# ---------------------------------------------------------------------------
# official results

def _cec() -> pd.DataFrame:
    return pd.read_csv(paths.interim_path("cec2022_localities"))


def druze_localities(threshold: float = 0.8) -> list[int]:
    """Localities whose adults are mostly Druze."""
    frame = pd.read_csv(paths.MODEL / "frame.csv")
    adults = frame.groupby(["locality", "group"])["count"].sum().unstack(fill_value=0)
    share = adults.get("druze", 0) / adults.sum(axis=1)
    return [int(x) for x in share[share >= threshold].index]


def arab_areas() -> pd.DataFrame:
    """Votes of Arab and Druze citizens by locality: all stations of localities whose adults are
    mostly Arab or Druze, and the Arab-majority stations of mixed localities."""
    cec = _cec()
    frame = pd.read_csv(paths.MODEL / "frame.csv")
    adults = frame.groupby(["locality", "group"])["count"].sum().unstack(fill_value=0)
    arab_share = adults[[g for g in ARAB_GROUPS if g in adults]].sum(axis=1) / adults.sum(axis=1)
    rows = {}
    for loc, g in cec.groupby("locality"):
        share = arab_share.get(loc, 0.0)
        if share >= 0.8:
            pick = g[g["stratum"] == "all"]
        elif share > 0.0 and (g["stratum"] == "arab_stations").any():
            pick = g[g["stratum"] == "arab_stations"]
        else:
            continue
        if len(pick):
            rows[loc] = pick.iloc[0]
    return pd.DataFrame(rows).T.drop(columns=["locality", "stratum"]).astype(float)


def double_envelope_ratio() -> pd.Series:
    """Votes cast in "double envelopes" (soldiers, diplomats, hospital patients, prisoners...;
    9.7% of all votes in 2022) have no locality. Each party's votes everywhere are scaled up by
    its national ratio of double-envelope to polling-station votes, so national totals and
    turnout match the official count (people who voted that way are spread over the country in
    proportion to each party's station votes)."""
    national = pd.read_csv(paths.interim_path("cec2022_national"), index_col=0)["value"]
    stations = _cec().query("stratum == 'all'")[PARTIES].sum()
    return ((national.reindex(PARTIES).astype(float) - stations) / stations).clip(lower=0.0)


def jewish_votes() -> pd.DataFrame:
    """Votes of Jewish (and "other") citizens by locality: all stations of mostly Jewish
    localities, the non-Arab stations of mixed localities."""
    cec = _cec()
    frame = pd.read_csv(paths.MODEL / "frame.csv")
    adults = frame.groupby(["locality", "group"])["count"].sum().unstack(fill_value=0)
    arab_share = adults[[g for g in ARAB_GROUPS if g in adults]].sum(axis=1) / adults.sum(axis=1)
    rows = {}
    for loc, g in cec.groupby("locality"):
        share = arab_share.get(loc, 0.0)
        if share >= 0.8:
            continue
        pick = g[g["stratum"] == "other_stations"] if (g["stratum"] == "arab_stations").any() else g[g["stratum"] == "all"]
        if len(pick):
            rows[loc] = pick.iloc[0]
    return pd.DataFrame(rows).T.drop(columns=["locality", "stratum"]).astype(float)


# ---------------------------------------------------------------------------
# INES model

def ines_design() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    ines = pd.read_csv(paths.interim_path("ines_2022"))
    d = ines[ines["group"].isin(["jewish", "other"]) & ines["vote_2022"].isin(OUTCOMES) & ines["w_panel1"].notna()].copy()
    d["rel"] = d["religiosity"].where(d["religiosity"].isin(JEW_R))
    d.loc[d["group"] == "other", "rel"] = d.loc[d["group"] == "other", "rel"].fillna("hiloni")
    d["age3"] = d["age_group"].map(INES_AGE)
    d["edu3"] = d["education"].map(INES_EDU)
    org = d["birthplace"].map(INES_ORIGIN)
    il3 = d["birthplace"] == "israel_father_israel"
    org = org.where(~il3, d["ancestry"].map(ANCESTRY_ORIGIN).fillna("IL3_other"))
    org = org.where(d["group"] != "other", "FSU")
    d["org"] = org
    d = d.dropna(subset=["rel", "age3", "edu3", "org"])
    names = [f"rel={r}" for r in JEW_R] + [f"age={a}" for a in AGES] + [f"edu={e}" for e in EDU] + [f"org={o}" for o in ORIGINS]
    X = np.zeros((len(d), len(names)))
    for j, n in enumerate(names):
        var, val = n.split("=")
        col = {"rel": "rel", "age": "age3", "edu": "edu3", "org": "org"}[var]
        X[:, j] = (d[col] == val).to_numpy()
    y = d["vote_2022"].map({k: i for i, k in enumerate(OUTCOMES)}).to_numpy()
    w = d["w_panel1"].to_numpy()
    w = w / w.mean()
    return X, y, w, names


def fit_mnlogit(X: np.ndarray, y: np.ndarray, w: np.ndarray, K: int, ridge: float = RIDGE) -> tuple[np.ndarray, np.ndarray]:
    """Weighted multinomial logit with a ridge penalty on the slopes (not the intercepts).
    Returns (intercepts [K], coefficients [features, K])."""
    n, p = X.shape
    Y = np.zeros((n, K))
    Y[np.arange(n), y] = 1.0

    def unpack(theta):
        return theta[:K], theta[K:].reshape(p, K)

    def f(theta):
        b0, B = unpack(theta)
        eta = b0 + X @ B
        eta -= eta.max(axis=1, keepdims=True)
        logp = eta - np.log(np.exp(eta).sum(axis=1, keepdims=True))
        loss = -(w[:, None] * Y * logp).sum() + 0.5 * ridge * (B**2).sum()
        P = np.exp(logp)
        G = w[:, None] * (P - Y)
        g0 = G.sum(axis=0)
        gB = X.T @ G + ridge * B
        return loss, np.concatenate([g0, gB.ravel()])

    res = minimize(f, np.zeros(K + p * K), jac=True, method="L-BFGS-B", options={"maxiter": 2000})
    return unpack(res.x)


# ---------------------------------------------------------------------------
# calibration and table

def build(log=print) -> None:
    X, y, w, names = ines_design()
    K = len(OUTCOMES)
    b0, B = fit_mnlogit(X, y, w, K)
    coef = pd.DataFrame(B, index=names, columns=OUTCOMES)

    # the model's eligible Jewish/other adults by profile and cell
    W = joint(["locality_profile", "religiosity", "vote_age", "vote_education", "vote_origin"],
              where={"group": ["jewish", "other"]})
    W = W[W["vote_age"] != "too_young"]
    W = W[W["religiosity"].isin(JEW_R)]

    def eta(df: pd.DataFrame) -> np.ndarray:
        e = np.tile(b0, (len(df), 1))
        for col, var in (("religiosity", "rel"), ("vote_age", "age"), ("vote_education", "edu"), ("vote_origin", "org")):
            e += coef.reindex([f"{var}={v}" for v in df[col]]).fillna(0.0).to_numpy()
        return e

    # targets: votes per profile / eligible adults per profile
    de = double_envelope_ratio()
    jv = jewish_votes()
    jv[PARTIES] = jv[PARTIES] * (1 + de)
    prof = pd.read_csv(paths.MODEL / "lookups" / "locality_profile.csv").set_index("locality")["value"]
    jv["profile"] = [prof.get(int(loc), "national") for loc in jv.index]
    adults_by_prof = W.groupby("locality_profile")["w"].sum()
    votes = jv.groupby("profile")[PARTIES].sum()
    national_votes = votes.sum()
    rows = []
    report = []
    nat_rows = []
    for p_id, g in W.groupby("locality_profile"):
        n = g["w"].sum()
        v = votes.loc[p_id] if p_id in votes.index and p_id != "national" else national_votes * (n / adults_by_prof.sum())
        share = (v / n).clip(lower=0.0)
        if share.sum() > MAX_TURNOUT:
            share = share * MAX_TURNOUT / share.sum()
        target = np.append(share.reindex(PARTIES).to_numpy(), 1 - share.sum())
        e = eta(g)
        wt = g["w"].to_numpy()
        delta = np.zeros(K)
        for _ in range(500):
            P = np.exp(e + delta - (e + delta).max(axis=1, keepdims=True))
            P /= P.sum(axis=1, keepdims=True)
            m = (wt[:, None] * P).sum(axis=0) / wt.sum()
            step = np.where(target > 0, np.log(np.maximum(target, 1e-12) / np.maximum(m, 1e-300)), -50.0)
            delta += step
            if np.abs(m - target).max() < 1e-7:
                break
        report.append((p_id, float(np.abs(m - target).max())))
        # full grid of cells for this profile
        grid = pd.MultiIndex.from_product([JEW_R, AGES, EDU, ORIGINS], names=["religiosity", "vote_age", "vote_education", "vote_origin"]).to_frame(index=False)
        eg = eta(grid) + delta
        P = np.exp(eg - eg.max(axis=1, keepdims=True))
        P /= P.sum(axis=1, keepdims=True)
        nat_rows.append((P, grid, g, e + delta))
        for i, r in enumerate(grid.itertuples(index=False)):
            for k, o in enumerate(OUTCOMES):
                if P[i, k] > 1e-9:
                    rows.append((f"j:{p_id}", r.religiosity, r.vote_age, r.vote_education, r.vote_origin, o, P[i, k]))

    # fallback for a Jewish area without eligible adults in the model: the national pattern by age
    for a in AGES:
        num = np.zeros(K)
        den = 0.0
        for _P, _grid, g, e in nat_rows:
            sel = (g["vote_age"] == a).to_numpy()
            if not sel.any():
                continue
            Pg = np.exp(e[sel] - e[sel].max(axis=1, keepdims=True))
            Pg /= Pg.sum(axis=1, keepdims=True)
            num += (g["w"].to_numpy()[sel, None] * Pg).sum(axis=0)
            den += g["w"].to_numpy()[sel].sum()
        for k, o in enumerate(OUTCOMES):
            rows.append(("*", "*", a, "*", "*", o, num[k] / den))

    # Arab and Druze areas: the official result, by age group alike
    frame = pd.read_csv(paths.MODEL / "frame.csv")
    frame = frame[frame["group"].isin(ARAB_GROUPS) & (frame["age_band"] != "18-19")]
    adults = frame.groupby("locality")["count"].sum()
    areas = arab_areas()
    nat_v = pd.Series(0.0, index=PARTIES)
    nat_n = 0.0
    used = set(pd.read_csv(paths.CPTS / "vote_area.csv")["value"])
    for loc, r in areas.iterrows():
        n = adults.get(int(loc), 0.0)
        if n <= 0 or f"a:{int(loc)}" not in used:
            continue
        v = r.reindex(PARTIES).astype(float) * (1 + de)
        nat_v += v
        nat_n += n
        share = v / n
        if share.sum() > MAX_TURNOUT:
            share = share * MAX_TURNOUT / share.sum()
        for a in AGES:
            for o in PARTIES:
                if share[o] > 0:
                    rows.append((f"a:{int(loc)}", "*", a, "*", "*", o, share[o]))
            rows.append((f"a:{int(loc)}", "*", a, "*", "*", "did_not_vote", 1 - share.sum()))
    dl = [loc for loc in druze_localities() if loc in areas.index]
    druze_v = areas.loc[dl, PARTIES].astype(float).sum() * (1 + de)
    druze_n = sum(adults.get(loc, 0.0) for loc in dl)
    for area_id, share in (("a:national", nat_v / nat_n), ("a:druze", druze_v / druze_n)):
        if share.sum() > MAX_TURNOUT:
            share = share * MAX_TURNOUT / share.sum()
        for a in AGES:
            for o in PARTIES:
                if share[o] > 0:
                    rows.append((area_id, "*", a, "*", "*", o, share[o]))
            rows.append((area_id, "*", a, "*", "*", "did_not_vote", 1 - share.sum()))
    rows.append(("*", "*", "too_young", "*", "*", "too_young", 1.0))
    df = pd.DataFrame(rows, columns=["vote_area", "religiosity", "vote_age", "vote_education", "vote_origin", "value", "p"])
    write_cpt(df, "vote_2022")
    coef.assign(intercept=pd.Series(b0, index=OUTCOMES)).to_csv(paths.interim_path("ines_vote_logit"), index=True)
    worst = max(report, key=lambda x: x[1])
    log(f"  vote_2022: INES logit on {len(y)} respondents; {len(report)} profiles raked (worst residual {worst[1]:.1e}); "
        f"{len(areas)} Arab/Druze areas")
