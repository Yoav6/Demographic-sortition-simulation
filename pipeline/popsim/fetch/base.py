"""Downloader for tier-A sources.

Behaviour per file:
  * already on disk and matching the pinned sha256 -> skipped;
  * otherwise downloaded (browser-like headers: CBS and the elections committee
    reject bare HTTP clients), from the live URL, then the archive URL, then the
    optional mirror ($POPSIM_MIRROR/<source id>/<file>);
  * if a pin exists and the bytes differ, the run fails unless --update is given,
    because a silently changed source would silently change the model.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import time
from pathlib import Path

import httpx

from ..sources import Source, SourceFile, load_lock, load_sources, save_lock

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    ),
    "Accept-Language": "he,en;q=0.8",
    "Accept": "*/*",
}


class SourceChanged(RuntimeError):
    pass


# Government sites block clients that send bursts of requests (CBS blocked us for ~25
# minutes after ~60 requests in a minute), so requests to the same host are spaced out.
MIN_INTERVAL_SECONDS = 2.0
HOST_INTERVAL_SECONDS = {
    "www.cbs.gov.il": 6.0,
    "boardsgenerator.cbs.gov.il": 6.0,
    "query.wikidata.org": 65.0,  # WDQS rate-limits heavy users to ~1 request/minute
}
_last_request: dict[str, float] = {}


def throttle(url: str) -> None:
    host = httpx.URL(url).host
    interval = HOST_INTERVAL_SECONDS.get(host, MIN_INTERVAL_SECONDS)
    wait = _last_request.get(host, 0.0) + interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last_request[host] = time.monotonic()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _looks_like_error_page(content: bytes, expected_name: str) -> bool:
    # CBS answers missing files and WAF blocks with HTTP 200 + an HTML page.
    if expected_name.lower().endswith((".html", ".htm", ".aspx")):
        return False
    head = content[:512].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def _download(url: str, expected_name: str, retries: int = 3) -> bytes:
    last: Exception | None = None
    for attempt in range(retries):
        throttle(url)
        try:
            with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=120) as client:
                resp = client.get(url)
                resp.raise_for_status()
                if _looks_like_error_page(resp.content, expected_name):
                    raise RuntimeError(f"got an HTML page instead of {expected_name}")
                return resp.content
        except Exception as exc:  # noqa: BLE001 - retried and reported
            last = exc
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"download failed for {url}: {last}")


def _candidate_urls(src: Source, f: SourceFile) -> list[str]:
    urls = [f.url]
    if f.archive_url:
        urls.append(f.archive_url)
    mirror = os.environ.get("POPSIM_MIRROR")
    if mirror:
        urls.append(f"{mirror.rstrip('/')}/{src.id}/{f.path}")
    return urls


def fetch_source(src: Source, lock: dict, update: bool = False, log=print) -> None:
    pins = lock.setdefault(src.id, {})
    for f in src.files:
        dest = src.raw_path(f)
        pin = pins.get(f.path)
        if dest.exists() and pin and sha256_file(dest) == pin["sha256"]:
            log(f"  ok      {src.id}/{f.path}")
            continue
        content, used, errors = None, None, []
        if f.fetcher:
            from .custom import FETCHERS

            try:
                content, used = FETCHERS[f.fetcher](f.url), f.url
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{f.fetcher}: {exc}")
        for url in _candidate_urls(src, f) if content is None and not f.fetcher else []:
            try:
                content, used = _download(url, f.path), url
                break
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))
        if content is None:
            raise RuntimeError(f"{src.id}/{f.path}: all URLs failed:\n  " + "\n  ".join(errors))
        digest = hashlib.sha256(content).hexdigest()
        if pin and pin["sha256"] != digest and not update:
            raise SourceChanged(
                f"{src.id}/{f.path} changed upstream (pinned {pin['sha256'][:12]}, got {digest[:12]}). "
                "Re-run with --update to accept it, then rebuild and re-validate the model."
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        pins[f.path] = {
            "sha256": digest,
            "size": len(content),
            "retrieved": dt.date.today().isoformat(),
            "url": used,
        }
        log(f"  fetched {src.id}/{f.path} ({len(content):,} bytes) from {used}")


def fetch(ids: list[str] | None = None, update: bool = False, log=print) -> None:
    sources = load_sources()
    lock = load_lock()
    selected = [sources[i] for i in ids] if ids else list(sources.values())
    try:
        for src in selected:
            # Tier M sources may list the original document (e.g. a PDF whose charts we
            # transcribed) so its checksum is pinned too. Tier B/C/R need a browser,
            # credentials or licensed access and have their own commands.
            if src.tier not in ("A", "M") or not src.files:
                continue
            fetch_source(src, lock, update=update, log=log)
    finally:
        save_lock(lock)
