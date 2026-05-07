# Scraper Demo

Production-shape web scraper demonstrating the patterns I use on real client jobs.

## What it shows

- Static HTML with **BeautifulSoup**, JS-rendered with Playwright (drop-in)
- **SQLite** storage with deduplication via primary key
- **Retries** with exponential backoff
- **Polite rate limiting** per domain
- **Structured logging**
- **CSV/JSON export**

Two public sources, no auth, no ToS issues:
- `hn` — Hacker News front page (top stories)
- `github` — GitHub Trending (today)

## Architecture

```
   ┌────────────┐    ┌──────────────┐    ┌──────────────┐
   │  Fetcher   │ ─▶ │   Parser     │ ─▶ │   Storage    │
   │  retries   │    │ BeautifulSoup│    │  SQLite      │
   │  backoff   │    │  fields      │    │  PK dedup    │
   └────────────┘    └──────────────┘    └──────────────┘
                                               │
                                               ▼
                                    CSV / JSON export
```

## Quick start

```bash
pip install requests beautifulsoup4

python scraper.py --target hn
python scraper.py --target github --export csv --out trending.csv
python scraper.py --target hn --export json --out top.json
```

## Real sample output

Live runs against HN front page and GitHub Trending — committed in [`sample/`](sample/).

[`sample/hn-top.csv`](sample/hn-top.csv) — 30 stories, generated `python scraper.py --target hn --export csv --out sample/hn-top.csv`:

```csv
post_id,title,url,meta
48023861,Three Inverse Laws of AI,https://susam.net/inverse-laws-of-robotics.html,"{""score"": ""81 points""}"
48024364,UK: Two millionth electric car registered as market rebounds strongly,https://www.smmt.co.uk/...,"{""score"": ""21 points""}"
48019163,Async Rust never left the MVP state,https://tweedegolf.nl/en/blog/237/async-rust-never-left-the-mvp-state,"{""score"": ""345 points""}"
```

[`sample/trending.json`](sample/trending.json) — same shape, GitHub Trending. Re-run any time, dedup keeps SQLite clean.

## What you get when you hire me

I have built scrapers for everything from Amazon listings to government registries to private SaaS dashboards. The shape is the same as this demo, scaled to your data:

- Identify the right rendering layer (static HTML, JS-rendered, or API behind the page)
- Build the extractor with retries plus rate limiting plus structured logging
- Output as CSV, JSON, or push directly into your database
- Handle anti-bot protection with Playwright plus rotating user agents if needed
- Document the code so you can run it yourself or hand it to your team

## Hire me for similar work

Contact: Nordikdata@proton.me
Profiles: Freelancer.com/u/nordikdata · Reddit u/nordikdata

Typical project sizes: small scrapers ($50-150), production pipelines ($300-1000).
