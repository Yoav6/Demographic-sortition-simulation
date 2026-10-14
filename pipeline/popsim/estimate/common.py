"""Shared definitions and numerical tools for the estimators."""

from __future__ import annotations

import numpy as np
import pandas as pd

GROUPS = ["jewish", "muslim", "christian_arab", "druze", "other"]
ARAB_GROUPS = ["muslim", "christian_arab", "druze"]
SEXES = ["male", "female"]

# Age bands of the frame (inclusive bounds; the last band is open-ended up to MAX_AGE).
MAX_AGE = 100
AGE_BANDS: list[tuple[int, int]] = [(18, 19)] + [(a, a + 4) for a in range(20, 85, 5)] + [(85, MAX_AGE)]


def band_id(lo: int, hi: int) -> str:
    return f"{lo}+" if hi >= MAX_AGE else f"{lo}-{hi}"


AGE_BAND_IDS = [band_id(lo, hi) for lo, hi in AGE_BANDS]


def age_to_band(age: int) -> str:
    for lo, hi in AGE_BANDS:
        if lo <= age <= hi:
            return band_id(lo, hi)
    raise ValueError(f"age {age} outside the adult bands")


def ipf(seed: np.ndarray, margins: list[tuple[tuple[int, ...], np.ndarray]], iters: int = 200, tol: float = 1e-9) -> np.ndarray:
    """Iterative proportional fitting.

    seed: n-dimensional non-negative array.
    margins: list of (axes kept, target array over those axes). Targets for the same
    total should agree; cells with zero seed stay zero (structural zeros).
    """
    x = seed.astype(float).copy()
    for _ in range(iters):
        max_rel = 0.0
        for axes, target in margins:
            drop = tuple(i for i in range(x.ndim) if i not in axes)
            current = x.sum(axis=drop)
            with np.errstate(divide="ignore", invalid="ignore"):
                factor = np.where(current > 0, target / current, 0.0)
            max_rel = max(max_rel, float(np.nanmax(np.abs(np.where(current > 0, factor - 1, 0)))))
            shape = [x.shape[i] if i in axes else 1 for i in range(x.ndim)]
            # broadcast factor back over the dropped axes (axes are in increasing order)
            x = x * factor.reshape(shape)
        if max_rel < tol:
            break
    return x


def normalize_rows(df: pd.DataFrame, by: list[str], col: str = "p") -> pd.DataFrame:
    df = df.copy()
    s = df.groupby(by)[col].transform("sum")
    df[col] = np.where(s > 0, df[col] / s, 0.0)
    return df


def combine(W: pd.DataFrame, a: str, b: str, A: pd.DataFrame, B: pd.DataFrame, target: str, values: list[str]) -> pd.DataFrame:
    """P(target | a, b) from two published conditionals, P(target | a) and P(target | b).

    W: population counts over (a, b) [columns a, b, w]; A: [a, target, p]; B: [b, target, p].
    Finds counts X(a, b, t) that sum over t to W(a, b), over b to W(a) A(t | a), and over a to
    W(b) B'(t | b), where B' is B adjusted (raked) so that its implied totals by t equal A's -
    A is kept exactly because it conditions on the model's main parents. IPF starts from the
    naive-Bayes estimate W(a, b) A(t | a) B(t | b) / P(t), so a and b interact only as much as
    the data require (the maximum-entropy solution). Cells with no population fall back to A.
    Returns [a, b, target, p].
    """
    av = list(dict.fromkeys(W[a]))
    bv = list(dict.fromkeys(W[b]))
    Wm = W.pivot_table(index=a, columns=b, values="w", aggfunc="sum").reindex(index=av, columns=bv).fillna(0.0).to_numpy()
    Am = A.pivot_table(index=a, columns=target, values="p", aggfunc="sum").reindex(index=av, columns=values)
    Bm = B.pivot_table(index=b, columns=target, values="p", aggfunc="sum").reindex(index=bv, columns=values)
    if Am.isna().all(axis=1).any() or Bm.isna().all(axis=1).any():
        missing = list(Am.index[Am.isna().all(axis=1)]) + list(Bm.index[Bm.isna().all(axis=1)])
        raise ValueError(f"combine: no conditional for {missing}")
    Am, Bm = Am.fillna(0.0).to_numpy(), Bm.fillna(0.0).to_numpy()
    Wa, Wb = Wm.sum(axis=1), Wm.sum(axis=0)
    Tt = Wa @ Am
    if Tt.sum() <= 0:
        raise ValueError("combine: empty population")
    Mb = ipf(Wb[:, None] * Bm + 1e-12, [((0,), Wb), ((1,), Tt)])
    Pt = Tt / Tt.sum()
    seed = Wm[:, :, None] * Am[:, None, :] * Bm[None, :, :] / np.where(Pt > 0, Pt, 1.0)[None, None, :]
    X = ipf(seed, [((0, 2), Wa[:, None] * Am), ((1, 2), Mb), ((0, 1), Wm)], iters=500)
    tot = X.sum(axis=2, keepdims=True)
    cond = np.where(tot > 0, X / np.where(tot > 0, tot, 1.0), Am[:, None, :])
    rows = [(x, y, v, cond[i, j, k]) for i, x in enumerate(av) for j, y in enumerate(bv) for k, v in enumerate(values)]
    return pd.DataFrame(rows, columns=[a, b, target, "p"])
