"""Custom fetchers for sources that need more than a plain GET.

A source file can set `fetcher: <name>` in sources.yaml; base.fetch_source then calls
FETCHERS[name](file_url) to obtain the bytes instead of downloading the URL directly.
The bytes are pinned in sources.lock.json like any other file.
"""

from __future__ import annotations

import html
import json
import re

import httpx

from .base import HEADERS, throttle


def igra_names(page_url: str) -> bytes:
    """IGRA population-registry name tables (WordPress "Ninja Tables").

    The page embeds a one-time nonce in the AJAX URL that returns the table rows as JSON.
    We save a normalised JSON list of {name, first, middle}: Hebrew name, count as a
    first name, count as a middle name.
    """
    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=120) as client:
        throttle(page_url)
        page = client.get(page_url).text
        m = re.search(r"admin-ajax\.php\?action=wp_ajax_ninja_tables_public_action[^\"']*", page)
        if not m:
            raise RuntimeError(f"no ninja-tables endpoint found on {page_url}")
        query = html.unescape(m.group(0)).replace("\\/", "/")
        url = "https://genealogy.org.il/wordpress/wp-admin/" + query
        throttle(url)
        rows = client.get(url).json()
    out = []
    for r in rows:
        v = r["value"]
        out.append(
            {
                "name": v["ninja_column_3"].strip(),
                "first": int(str(v["ninja_column_2"]).replace(",", "") or 0),
                "middle": int(str(v["ninja_column_1"]).replace(",", "") or 0),
            }
        )
    out.sort(key=lambda d: (-d["first"], d["name"]))
    return (json.dumps(out, ensure_ascii=False, indent=0) + "\n").encode("utf-8")


WIKIDATA_TYPES = "wd:Q12308941 wd:Q11879590 wd:Q3409032 wd:Q202444"  # male, female, unisex, given name
WIKIDATA_BATCH = 350
WIKIDATA_QUERY = """
SELECT ?he ?item ?type ?en WHERE {
  VALUES ?he { %s }
  VALUES ?type { %s }
  ?item rdfs:label ?he ; wdt:P31 ?type .
  OPTIONAL { ?item rdfs:label ?en . FILTER(LANG(?en) = "en") }
}
"""


def _model_names(min_people: int = 100) -> list[str]:
    """Hebrew first names worth transliterating: every name borne by at least `min_people`
    people in the CBS table (all groups) or the IGRA "Other" tables. Needs those two
    sources fetched first (they precede this one in sources.yaml)."""
    from ..estimate.names import read_cbs_names, read_igra

    cbs = read_cbs_names().groupby("name")["count"].sum()
    names = set(cbs[cbs >= min_people].index)
    for sex in ("female", "male"):
        igra = read_igra(sex)
        names |= set(igra.loc[igra["count"] >= min_people // 2, "name"])
    return sorted(n for n in names if '"' not in n and "\\" not in n)


def wikidata_given_names(endpoint: str) -> bytes:
    """English labels of Wikidata given-name items whose Hebrew label is one of the model's
    names, queried by exact label in batches (whole-class scans time out). Saved as a
    normalised JSON list sorted for stable bytes."""
    headers = dict(HEADERS, Accept="application/sparql-results+json")
    headers["User-Agent"] = "popsim/0.1 (sortition simulation research; python-httpx)"
    names = _model_names()
    rows: dict[tuple[str, str, str], dict] = {}
    with httpx.Client(headers=headers, timeout=300) as client:
        for i in range(0, len(names), WIKIDATA_BATCH):
            batch = " ".join(f'"{n}"@he' for n in names[i : i + WIKIDATA_BATCH])
            query = WIKIDATA_QUERY % (batch, WIKIDATA_TYPES)
            for attempt in range(4):
                throttle(endpoint)
                resp = client.post(endpoint, data={"query": query})
                if resp.status_code == 200 and resp.content.lstrip().startswith(b"{"):
                    break
            resp.raise_for_status()
            for r in resp.json()["results"]["bindings"]:
                item = r["item"]["value"].rsplit("/", 1)[-1]
                typ = r["type"]["value"].rsplit("/", 1)[-1]
                key = (r["he"]["value"], item, typ)
                rows[key] = {"he": key[0], "item": item, "type": typ, "en": r.get("en", {}).get("value")}
    out = sorted(rows.values(), key=lambda d: (d["he"], int(d["item"][1:]), d["type"]))
    return (json.dumps(out, ensure_ascii=False, indent=0) + "\n").encode("utf-8")


FETCHERS = {"igra_names": igra_names, "wikidata_given_names": wikidata_given_names}
