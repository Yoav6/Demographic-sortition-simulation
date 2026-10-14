"""Headless-browser helpers (Playwright) for CBS pages that are rendered by JavaScript
or protected by a web-application firewall.

Used by:
  * `popsim links <url>`   - list the file links a CBS publication page renders, to pin
                             them in sources.yaml (discovery only);
  * fetch/cbs_generator.py - the Social Survey table generator.
"""

from __future__ import annotations

import re
from contextlib import contextmanager

from .base import HEADERS


@contextmanager
def browser_page(locale: str = "he-IL"):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(user_agent=HEADERS["User-Agent"], locale=locale)
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()


def rendered_links(url: str, pattern: str = r"\.(xlsx?|zip|csv|pdf)(\?|$)", wait_ms: int = 10000) -> list[tuple[str, str]]:
    """Returns (link text, absolute URL) pairs for links matching `pattern` after JS runs.

    CBS publication pages keep their file lists collapsed under "הצג הכל" (show all), so
    that control is clicked when present. ("networkidle" never fires on CBS pages.)
    """
    rx = re.compile(pattern, re.I)
    with browser_page() as page:
        page.goto(url, wait_until="commit", timeout=90_000)
        page.wait_for_timeout(wait_ms)
        try:
            page.get_by_text("הצג הכל").first.click(timeout=3000)
            page.wait_for_timeout(3000)
        except Exception:  # noqa: BLE001 - the control is optional
            pass
        anchors = page.eval_on_selector_all(
            "a[href]", "els => els.map(e => [e.innerText.trim(), e.href])"
        )
    seen, out = set(), []
    for text, href in anchors:
        if rx.search(href) and href not in seen:
            seen.add(href)
            out.append((" ".join(text.split()), href))
    return out
