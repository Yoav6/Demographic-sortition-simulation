"""Estimation steps, run in dependency order by `popsim build`.

Each step reads raw/interim data and writes files under model/ (or data/interim/).
"""

from __future__ import annotations

import importlib
import time

# (step name, module path, function) in execution order
STEPS: list[tuple[str, str, str]] = [
    ("extract_population", "popsim.extract.cbs_abstract", "extract"),
    ("extract_ines", "popsim.extract.ines", "extract"),
    ("extract_cec", "popsim.extract.cec", "extract"),
    ("extract_origin", "popsim.extract.cbs_origin", "extract"),
    ("frame", "popsim.estimate.frame", "build"),
    ("age", "popsim.estimate.basic", "build_age"),
    ("lookups", "popsim.estimate.basic", "build_lookups"),
    ("first_name", "popsim.estimate.names", "build"),
    ("religiosity_ei", "popsim.estimate.religiosity_ei", "build"),
    ("religiosity", "popsim.estimate.religiosity", "build"),
    ("origin", "popsim.estimate.origin", "build"),
    ("birth_region", "popsim.estimate.socioeconomic", "build_birth_region"),
    ("marital_status", "popsim.estimate.socioeconomic", "build_marital"),
    ("children", "popsim.estimate.socioeconomic", "build_children"),
    ("education", "popsim.estimate.socioeconomic", "build_education"),
    ("military_service", "popsim.estimate.socioeconomic", "build_military"),
    ("labour_status", "popsim.estimate.socioeconomic", "build_labour"),
    ("occupation", "popsim.estimate.socioeconomic", "build_occupation"),
    ("industry", "popsim.estimate.socioeconomic", "build_industry_work"),
    ("income", "popsim.estimate.socioeconomic", "build_income"),
    ("household_income", "popsim.estimate.socioeconomic", "build_household"),
    ("income_percentile", "popsim.estimate.socioeconomic", "build_income_percentile"),
    ("household_income_percentile", "popsim.estimate.socioeconomic", "build_household_percentile"),
    ("health", "popsim.estimate.health", "build_health"),
    ("chronic", "popsim.estimate.health", "build_chronic"),
    ("disability", "popsim.estimate.health", "build_disability"),
    ("vote_helpers", "popsim.estimate.vote", "build_helpers"),
    ("vote_2022", "popsim.estimate.vote", "build"),
    ("online", "popsim.estimate.media", "build_online"),
    ("vote_bloc", "popsim.estimate.media", "build_vote_bloc"),
    ("news", "popsim.estimate.media", "build_news"),
    ("favorite_news", "popsim.estimate.media", "build_favorite_news"),
    ("literacy", "popsim.estimate.skills", "build"),
]


def run_steps(only: list[str] | None = None, log=print) -> None:
    names = [s[0] for s in STEPS]
    for o in only or []:
        if o not in names:
            raise SystemExit(f"unknown step {o!r}; steps: {', '.join(names)}")
    for name, module, func in STEPS:
        if only and name not in only:
            continue
        t = time.time()
        log(f"[{name}]")
        getattr(importlib.import_module(module), func)()
        log(f"  done in {time.time() - t:.1f}s")
