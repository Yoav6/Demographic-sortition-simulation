"""Discovery helper: render CBS Statistical Abstract chapter pages (JavaScript) and list
their Excel tables with titles. Writes data/raw/_discovery/chapters.tsv (gitignored)."""

from __future__ import annotations

import io
import time

import httpx

from .. import paths
from .base import HEADERS, throttle
from .browser import rendered_links
from .discover import _title

ABSTRACT_2025 = "https://www.cbs.gov.il/he/publications/Pages/2025/{}-%D7%A9%D7%A0%D7%AA%D7%95%D7%9F-%D7%A1%D7%98%D7%98%D7%99%D7%A1%D7%98%D7%99-%D7%9C%D7%99%D7%A9%D7%A8%D7%90%D7%9C-2025-%D7%9E%D7%A1%D7%A4%D7%A8-76.aspx"

CHAPTERS = {
    "attitudes": "%D7%A2%D7%9E%D7%93%D7%95%D7%AA-%D7%95%D7%AA%D7%97%D7%95%D7%A9%D7%95%D7%AA-%D7%94%D7%A6%D7%99%D7%91%D7%95%D7%A8",
    "labour": "%D7%A9%D7%95%D7%A7-%D7%94%D7%A2%D7%91%D7%95%D7%93%D7%94",
    "education": "%D7%97%D7%99%D7%A0%D7%95%D7%9A-%D7%95%D7%94%D7%A9%D7%9B%D7%9C%D7%94",
    "living_standards": "%D7%A8%D7%9E%D7%AA-%D7%97%D7%99%D7%99%D7%9D",
    "health": "%D7%91%D7%A8%D7%99%D7%90%D7%95%D7%AA",
    "welfare": "%D7%A8%D7%95%D7%95%D7%97%D7%94",
    "science_tech": "%D7%9E%D7%93%D7%A2-%D7%98%D7%9B%D7%A0%D7%95%D7%9C%D7%95%D7%92%D7%99%D7%94-%D7%95%D7%AA%D7%A7%D7%A9%D7%95%D7%A8%D7%AA",
    "elections": "%D7%91%D7%97%D7%99%D7%A8%D7%95%D7%AA-%D7%9B%D7%A0%D7%A1%D7%AA-%D7%95%D7%9E%D7%9E%D7%A9%D7%9C",
}


def discover_chapters(names: list[str] | None = None, log=print) -> None:
    out = paths.RAW / "_discovery" / "chapters.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh, httpx.Client(headers=HEADERS, follow_redirects=True, timeout=60) as client:
        for name in names or list(CHAPTERS):
            url = ABSTRACT_2025.format(CHAPTERS[name])
            links = rendered_links(url, pattern=r"\.xlsx?$")
            log(f"== {name}: {len(links)} excel links")
            for _text, href in links:
                throttle(href)
                try:
                    content = client.get(href).content
                    title = _title(content) if content.startswith(b"PK") else "?"
                except Exception as exc:  # noqa: BLE001
                    title = f"error {exc}"
                fh.write(f"{name}\t{href}\t{title}\n")
                fh.flush()
                log(f"   {href.rsplit('/', 1)[-1]}\t{title[:120]}")
            time.sleep(5)
