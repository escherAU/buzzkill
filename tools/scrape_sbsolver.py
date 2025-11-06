#!/usr/bin/env python3
"""
tools/scrape_sbsolver.py

Scrape sbsolver.com Spelling Bee answers (alphabetical list) politely.

- Targets ONLY the answers container (#alpha-inner) the site renders for the
  'list solutions alphabetically' view shown inline on each puzzle page.
- Extracts anchor text from 'td.bee-hover > a' under #alpha-inner.
- Applies guardrails: letters-only, min length 4, optional pool/center filter.
- Checks robots.txt and rate-limits requests.
- Saves JSON to data/wordlists/<id>.json.

Usage examples:
  python tools/scrape_sbsolver.py --ids 1 25
  python tools/scrape_sbsolver.py --range 1 100
  python tools/scrape_sbsolver.py --url https://www.sbsolver.com/s/2736
  python tools/scrape_sbsolver.py --ids 2736 --pool denopux --center n
"""

from __future__ import annotations
import argparse
import json
import re
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse
from urllib import robotparser

import requests
from bs4 import BeautifulSoup

BASE = "https://www.sbsolver.com"
HEADERS = {"User-Agent": "Scraper/1.0 (+)"}
REQUEST_DELAY_SEC = 1.25  # be polite
OUT_DIR = Path("data/wordlists")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------- polite fetch ----------

def robots_allows(url: str, agent: str = HEADERS["User-Agent"]) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(agent, url)
    except Exception:
        # If robots is unreachable, allow but still be gentle.
        return True

def get(url: str) -> str:
    time.sleep(REQUEST_DELAY_SEC)
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


# ---------- utils ----------

def normalise_words(words: List[str]) -> List[str]:
    out, seen = [], set()
    for w in words:
        w = w.strip().lower()
        if not w:
            continue
        if not re.fullmatch(r"[a-z]+", w):  # letters only
            continue
        if len(w) < 4:  # NYT SB rule
            continue
        if w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out

def filter_by_pool(words: List[str], pool: Optional[str], center: Optional[str]) -> List[str]:
    if not pool and not center:
        return words
    pool = (pool or "").lower()
    center = (center or "").lower()
    keep = []
    for w in words:
        if center and center not in w:
            continue
        if pool and any(ch not in pool for ch in w):
            continue
        keep.append(w)
    return keep


# ---------- extraction (DOM-specific) ----------

def extract_from_alpha_inline(html: str) -> List[str]:
    """
    Extract only the answers rendered under #alpha-inner.
    Words are anchors inside 'td.bee-hover > a'.
    """
    soup = BeautifulSoup(html, "lxml")

    alpha = soup.select_one("#alpha-inner")
    if not alpha:
        return []

    # exact anchors for words
    anchors = alpha.select("td.bee-hover > a")
    if not anchors:
        # fallback: any anchors under #alpha-inner (still constrained to the block)
        anchors = alpha.select("a")

    words = [a.get_text(strip=True) for a in anchors if a and a.get_text(strip=True)]
    return normalise_words(words)


def extract_fallback(html: str) -> List[str]:
    """
    Safety fallback if #alpha-inner is missing.
    We still constrain to the main content area to avoid 'November' etc.
    """
    soup = BeautifulSoup(html, "lxml")
    content = soup.select_one("#content") or soup.select_one("#content-inner") \
               or soup.select_one("main") or soup.select_one("article") or soup

    tokens = re.findall(r"[A-Za-z]{3,}", content.get_text(" ", strip=True))
    return normalise_words(tokens)


# ---------- main flow ----------

def scrape_one(pid: int, pool: Optional[str], center: Optional[str], overwrite: bool) -> Optional[Path]:
    url = f"{BASE}/s/{pid}"

    if not robots_allows(url):
        print(f"[robots] Disallowed: {url}")
        return None

    try:
        html = get(url)
    except Exception as e:
        print(f"[fetch] {url} -> {e}")
        return None

    words = extract_from_alpha_inline(html)
    if not words:
        words = extract_fallback(html)

    if not words:
        print(f"[parse] {pid}: no words found")
        return None

    words = filter_by_pool(words, pool, center)

    payload = {
        "id": str(pid),
        "count": len(words),
        "words": words,
        "meta": {
            "source_url": url,
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "user_agent": HEADERS["User-Agent"],
            "pool": pool,
            "center": center,
        },
    }
    out_path = OUT_DIR / f"{pid}.json"
    if not out_path.exists() or overwrite:
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] {pid}: {len(words)} words -> {out_path}")
    return out_path


def scrape_ids(ids: List[int], pool: Optional[str], center: Optional[str], overwrite: bool) -> None:
    for pid in ids:
        scrape_one(pid, pool, center, overwrite)

def scrape_range(start: int, end: int, pool: Optional[str], center: Optional[str], overwrite: bool) -> None:
    step = 1 if end >= start else -1
    for pid in range(start, end + step, step):
        scrape_one(pid, pool, center, overwrite)


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Scrape sbsolver.com Spelling Bee answers (alphabetical list).")
    ap.add_argument("--url", help="Full page URL (e.g., https://www.sbsolver.com/s/2736)")
    ap.add_argument("--ids", nargs="*", type=int, help="One or more puzzle IDs (e.g., 2736 2735)")
    ap.add_argument("--range", nargs=2, type=int, metavar=("START", "END"),
                    help="Inclusive range of puzzle IDs (e.g., 1 2736)")
    ap.add_argument("--pool", help="Optional 7-letter pool for validation (e.g., denopux)")
    ap.add_argument("--center", help="Optional center letter (e.g., n)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing JSON")
    return ap.parse_args()

def main():
    args = parse_args()

    if args.url:
        m = re.search(r"/s/(\d+)", args.url)
        if not m:
            print("Could not detect puzzle id in URL.")
            return
        pid = int(m.group(1))
        scrape_one(pid, args.pool, args.center, args.overwrite)
        return

    if args.ids:
        scrape_ids(args.ids, args.pool, args.center, args.overwrite)
        return

    if args.range:
        start, end = args.range
        scrape_range(start, end, args.pool, args.center, args.overwrite)
        return

    print("Provide --url, --ids, or --range. See --help for examples.")

if __name__ == "__main__":
    main()
