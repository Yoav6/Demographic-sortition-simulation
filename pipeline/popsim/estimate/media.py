"""Media diet: online use, how often the person follows the news (overall and on social
networks), and favourite TV news broadcast. See docs/methodology/media.md.

    online         <- group, religiosity, sex, age band             (CBS Social Survey 2024)
    vote_bloc      <- vote_2022                                       (lookup)
    news_frequency <- religiosity, vote_age, vote_education, vote_bloc           (INES 2022)
    social_news    <- online, news_frequency, vote_age                          (INES 2022)
    favorite_news  <- group, vote_bloc                                (Agam Media Index 2024)
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from .. import paths
from .socioeconomic import by_population, expand, write_cpt
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
TV = ["news12", "channel14", "kan11", "news13", "i24", "channel9", "other", "none"]


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
    """How often the person catches up on political news (INES: logit on religiosity, age,
    education and 2022 vote bloc), and how often on social networks - given that frequency and
    age, for people who use social networks (INES respondents who do, weighted; each
    frequency x age row shrunk toward its frequency row with 10 pseudo-respondents)."""
    X, y, w, names = _ines("news_freq", NEWS)
    b0, B = fit_mnlogit(X, y, w, len(NEWS))
    write_cpt(_expand_logit(b0, B, names, NEWS), "news_frequency")

    ines = pd.read_csv(paths.interim_path("ines_2022"))
    d = ines[ines["news_freq"].isin(NEWS) & ines["social_news_freq"].isin(NEWS) & ines["w_panel1"].notna()].copy()
    d["age3"] = d["age_group"].map(INES_AGE)
    d = d.dropna(subset=["age3"])
    by_freq = d.groupby(["news_freq", "social_news_freq"])["w_panel1"].sum().unstack(fill_value=0.0).reindex(index=NEWS, columns=NEWS, fill_value=0.0)
    by_freq = (by_freq + 0.5).div((by_freq + 0.5).sum(axis=1), axis=0)
    rows = []
    for f, a in itertools.product(NEWS, AGES):
        g = d[(d["news_freq"] == f) & (d["age3"] == a)]
        n = len(g)
        share = g.groupby("social_news_freq")["w_panel1"].sum().reindex(NEWS, fill_value=0.0)
        share = share / share.sum() if share.sum() > 0 else by_freq.loc[f]
        p = (n * share + 10 * by_freq.loc[f]) / (n + 10)
        for age in ([a, "too_young"] if a == "y" else [a]):
            rows += [("social", f, age, v, p[v]) for v in NEWS]
    rows += [(o, "*", "*", "no_social_media", 1.0) for o in ("internet_only", "offline")]
    write_cpt(pd.DataFrame(rows, columns=["online", "news_frequency", "vote_age", "value", "p"]), "social_news")
    log(f"  news_frequency (INES, {len(y)} respondents), social_news ({len(d)})")


def build_favorite_news(log=print) -> None:
    """Agam Media Index: favourite news broadcast of coalition and opposition supporters, and of
    everyone. Jewish and "other" citizens who voted for the coalition or the Jewish opposition in
    2022 get those distributions; others the overall one. Arabic-language media are not covered,
    so Arab and Druze citizens get "not_measured"."""
    t = pd.read_csv(paths.MANUAL / "agam" / "favorite_news.csv")
    dist = {pop: g.set_index("outlet")["percent"].reindex(TV).fillna(0.0) for pop, g in t.groupby("population")}
    use = {"coalition": "coalition", "opposition": "opposition", "arab": "opposition"}
    rows = []
    for group in ("jewish", "other"):
        for bloc in BLOCS:
            d = dist[use.get(bloc, "all")]
            d = d / d.sum()
            rows += [(group, bloc, v, p) for v, p in d.items() if p > 0]
    rows.append(("*", "*", "not_measured", 1.0))
    write_cpt(pd.DataFrame(rows, columns=["group", "vote_bloc", "value", "p"]), "favorite_news")
    log("  favorite_news")
