"""Client for the CBS Social Survey table generator (tier B).

The generator (boardsgenerator.cbs.gov.il) is an AngularJS app whose JSON handlers sit
behind a web-application firewall; they answer only inside a real browser session. We
open the wizard page in headless Chromium and call the same handlers the app calls:
  WizardHandler.ashx  - catalogue (years, subjects, variables, categories)
  GridHandler.ashx    - a cross-tab: up to 3 nested row and 3 nested column variables,
                        weighted frequencies with relative standard errors, <= 3 filters.

Each query is a JSON spec in data/manual/cbs_ss/queries/<id>.json; its result is written
to data/manual/cbs_ss/<id>.csv (committed - CBS publishes these tables online, and the
spec lets anyone regenerate them with `popsim fetch-cbs-ss`). Output columns: one
`<variable>_code`/`<variable>_label` pair per row/column variable, then `count` (weighted
persons) and `rse` (relative standard error of the cell).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pandas as pd

from .. import paths
from .browser import browser_page

WIZARD_URL = "https://boardsgenerator.cbs.gov.il/pages/Seker/wizardpage.aspx"
QUERY_DIR = paths.MANUAL / "cbs_ss" / "queries"
OUT_DIR = paths.MANUAL / "cbs_ss"

_WIZ = """async (q) => {
  const r = await fetch('/Handlers/Seker/WizardHandler.ashx?' + new URLSearchParams(q).toString(),
                        {method: 'POST', headers: {'Content-type': 'text/html'}});
  return await r.text();
}"""
_GRID = """async (query) => {
  const body = new URLSearchParams({query: query}).toString();
  const r = await fetch('/Handlers/Seker/GridHandler.ashx',
                        {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}, body});
  return await r.text();
}"""


class GeneratorSession:
    def __init__(self, page):
        self.page = page
        self._field_of: dict[int, str] = {}

    def wizard(self, **params) -> dict:
        time.sleep(1.0)
        return json.loads(self.page.evaluate(_WIZ, params))

    def categories(self, var_id: int) -> list[dict]:
        r = self.wizard(mode="SetCategories", id=var_id, lang="Hebrew")
        return r.get("Categories", r)

    def grid(self, spec: dict) -> dict:
        rows = spec["rows"] + [None] * (3 - len(spec["rows"]))
        cols = spec.get("cols", []) + [None] * (3 - len(spec.get("cols", [])))
        query = {
            "Fr": rows[0], "Sr": rows[1], "Tr": rows[2],
            "Fc": cols[0], "Sc": cols[1], "Tc": cols[2],
            "BoardChoice": "0", "PrecentDirection": None,
            "SekerType": spec.get("seker_type", 1),
            "Fyear": spec["year"], "Tyear": spec.get("to_year", spec["year"]),
            "Filters": [{"QuestId": f["var"], "Values": ",".join(str(v) for v in f["values"])} for f in spec.get("filters", [])],
            "Grouping": [], "Unknow": False, "IncludeAllRelevant": False, "uptodate": False,
        }
        time.sleep(2.0)
        text = self.page.evaluate(_GRID, json.dumps(query))
        return json.loads(text)


def _cell(v) -> tuple[float, float]:
    """'546,818##&nbsp&&0.0352' -> (546818.0, 0.0352); suppressed/empty -> (nan, nan)."""
    if v is None:
        return float("nan"), float("nan")
    s = str(v)
    m = re.match(r"\s*([-\d,\.]+)\s*(?:##.*?&&([\d\.eE-]+))?", s)
    if not m or not re.search(r"\d", m.group(1)):
        return float("nan"), float("nan")
    num = float(m.group(1).replace(",", ""))
    rse = float(m.group(2)) if m.group(2) else float("nan")
    return num, rse


def parse_grid(result: dict, spec: dict, cat_labels: dict[int, dict[str, str]]) -> pd.DataFrame:
    """Flatten the Kendo-grid JSON into a long table."""
    columns = result["columns"]
    # row variable fields: hidden "<X>Code" columns paired with visible label columns
    code_fields = [c["field"].strip("[]'") for c in columns if c.get("hidden") and c["field"].strip("[]'").endswith("Code")]
    leaf_cols: list[tuple[str, list[str]]] = []

    def walk(col, path):
        title = col.get("title") or ""
        sub = col.get("columns")
        if sub:
            for c in sub:
                walk(c, path + [title])
        else:
            field = col["field"].strip("[]'")
            if field.endswith("Code") or field in [cf[:-4] for cf in code_fields]:
                return
            leaf_cols.append((field, path + [title]))

    for c in columns:
        walk(c, [])
    rows = []
    for rec in result["data"]:
        codes = [rec.get(cf) for cf in code_fields]
        if any(str(c) == "-1" for c in codes):  # totals rows
            continue
        for field, titles in leaf_cols:
            if field not in rec:
                continue
            count, rse = _cell(rec[field])
            rows.append({**{f"r{i}_code": codes[i] for i in range(len(codes))}, "col_path": " | ".join(t for t in titles if t), "count": count, "rse": rse})
    df = pd.DataFrame(rows)
    # name row variables and attach labels
    for i, var in enumerate(spec["rows"]):
        df = df.rename(columns={f"r{i}_code": f"{var}_code"})
        df[f"{var}_label"] = df[f"{var}_code"].astype(str).map(cat_labels.get(var, {}))
    # column path -> one column per column variable (titles are category labels)
    cols = spec.get("cols", [])
    if cols:
        parts = df["col_path"].str.split(r" \| ", regex=True)
        for i, var in enumerate(cols):
            df[f"{var}_label"] = parts.map(lambda p: p[i] if len(p) > i else None)
            inv = {lbl: code for code, lbl in cat_labels.get(var, {}).items()}
            df[f"{var}_code"] = df[f"{var}_label"].map(inv)
        df = df[~df[[f"{v}_label" for v in cols]].isin(["סה''כ", 'סה"כ', "סך הכל"]).any(axis=1)]
    return df.drop(columns=["col_path"])


def run_queries(ids: list[str] | None = None, log=print) -> None:
    specs = sorted(QUERY_DIR.glob("*.json"))
    if ids:
        specs = [p for p in specs if p.stem in ids]
    with browser_page() as page:
        page.goto(WIZARD_URL, wait_until="commit", timeout=90_000)
        page.wait_for_timeout(12_000)
        session = GeneratorSession(page)
        label_cache: dict[int, dict[str, str]] = {}
        for path in specs:
            spec = json.loads(path.read_text(encoding="utf-8"))
            for var in spec["rows"] + spec.get("cols", []):
                if var not in label_cache:
                    label_cache[var] = {str(c["Code"]): c["Description"] for c in session.categories(var)}
            result = session.grid(spec)
            df = parse_grid(result, spec, label_cache)
            out = OUT_DIR / f"{path.stem}.csv"
            df.to_csv(out, index=False)
            log(f"  {path.stem}: {len(df)} cells")
