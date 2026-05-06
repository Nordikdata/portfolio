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

Sample output (`trending.csv`):

```csv
post_id,title,url,meta
"openai/codex","openai/codex","https://github.com/openai/codex","{""description"": ""..."", ""stars"": ""3,420""}"
```

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
