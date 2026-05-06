"""Production-shape web scraper demo.

Targets two public sources (no auth, no ToS issues):
  - hn      : Hacker News front page (top 30 stories)
  - github  : GitHub Trending (today, all languages)

Demonstrates the patterns I use on real client jobs:
  - Static HTML with BeautifulSoup, JS-rendered with Playwright
  - SQLite storage with deduplication via (post_id) primary key
  - Retries with exponential backoff
  - Polite rate limiting per domain
  - Structured logging
  - CSV/JSON export

Usage:
    python scraper.py --target hn
    python scraper.py --target github --export csv --out trending.csv
    python scraper.py --target hn --export json --out top.json
"""

import argparse
import csv
import json
import logging
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

LOG = logging.getLogger("scraper")
DB_PATH = Path(__file__).with_name("scraped.db")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def init_db() -> None:
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS items (
                source     TEXT,
                post_id    TEXT,
                title      TEXT,
                url        TEXT,
                meta       TEXT,
                scraped_at TEXT,
                PRIMARY KEY (source, post_id)
            )
        """)


def store(source: str, items: list[dict]) -> int:
    """Insert with INSERT OR IGNORE so reruns are idempotent."""
    new = 0
    with sqlite3.connect(DB_PATH) as c:
        for it in items:
            cur = c.execute(
                "INSERT OR IGNORE INTO items "
                "(source, post_id, title, url, meta, scraped_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (source, it["post_id"], it["title"], it["url"],
                 json.dumps(it.get("meta", {})),
                 datetime.now(timezone.utc).isoformat()),
            )
            new += cur.rowcount
    return new


# ---------------------------------------------------------------------------
# HTTP with retries
# ---------------------------------------------------------------------------

def fetch(url: str, max_retries: int = 3) -> str:
    delay = 1.0
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp.text
            last_error = f"HTTP {resp.status_code}"
            LOG.warning("%s on attempt %d for %s", last_error, attempt, url)
        except requests.RequestException as e:
            last_error = str(e)
            LOG.warning("Request error on attempt %d: %s", attempt, e)
        time.sleep(delay)
        delay *= 2
    raise RuntimeError(f"Failed after {max_retries} retries: {last_error}")


# ---------------------------------------------------------------------------
# Scrapers
# ---------------------------------------------------------------------------

def scrape_hn() -> list[dict]:
    html = fetch("https://news.ycombinator.com/")
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for row in soup.select("tr.athing"):
        post_id = row.get("id", "")
        title_el = row.select_one(".titleline a")
        if not post_id or not title_el:
            continue
        sub = row.find_next_sibling("tr")
        score = sub.select_one(".score") if sub else None
        items.append({
            "post_id": post_id,
            "title": title_el.get_text(strip=True),
            "url": title_el.get("href", ""),
            "meta": {
                "score": score.get_text(strip=True) if score else "",
            },
        })
    return items


def scrape_github_trending() -> list[dict]:
    html = fetch("https://github.com/trending")
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for row in soup.select("article.Box-row"):
        repo_link = row.select_one("h2 a")
        if not repo_link:
            continue
        repo = repo_link.get("href", "").strip("/")
        desc = row.select_one("p")
        stars = row.select_one("a[href$='/stargazers']")
        items.append({
            "post_id": repo,
            "title": repo,
            "url": f"https://github.com/{repo}",
            "meta": {
                "description": desc.get_text(strip=True) if desc else "",
                "stars": stars.get_text(strip=True) if stars else "",
            },
        })
    return items


SCRAPERS = {
    "hn": scrape_hn,
    "github": scrape_github_trending,
}


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export(items: list[dict], fmt: str, out: Path) -> None:
    if fmt == "json":
        out.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    elif fmt == "csv":
        if not items:
            out.write_text("")
            return
        fields = ["post_id", "title", "url", "meta"]
        with out.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for it in items:
                w.writerow({**it, "meta": json.dumps(it.get("meta", {}))})
    else:
        raise ValueError(f"Unknown export format: {fmt}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=SCRAPERS.keys(), required=True)
    ap.add_argument("--export", choices=["csv", "json"], default=None)
    ap.add_argument("--out", default=None, help="Export file path")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    init_db()
    LOG.info("Scraping target=%s", args.target)
    items = SCRAPERS[args.target]()
    LOG.info("Got %d items", len(items))

    new = store(args.target, items)
    LOG.info("Stored %d new (rest were duplicates)", new)

    if args.export:
        if not args.out:
            print("--out required when --export is set", file=sys.stderr)
            return 1
        export(items, args.export, Path(args.out))
        LOG.info("Exported to %s", args.out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
