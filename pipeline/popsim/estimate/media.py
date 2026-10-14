"""Media diet: internet use, how often the person follows political news, how often they get
news from each medium, the social networks they use and read news on, the TV news channels they
watch and their main printed newspaper. See docs/methodology/media.md.

    online          <- group, religiosity, sex, age band                (CBS Social Survey 2024)
    vote_bloc       <- vote_2022                                         (lookup)
    news_frequency  <- religiosity, vote_age, vote_education, vote_bloc  (INES 2022)
    media_age       <- age; media_sector <- religiosity                  (lookups: survey groups)
    news_<medium>   <- news_frequency, media_age, media_sector, sex, vote_education, online
                       (ISOC-IL 2024, tied to news_frequency through INES 2025)
    social_networks <- online, media_age, media_sector, sex, vote_education    (ISOC-IL 2024)
    news_networks   <- news_social, media_age, media_sector, within social_networks (ISOC-IL)
    tv_channels     <- news_tv, media_sector, vote_bloc, media_age   (INES 2025)
    news_websites   <- news_sites, media_sector, vote_bloc           (Agam Media Index 2024)
    newspaper       <- news_print, media_sector, media_age, vote_bloc (TGI; lean of the papers' websites)
    preferred_source <- the seven media, media_age, media_sector     (ISOC-IL 2024; logit)
"""

from __future__ import annotations

import itertools
import json
import math

import numpy as np
import pandas as pd

from .. import paths
from ..model_spec import load_spec
from .common import ipf
from .joint import joint
from .socioeconomic import by_population, expand, write_cpt
from scipy.optimize import brentq, minimize

from .vote import AGES, EDU, INES_AGE, INES_EDU, fit_mnlogit

ONLINE = ["social", "internet_only", "offline"]
NEWS = ["several_daily", "daily", "few_times_week", "weekly", "never"]
BLOCS = ["coalition", "opposition", "arab", "other", "did_not_vote", "too_young"]
BLOC_OF_PARTY = {
    "likud": "coalition", "religious_zionism": "coalition", "shas": "coalition", "utj": "coalition",
    "yesh_atid": "opposition", "national_unity": "opposition", "yisrael_beiteinu": "opposition", "labor": "opposition",
    "meretz": "opposition", "raam": "arab", "hadash_taal": "arab", "balad": "arab", "jewish_home": "other",
    "other_party": "other", "did_not_vote": "did_not_vote", "too_young": "too_young",
}
REL = ["haredi", "dati", "masorti_dati", "masorti", "hiloni", "very_religious", "religious", "not_so_religious", "not_religious"]

# --- the media surveys' groups -------------------------------------------------------------
MEDIA_AGES = ["18_24", "25_29", "30_39", "40_49", "50_64", "65_plus"]
SECTORS = ["secular", "traditional", "religious", "haredi", "arab"]
SECTOR_OF = {"hiloni": "secular", "masorti": "traditional", "masorti_dati": "traditional", "dati": "religious",
             "haredi": "haredi", "very_religious": "arab", "religious": "arab", "not_so_religious": "arab",
             "not_religious": "arab"}
LEVELS = ["often", "sometimes", "rarely", "never"]
MEDIA = ["tv", "radio", "print", "sites", "social", "search", "podcasts"]
INTERNET_MEDIA = {"sites", "social", "search", "podcasts"}
NETWORKS = ["whatsapp", "facebook", "youtube", "instagram", "telegram", "tiktok", "linkedin", "pinterest", "x", "snapchat"]
MESSAGING = {"whatsapp", "telegram"}
# INES 2025 question 613 (sources of political news in the past week) standing for each medium
INES_LINK = {"tv": ["tv"], "radio": ["radio"], "print": ["print"], "sites": ["sites"],
             "social": ["facebook", "instagram", "tiktok", "whatsapp", "telegram", "x"],
             "search": ["sites"], "podcasts": ["sites"]}
NF_SCORE = {"never": 0, "weekly": 1, "few_times_week": 2, "daily": 3, "several_daily": 4}
INES25_AGES = ["18-29", "30-39", "40-49", "50-59", "60+"]
# media age group -> INES 2025 age groups (50-64 spans two of them)
INES25_AGE_OF = {"18_24": {"18-29": 1.0}, "25_29": {"18-29": 1.0}, "30_39": {"30-39": 1.0}, "40_49": {"40-49": 1.0},
                 "50_64": {"50-59": 2 / 3, "60+": 1 / 3}, "65_plus": {"60+": 1.0}}
RIDGE = 1.0


def media_age_of(age: int) -> str:
    for hi, g in ((24, "18_24"), (29, "25_29"), (39, "30_39"), (49, "40_49"), (64, "50_64")):
        if age <= hi:
            return g
    return "65_plus"


def build_online(log=print) -> None:
    """Uses the internet and social networks / the internet only / neither (Social Survey:
    "used social networks in the last three months", with "does not use the internet")."""
    def loader(name: str) -> pd.DataFrame:
        from .survey import load

        d = load(name)
        d["online"] = d["social_networks"].map({"yes": "social", "no": "internet_only", "no_internet": "offline"})
        return d.drop(columns=["social_networks"])

    cond = by_population("social_networks", "online", ONLINE, loader=loader)
    write_cpt(expand(cond, "online"), "online")
    log("  online")


def build_vote_bloc(log=print) -> None:
    pd.DataFrame(list(BLOC_OF_PARTY.items()), columns=["vote_2022", "value"]).to_csv(
        paths.MODEL / "lookups" / "vote_bloc.csv", index=False
    )
    log("  vote_bloc")


def _ines(outcome: str, values: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    ines = pd.read_csv(paths.interim_path("ines_2022"))
    d = ines[ines[outcome].isin(values) & ines["religiosity"].isin(REL) & ines["w_panel1"].notna()].copy()
    d["age3"] = d["age_group"].map(INES_AGE)
    d["edu3"] = d["education"].map(INES_EDU)
    d["bloc"] = d["vote_2022"].map(BLOC_OF_PARTY)  # missing vote: no bloc dummy
    d = d.dropna(subset=["age3", "edu3"])
    names = [f"rel={r}" for r in REL] + [f"age={a}" for a in AGES] + [f"edu={e}" for e in EDU] + [f"bloc={b}" for b in BLOCS[:5]]
    X = np.zeros((len(d), len(names)))
    for j, n in enumerate(names):
        var, val = n.split("=")
        col = {"rel": "religiosity", "age": "age3", "edu": "edu3", "bloc": "bloc"}[var]
        X[:, j] = (d[col] == val).to_numpy()
    y = d[outcome].map({k: i for i, k in enumerate(values)}).to_numpy()
    w = d["w_panel1"].to_numpy()
    return X, y, w / w.mean(), names


def _expand_logit(b0: np.ndarray, B: np.ndarray, names: list[str], values: list[str]) -> pd.DataFrame:
    """The fitted logit as a table over religiosity x age x education x bloc. People too young
    to have voted in 2022 get no bloc effect, and the age effect of 18-29-year-olds."""
    coef = pd.DataFrame(B, index=names, columns=values)
    rows = []
    for rel, age, edu, bloc in itertools.product(REL, AGES + ["too_young"], EDU, BLOCS):
        e = b0.copy()
        e += coef.loc[f"rel={rel}"].to_numpy()
        e += coef.loc[f"age={'y' if age == 'too_young' else age}"].to_numpy()
        e += coef.loc[f"edu={edu}"].to_numpy()
        if f"bloc={bloc}" in coef.index:
            e += coef.loc[f"bloc={bloc}"].to_numpy()
        p = np.exp(e - e.max())
        p /= p.sum()
        rows += [(rel, age, edu, bloc, v, p[k]) for k, v in enumerate(values)]
    return pd.DataFrame(rows, columns=["religiosity", "vote_age", "vote_education", "vote_bloc", "value", "p"])


def build_news(log=print) -> None:
    """How often the person catches up on political news (INES 2022: logit on religiosity,
    age, education and 2022 vote bloc)."""
    X, y, w, names = _ines("news_freq", NEWS)
    b0, B = fit_mnlogit(X, y, w, len(NEWS))
    write_cpt(_expand_logit(b0, B, names, NEWS), "news_frequency")
    log(f"  news_frequency (INES 2022, {len(y)} respondents)")


def build_media_helpers(log=print) -> None:
    """The age groups and population groups of the media surveys, as lookups."""
    ages = load_spec().node("age").value_ids()
    pd.DataFrame({"age": ages, "value": [media_age_of(int(a)) for a in ages]}).to_csv(
        paths.MODEL / "lookups" / "media_age.csv", index=False)
    pd.DataFrame(list(SECTOR_OF.items()), columns=["religiosity", "value"]).to_csv(
        paths.MODEL / "lookups" / "media_sector.csv", index=False)
    log("  media_age, media_sector")


# --- ISOC-IL 2024 --------------------------------------------------------------------------

def isoc() -> pd.DataFrame:
    """ISOC respondents with known sex and education. "Internet only" = uses no social
    platform (messaging apps - WhatsApp, Telegram - aside), like the Social Survey's "does not
    use social networks". 23 respondents who never get news from social media yet ticked a social
    platform (mostly YouTube) as a place where they regularly read news are counted as not
    reading news there: the frequency question is taken as the primary answer."""
    d = pd.read_csv(paths.interim_path("isoc_2024"))
    d = d.dropna(subset=["sex", "education"]).copy()
    platforms = d[[f"uses_{n}" for n in NETWORKS if n not in MESSAGING]].sum(axis=1)
    d["online"] = np.where(platforms == 0, "internet_only", "social")
    never = d["freq_social"] == "never"
    for net in NETWORKS:
        if net not in MESSAGING:
            d.loc[never, f"news_{net}"] = 0
    return d


def _design(df: pd.DataFrame, extra: dict[str, list[str]] | None = None, online: bool = True) -> tuple[np.ndarray, list[str]]:
    """Main-effects design: age group, population group, sex, education, (internet only), and
    any extra categorical columns {column: levels, first = reference}."""
    cols: dict[str, np.ndarray] = {}
    for a in MEDIA_AGES[1:]:
        cols[f"age={a}"] = (df["media_age"] == a).to_numpy()
    for s in SECTORS[1:]:
        cols[f"sector={s}"] = (df["media_sector"] == s).to_numpy()
    cols["female"] = (df["sex"] == "female").to_numpy()
    for e in ("low", "academic"):
        cols[f"edu={e}"] = (df["vote_education"] == e).to_numpy()
    if online:
        cols["internet_only"] = (df["online"] == "internet_only").to_numpy()
    for col, levels in (extra or {}).items():
        for lv in levels[1:]:
            cols[f"{col}={lv}"] = (df[col] == lv).to_numpy()
    return np.column_stack(list(cols.values())).astype(float), list(cols)


def _predict(b0: np.ndarray, B: np.ndarray, X: np.ndarray) -> np.ndarray:
    eta = b0 + X @ B
    P = np.exp(eta - eta.max(axis=1, keepdims=True))
    return P / P.sum(axis=1, keepdims=True)


def _cells(online: list[str]) -> pd.DataFrame:
    """Every combination of the media nodes' demographic parents."""
    return pd.DataFrame(list(itertools.product(MEDIA_AGES, SECTORS, ["male", "female"], EDU, online)),
                        columns=["media_age", "media_sector", "sex", "vote_education", "online"])


def isoc_frequencies() -> dict[str, pd.DataFrame]:
    """P(frequency | age group, population group, sex, education, internet use) for each medium:
    a multinomial logit on the ISOC respondents (internet users; those who use no social
    network stand for the model's "internet but not social networks")."""
    d = isoc().rename(columns={"sector": "media_sector", "education": "vote_education"})
    X, _ = _design(d)
    cells = _cells(["social", "internet_only"])
    Xc, _ = _design(cells)
    out = {}
    for m in MEDIA:
        ok = d[f"freq_{m}"].notna().to_numpy()
        y = d.loc[ok, f"freq_{m}"].map({v: i for i, v in enumerate(LEVELS)}).to_numpy()
        b0, B = fit_mnlogit(X[ok], y, np.ones(int(ok.sum())), len(LEVELS), ridge=RIDGE)
        out[m] = pd.concat([cells, pd.DataFrame(_predict(b0, B, Xc), columns=LEVELS)], axis=1)
    return out


# --- INES 2025: medium use against political-news frequency ----------------------------------

def ines25() -> pd.DataFrame:
    d = pd.read_csv(paths.interim_path("ines_2025"))
    d["media_sector"] = d["religiosity"].map(SECTOR_OF)
    d["vote_education"] = d["education"].map(INES_EDU)
    d["bloc"] = d["vote_2022"].map(BLOC_OF_PARTY)
    return d.dropna(subset=["media_sector", "vote_education", "sex", "age_group", "w"])


def _ines25_design(df: pd.DataFrame) -> np.ndarray:
    cols = [df["nf_score"].to_numpy(dtype=float)]
    cols += [(df["age_group"] == a).to_numpy() for a in INES25_AGES[1:]]
    cols += [(df["media_sector"] == s).to_numpy() for s in SECTORS[1:]]
    cols += [(df["sex"] == "female").to_numpy(), (df["vote_education"] == "low").to_numpy(),
             (df["vote_education"] == "academic").to_numpy()]
    return np.column_stack(cols).astype(float)


def ines25_links() -> dict[str, pd.DataFrame]:
    """P(used the medium for political news in the past week | political-news frequency,
    age, population group, sex, education), from INES 2025: a weighted logit with the frequency
    as a linear score (once a week = 1 ... more than once a day = 4). People who hardly ever
    follow political news were not asked; their score (0) is extrapolated from the slope."""
    d = ines25()
    d = d[d["news_freq"].isin(NEWS[:4])].copy()
    d["nf_score"] = d["news_freq"].map(NF_SCORE)
    X = _ines25_design(d)
    w = (d["w"] / d["w"].mean()).to_numpy()
    grid = pd.DataFrame(list(itertools.product(NEWS, INES25_AGES, SECTORS, ["male", "female"], EDU)),
                        columns=["news_frequency", "age_group", "media_sector", "sex", "vote_education"])
    grid["nf_score"] = grid["news_frequency"].map(NF_SCORE)
    Xg = _ines25_design(grid)
    out = {}
    for m, items in INES_LINK.items():
        y = (d[[f"src_{i}" for i in items]].fillna(0).sum(axis=1) > 0).astype(int).to_numpy()
        b0, B = fit_mnlogit(X, y, w, 2, ridge=RIDGE)
        g = grid[["news_frequency", "age_group", "media_sector", "sex", "vote_education"]].copy()
        g["r"] = _predict(b0, B, Xg)[:, 1]
        # onto the media age groups
        rows = []
        for ma, mix in INES25_AGE_OF.items():
            part = sum(wt * g[g["age_group"] == ag].set_index(["news_frequency", "media_sector", "sex", "vote_education"])["r"]
                       for ag, wt in mix.items())
            rows.append(part.rename("r").reset_index().assign(media_age=ma))
        out[m] = pd.concat(rows, ignore_index=True)
    return out


def _couple(nf: np.ndarray, q: np.ndarray, r: np.ndarray) -> np.ndarray:
    """P(frequency level | political-news frequency) in one cell: the table with margins nf
    (political-news frequency) and q (ISOC frequency levels) closest to the INES association,
    i.e. IPF from the seed r_i for often/sometimes and 1 - r_i for rarely/never."""
    seed = np.column_stack([r, r, 1 - r, 1 - r])
    T = ipf(seed, [((0,), nf), ((1,), q)], iters=500)
    tot = T.sum(axis=1, keepdims=True)
    return np.where(tot > 0, T / np.where(tot > 0, tot, 1.0), q[None, :])


def build_media_frequency(log=print) -> None:
    """news_tv ... news_podcasts. For each demographic cell, the ISOC distribution of the
    medium's frequency is spread over the political-news frequencies with the association that
    INES 2025 shows between that frequency and using the medium. Offline people: TV, radio and
    newspapers as internet users who use no social network; internet media never. People who
    use no social network: no news on social media."""
    q_all = isoc_frequencies()
    links = ines25_links()
    keys = ["media_age", "media_sector", "sex", "vote_education", "online"]
    W = joint(["news_frequency"] + keys)
    nf = W.pivot_table(index=keys, columns="news_frequency", values="w", aggfunc="sum").reindex(columns=NEWS).fillna(0.0)
    for m in MEDIA:
        q = q_all[m].set_index(keys)
        r = links[m].set_index(["news_frequency", "media_age", "media_sector", "sex", "vote_education"])["r"]
        rows = []
        online_states = ["social", "internet_only"] if m in INTERNET_MEDIA else ONLINE
        for cell in itertools.product(MEDIA_AGES, SECTORS, ["male", "female"], EDU, online_states):
            age, sector, sex, edu, onl = cell
            if m == "social" and onl == "internet_only":
                continue
            qrow = q.loc[(age, sector, sex, edu, "internet_only" if onl == "offline" else onl), LEVELS].to_numpy(dtype=float)
            qrow = qrow / qrow.sum()
            marg = nf.loc[cell].to_numpy(dtype=float) if cell in nf.index else np.zeros(len(NEWS))
            marg = marg / marg.sum() if marg.sum() > 0 else np.full(len(NEWS), 1 / len(NEWS))
            rr = np.array([r.loc[(f, age, sector, sex, edu)] for f in NEWS])
            cond = _couple(marg, qrow, rr)
            for i, f in enumerate(NEWS):
                rows += [(onl, f, age, sector, sex, edu, lv, cond[i, j]) for j, lv in enumerate(LEVELS)]
        cols = ["online", "news_frequency", "media_age", "media_sector", "sex", "vote_education", "value", "p"]
        df = pd.DataFrame(rows, columns=cols)
        if m in INTERNET_MEDIA:
            no = ["offline"] if m != "social" else ["offline", "internet_only"]
            df = pd.concat([df, pd.DataFrame([(o, "*", "*", "*", "*", "*", "never", 1.0) for o in no], columns=cols)])
        else:
            df = df[["news_frequency", "media_age", "media_sector", "sex", "vote_education", "online", "value", "p"]]
        write_cpt(df, f"news_{m}")
    log(f"  news_<medium> for {', '.join(MEDIA)} (ISOC {len(isoc())} respondents; INES 2025 link)")


# --- social networks -----------------------------------------------------------------------

def build_social_networks(log=print) -> None:
    """Which networks the person uses (ISOC question 3), and on which of them they regularly
    read news (question 4; users of each network). Independent logits per network: age group,
    population group, sex, education - on respondents who use social platforms for people who
    use social networks, and (WhatsApp and Telegram only) on respondents who use none for people
    who use the internet but not social networks; news also on how often the person gets news
    from social media. Someone who never gets news from social media reads none on the social
    platforms (WhatsApp and Telegram groups count as messaging, not social media)."""
    all_ = isoc().rename(columns={"sector": "media_sector", "education": "vote_education"})
    cols = ["online", "media_age", "media_sector", "sex", "vote_education", "item", "p"]
    rows = []
    for state in ("social", "internet_only"):
        d = all_[all_["online"] == state]
        X, _ = _design(d, online=False)
        cells = _cells([state])
        Xc, _ = _design(cells, online=False)
        for net in NETWORKS:
            if state == "internet_only" and net not in MESSAGING:
                p = np.zeros(len(cells))
            else:
                b0, B = fit_mnlogit(X, d[f"uses_{net}"].to_numpy(), np.ones(len(d)), 2, ridge=RIDGE)
                p = _predict(b0, B, Xc)[:, 1]
            rows += [(*c, net, pk) for c, pk in zip(cells[cols[:5]].itertuples(index=False), p)]
    df = pd.DataFrame(rows, columns=cols)
    df = pd.concat([df, pd.DataFrame([("offline", "*", "*", "*", "*", net, 0.0) for net in NETWORKS], columns=cols)])
    df["p"] = df["p"].round(10)
    df.to_csv(paths.CPTS / "social_networks.csv", index=False)

    # news on each network, given that the person uses it
    d = all_
    grid = pd.DataFrame(list(itertools.product(LEVELS, MEDIA_AGES, SECTORS)), columns=["news_social", "media_age", "media_sector"])
    grid["freq_social"] = grid["news_social"]
    rows = []
    for net in NETWORKS:
        u = d[d[f"uses_{net}"] == 1]
        Xu = _news_design(u)
        b0, B = fit_mnlogit(Xu, u[f"news_{net}"].to_numpy(), np.ones(len(u)), 2, ridge=RIDGE)
        p = _predict(b0, B, _news_design(grid))[:, 1]
        if net not in MESSAGING:
            p = np.where(grid["news_social"] == "never", 0.0, p)
        rows += [(f, a, s, net, pk) for (f, a, s), pk in zip(grid[["news_social", "media_age", "media_sector"]].itertuples(index=False), p)]
    df = pd.DataFrame(rows, columns=["news_social", "media_age", "media_sector", "item", "p"])
    df["p"] = df["p"].round(10)
    df.to_csv(paths.CPTS / "news_networks.csv", index=False)
    n_social = int((all_["online"] == "social").sum())
    log(f"  social_networks, news_networks (ISOC: {n_social} respondents who use social platforms, {len(all_) - n_social} who do not)")


def _news_design(df: pd.DataFrame) -> np.ndarray:
    cols = [(df["freq_social"] == lv).to_numpy() for lv in LEVELS[:3]]
    cols += [(df["media_age"] == a).to_numpy() for a in MEDIA_AGES[1:]]
    cols += [(df["media_sector"] == s).to_numpy() for s in SECTORS[1:]]
    return np.column_stack(cols).astype(float)


# --- TV ------------------------------------------------------------------------------------

CHANNELS = ["news12", "kan11", "news13", "channel14", "al_jazeera", "makan33", "other"]
ARABIC_CHANNELS = {"al_jazeera", "makan33"}


def _tv_design(df: pd.DataFrame) -> np.ndarray:
    cols = [df["tv_past_week"].to_numpy(dtype=float)]
    cols += [(df["media_sector"] == s).to_numpy() for s in SECTORS[1:]]
    cols += [(df["bloc"] == b).to_numpy() for b in BLOCS[1:]]
    cols += [(df["age_group"] == a).to_numpy() for a in INES25_AGES[1:]]
    return np.column_stack(cols).astype(float)


def build_tv_channels(log=print) -> None:
    """The TV channels the person watches regularly to follow the news (INES 2025, question
    614, asked of everyone who follows the news at all). Independent weighted logits per channel
    on whether the respondent watched TV news in the past week, population group, 2022 vote bloc
    and age group; Al Jazeera and Makan 33 (Arabic) on Arab respondents only. The
    model's "often" or "sometimes" watching TV news counts as having watched it in the past
    week, "rarely" as not; people who never watch TV news watch no channel."""
    d = ines25()
    d = d[d["news_freq"].isin(NEWS[:4]) & d["ch_none"].notna()].copy()
    d["tv_past_week"] = d["src_tv"].fillna(0)
    w = (d["w"] / d["w"].mean()).to_numpy()
    grid = pd.DataFrame(list(itertools.product(LEVELS[:3], SECTORS, BLOCS, MEDIA_AGES)), columns=["news_tv", "media_sector", "bloc", "media_age"])
    grid["tv_past_week"] = (grid["news_tv"] != "rarely").astype(float)
    preds = {}
    for c in CHANNELS:
        sub = d["media_sector"] == "arab" if c in ARABIC_CHANNELS else np.ones(len(d), dtype=bool)
        X, y = _tv_design(d[sub]), d.loc[sub, f"ch_{c}"].fillna(0).astype(int).to_numpy()
        b0, B = fit_mnlogit(X, y, w[np.asarray(sub)], 2, ridge=RIDGE)
        p = np.zeros(len(grid))
        for ma, mix in INES25_AGE_OF.items():
            at = (grid["media_age"] == ma).to_numpy()
            for ag, wt in mix.items():
                p[at] += wt * _predict(b0, B, _tv_design(grid[at].assign(age_group=ag)))[:, 1]
        if c in ARABIC_CHANNELS:
            p = np.where(grid["media_sector"] == "arab", p, 0.0)
        preds[c] = p
    rows = [(r.news_tv, r.media_sector, r.bloc, r.media_age, c, preds[c][i])
            for i, r in enumerate(grid.itertuples(index=False)) for c in CHANNELS]
    cols = ["news_tv", "media_sector", "vote_bloc", "media_age", "item", "p"]
    df = pd.DataFrame(rows + [("never", "*", "*", "*", c, 0.0) for c in CHANNELS], columns=cols)
    df["p"] = df["p"].round(10)
    df.to_csv(paths.CPTS / "tv_channels.csv", index=False)
    log(f"  tv_channels (INES 2025, {len(d)} respondents who follow the news)")


# --- news websites (Agam) ------------------------------------------------------------------

SITES = ["ynet", "n12", "mako", "walla", "kan", "haaretz", "rotter", "kikar", "bhol"]
SITE_LEVELS = ["never", "monthly", "weekly", "few_times_week", "daily", "several_daily"]  # scale 1..6
HAREDI_SITES = {"kikar", "bhol"}
# assumed log-odds of visiting a Haredi news site regularly, by population group (no source
# breaks these sites down; see docs/methodology/media.md)
HAREDI_SITE_LOGODDS = {"haredi": 2.0, "religious": 1.0, "traditional": 0.0, "secular": -1.0}


def _camp(sector: str, bloc: str) -> str:
    if sector == "arab":
        return "arabs"
    return {"coalition": "right", "opposition": "liberal"}.get(bloc, "jews")


def agam_site_regular() -> pd.DataFrame:
    """P(visits the site at least once a week | camp), from Agam's national distribution (page
    14) shifted on a cumulative-logit scale so that each camp's mean frequency is the one on
    page 15. Rows: site; columns: all, jews, arabs, right, liberal."""
    dist = pd.read_csv(paths.MANUAL / "agam" / "news_sites.csv").set_index("site")
    means = pd.read_csv(paths.MANUAL / "agam" / "news_sites_by_camp.csv").set_index("site")
    out = {}
    for site in SITES:
        p = dist.loc[site, SITE_LEVELS].to_numpy(dtype=float)  # never .. several_daily
        p = p / p.sum()
        upper = np.cumsum(p[::-1])[::-1][1:]  # P(C >= j), j = 2..6
        theta = -np.log(upper / (1 - upper))

        def at(eta: float) -> np.ndarray:
            return 1 / (1 + np.exp(theta - eta))

        row = {"all": float(at(0.0)[1])}
        if site in means.index:
            m = means.loc[site]
            base = brentq(lambda e: 1 + at(e).sum() - m["all"], -10, 10)
            for camp in ("jews", "arabs", "right", "liberal"):
                eta = brentq(lambda e, c=camp: 1 + at(e).sum() - m[c], -10, 10) - base
                row[camp] = float(at(eta)[1])
        out[site] = row
    return pd.DataFrame(out).T


def _two_level(p_often: float, p_some: float, target: float, ratio: float = 3.0) -> tuple[float, float]:
    """Probabilities for people who visit news sites often / sometimes, with odds ratio
    `ratio`, averaging to `target` over both (capped at 0.97 when out of reach)."""
    def avg(a: float) -> float:
        return p_often / (1 + math.exp(-a - math.log(ratio))) + p_some / (1 + math.exp(-a))
    tot = p_often + p_some
    if tot <= 0 or target <= 0:
        return 0.0, 0.0
    if target >= avg(30) * 0.97:
        a = brentq(lambda x: avg(x) - avg(30) * 0.97, -30, 30)
    else:
        a = brentq(lambda x: avg(x) - target, -30, 30)
    return 1 / (1 + math.exp(-a - math.log(ratio))), 1 / (1 + math.exp(-a))


def build_news_websites(log=print) -> None:
    """Which news sites the person visits at least once a week (Agam Media Index, pages 14-15),
    for people who use news sites often or sometimes. Each site's weekly share among internet
    users of the person's camp (Arab citizens; coalition, opposition or other Jewish and other
    voters) is spread over those who use news sites often and sometimes (odds ratio 3). Walla:
    the national share for everyone; Kikar HaShabbat and Behadrei Haredim: an assumed gradient
    by religiosity, calibrated to the national share, and no Arab readers."""
    reg = agam_site_regular()
    W = joint(["news_sites", "media_sector", "vote_bloc"], where={"online": ["social", "internet_only"]})
    W = W.pivot_table(index=["media_sector", "vote_bloc"], columns="news_sites", values="w", aggfunc="sum").reindex(columns=LEVELS).fillna(0.0)
    share = W.div(W.sum(axis=1), axis=0)

    # Haredi sites: intercept so that the internet users' national weekly share is Agam's
    def haredi_site(site: str) -> dict[str, float]:
        pop = W.sum(axis=1).groupby(level="media_sector").sum()
        def nat(a: float) -> float:
            tot = sum(pop[sec] * (0 if sec == "arab" else 1 / (1 + math.exp(-a - HAREDI_SITE_LOGODDS[sec]))) for sec in pop.index)
            return tot / pop.sum()
        a = brentq(lambda x: nat(x) - reg.loc[site, "all"], -20, 20)
        return {sec: (0.0 if sec == "arab" else 1 / (1 + math.exp(-a - HAREDI_SITE_LOGODDS[sec]))) for sec in pop.index}

    haredi = {site: haredi_site(site) for site in HAREDI_SITES}
    rows = []
    for (sector, bloc), sh in share.iterrows():
        camp = _camp(sector, bloc)
        for site in SITES:
            if site in HAREDI_SITES:
                target = haredi[site][sector]
            elif site in reg.index and pd.notna(reg.loc[site].get(camp)):
                target = reg.loc[site, camp]
            else:
                target = reg.loc[site, "all"]
            po, ps = _two_level(sh["often"], sh["sometimes"], target)
            rows += [("often", sector, bloc, site, po), ("sometimes", sector, bloc, site, ps)]
    rows += [(lv, "*", "*", site, 0.0) for lv in ("rarely", "never") for site in SITES]
    df = pd.DataFrame(rows, columns=["news_sites", "media_sector", "vote_bloc", "item", "p"])
    df["p"] = df["p"].round(10)
    df.to_csv(paths.CPTS / "news_websites.csv", index=False)
    log(f"  news_websites (Agam: {len(SITES)} sites; weekly shares {', '.join(f'{k} {v:.0%}' for k, v in reg['all'].items())})")


# --- newspapers ----------------------------------------------------------------------------

DAILIES = ["israel_hayom", "yedioth", "haaretz", "maariv", "globes"]
RELIGIOUS_WEEKLIES = ["makor_rishon", "besheva"]  # religious-Zionist; read by religious and traditional Jews
TGI_AGES = {"18_34": "age_18_34", "35_54": "age_35_54", "55_plus": "age_55_plus"}
# media age group -> TGI age groups
TGI_AGE_OF = {"18_24": {"18_34": 1.0}, "25_29": {"18_34": 1.0}, "30_39": {"18_34": 0.5, "35_54": 0.5},
              "40_49": {"35_54": 1.0}, "50_64": {"35_54": 1 / 3, "55_plus": 2 / 3}, "65_plus": {"55_plus": 1.0}}


# a title's political lean is taken from its own website's (Agam, page 15)
PAPER_SITE = {"yedioth": "ynet", "haaretz": "haaretz"}


def build_newspaper(log=print) -> None:
    """The printed newspaper a reader reads most: shares proportional to TGI average-issue
    exposure - weekday editions for people who read newspapers often, weekend editions
    otherwise - with each title's age profile (TGI 2018) for non-Haredi Jews. Religious-Zionist
    weeklies go to religious and traditional readers. Yedioth Ahronoth and Haaretz lean as
    their websites (ynet, haaretz.co.il) do among coalition, opposition and other voters, and
    each title is rescaled so that its national share is unchanged. Haredim read the Haredi
    press (Haredi TGI); Arab citizens a newspaper in Arabic."""
    titles = pd.read_csv(paths.MANUAL / "tgi" / "titles.csv")
    prof = pd.read_csv(paths.MANUAL / "tgi" / "age_profile_2018.csv").set_index("title")
    reg = agam_site_regular()

    pop = joint(["media_age"], where={"media_sector": SECTORS[:3]}).set_index("media_age")["w"]
    tgi_pop = pd.Series(0.0, index=list(TGI_AGES))
    for ma, mix in TGI_AGE_OF.items():
        for g, wt in mix.items():
            tgi_pop[g] += wt * pop.get(ma, 0.0)
    tgi_pop /= tgi_pop.sum()

    def age_index(title: str, ma: str) -> float:
        if title not in prof.index:
            return 1.0
        e = prof.loc[title, list(TGI_AGES.values())].to_numpy(dtype=float)
        mean = float((tgi_pop.to_numpy() * e).sum())
        return sum(wt * prof.loc[title, TGI_AGES[g]] for g, wt in TGI_AGE_OF[ma].items()) / mean

    def lean(title: str, bloc: str) -> float:
        site = PAPER_SITE.get(title)
        return 1.0 if site is None else reg.loc[site, _camp("secular", bloc)] / reg.loc[site, "jews"]

    gen = titles[titles["survey"] == "tgi_2025_26"].pivot_table(index="title", columns="edition", values="exposure_pct")
    har = titles[titles["survey"] == "tgi_haredi_2017"].pivot_table(index="title", columns="edition", values="exposure_pct")

    W = joint(["news_print", "media_sector", "media_age", "vote_bloc"], where={"media_sector": SECTORS[:3]})
    W = W[W["news_print"] != "never"].set_index(["news_print", "media_sector", "media_age", "vote_bloc"])["w"]
    occ = W[W.index.get_level_values("news_print") != "often"].groupby(level="media_sector").sum()
    rt_share = float(occ[["traditional", "religious"]].sum() / occ.sum())

    def base(level: str, sector: str, ma: str) -> dict[str, float]:
        edition = "weekday" if level == "often" else "weekend"
        w = {t: gen.loc[t, edition] * age_index(t, ma) for t in gen.index if pd.notna(gen.loc[t, edition])}
        for t in RELIGIOUS_WEEKLIES:
            if t in w:
                w[t] = w[t] / rt_share if sector in ("traditional", "religious") else 0.0
        return w

    def dist(w: dict[str, float]) -> dict[str, float]:
        tot = sum(w.values())
        return {t: v / tot for t, v in w.items()}

    # rescale the leaning titles so each title's national share among the readers of each
    # edition stays what it is without the lean
    scale = {"often": {}, "occasional": {}}
    for key, levels in (("often", ["often"]), ("occasional", ["sometimes", "rarely"])):
        cells = [k for k in W.index if k[0] in levels]
        target = pd.Series(0.0, dtype=float)
        for k in cells:
            target = target.add(pd.Series(dist(base(*k[:3]))) * W[k], fill_value=0.0)
        c = {t: 1.0 for t in target.index}
        for _ in range(50):
            model = pd.Series(0.0, dtype=float)
            for k in cells:
                w = {t: v * c[t] * lean(t, k[3]) for t, v in base(*k[:3]).items()}
                model = model.add(pd.Series(dist(w)) * W[k], fill_value=0.0)
            c = {t: c[t] * (target[t] / model[t] if model[t] > 0 else 1.0) for t in c}
        scale[key] = c

    rows = []
    for level, sector, ma, bloc in itertools.product(LEVELS[:3], SECTORS[:3], MEDIA_AGES, BLOCS):
        c = scale["often" if level == "often" else "occasional"]
        w = {t: v * c.get(t, 1.0) * lean(t, bloc) for t, v in base(level, sector, ma).items()}
        rows += [(level, sector, ma, bloc, t, p) for t, p in dist(w).items()]
    for level in LEVELS[:3]:
        edition = "weekday" if level == "often" else "weekend"
        w = har[edition].dropna()
        rows += [(level, "haredi", "*", "*", t, v / w.sum()) for t, v in w.items()]
        rows.append((level, "arab", "*", "*", "arabic", 1.0))
    rows.append(("never", "*", "*", "*", "none", 1.0))
    write_cpt(pd.DataFrame(rows, columns=["news_print", "media_sector", "media_age", "vote_bloc", "value", "p"]), "newspaper")
    log(f"  newspaper (TGI; religious and traditional readers are {rt_share:.0%} of occasional non-Haredi Jewish readers; "
        f"lean: Haaretz x{lean('haaretz', 'opposition') / lean('haaretz', 'coalition'):.1f}, "
        f"Yedioth x{lean('yedioth', 'opposition') / lean('yedioth', 'coalition'):.1f} opposition vs coalition)")


# --- preferred source (ISOC question 2) -----------------------------------------------------

# Respondents chose among the media they use often (everyone who answered prefers one of
# those; those who use none often were not asked). The model picks among the media the person
# uses at their highest frequency: own-frequency penalties far apart make the choice
# lexicographic, and "none" wins only when every medium is "never".
OWN = {"often": 0.0, "sometimes": -30.0, "rarely": -60.0, "never": -120.0}
NONE = -90.0


def build_preferred_source(log=print) -> None:
    """Which medium the person prefers for news (ISOC question 2, "Which of the sources you
    marked do you prefer?"), among the media they use most often. A conditional logit on the
    respondents who answered: medium constants plus age-group and population-group effects per
    medium (ridge 1), written as a logit node over the seven media frequencies, age group and
    population group."""
    d = isoc().dropna(subset=["preferred"])
    d = d[d["preferred"] != "other"].reset_index(drop=True)
    n, K = len(d), len(MEDIA)
    y = d["preferred"].map({m: i for i, m in enumerate(MEDIA)}).to_numpy()
    own = np.stack([d[f"freq_{m}"].map(OWN).to_numpy() for m in MEDIA], axis=1)
    A = np.stack([(d["media_age"] == a).to_numpy() for a in MEDIA_AGES[1:]], axis=1).astype(float)
    S = np.stack([(d["sector"] == x).to_numpy() for x in SECTORS[1:]], axis=1).astype(float)
    na, ns = A.shape[1], S.shape[1]

    def unpack(th):
        a0 = np.concatenate([[0.0], th[:K - 1]])
        g = th[K - 1:K - 1 + na * K].reshape(na, K)
        h = th[K - 1 + na * K:].reshape(ns, K)
        return a0, g, h

    def nll(th):
        a0, g, h = unpack(th)
        u = a0[None, :] + own + A @ g + S @ h
        u = u - u.max(axis=1, keepdims=True)
        ll = u[np.arange(n), y] - np.log(np.exp(u).sum(axis=1))
        return -ll.sum() + 0.5 * RIDGE * ((g ** 2).sum() + (h ** 2).sum())

    res = minimize(nll, np.zeros(K - 1 + (na + ns) * K), method="L-BFGS-B", options={"maxiter": 5000})
    a0, g, h = unpack(res.x)
    coef = {f"news_{m}": {lvl: {m: v} for lvl, v in OWN.items()} for m in MEDIA}
    coef["media_age"] = {a: ({MEDIA[k]: float(g[i - 1, k]) for k in range(K)} if i else {}) for i, a in enumerate(MEDIA_AGES)}
    coef["media_sector"] = {x: ({MEDIA[k]: float(h[i - 1, k]) for k in range(K)} if i else {}) for i, x in enumerate(SECTORS)}
    out = {"intercept": {**{m: float(a0[k]) for k, m in enumerate(MEDIA)}, "none": NONE}, "coef": coef}
    (paths.CPTS / "preferred_source.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    log(f"  preferred_source (ISOC, {n} respondents who use at least one medium often)")
