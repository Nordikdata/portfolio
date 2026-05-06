# Claude Classifier

Batch-classify any CSV column with the Claude API. Built-in cost cap, token tracking, and resume support.

Use it for: support tickets, product reviews, survey responses, news articles, social posts, job listings, anything with free text that needs a tag.

## What it does

```
input.csv (any columns + a free-text column)
        │
        ▼
   classify.py  ──▶  Claude API  ──▶  classified.csv
        │                              (original cols + label,
        │                               confidence, reasoning)
        └─ token + cost tracking, daily cap, resumable
```

## Quick start

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...

python classify.py \
    --input sample/reviews.csv \
    --output classified.csv \
    --column text \
    --labels "positive,negative,neutral,mixed" \
    --cost-cap-eur 0.10
```

Output (excerpt):

| id | text | label | confidence | reasoning |
| -- | ---- | ----- | ---------- | --------- |
| 1 | The shipping was slow but the product itself is excellent... | mixed | 85 | Praises product, complains about shipping. |
| 2 | Total waste of money. Broke after one week... | negative | 95 | Strong negative tone, defective product, no support. |
| 4 | Best purchase I made this year... | positive | 98 | Unambiguous praise. |

## Cost example

Classifying 1000 product reviews with Sonnet 4.5: roughly **0,05 €** total. Cost cap stops the run cold if you exceed it.

## Resume

If the run aborts (cost cap, network drop, Ctrl-C), just rerun the same command. Already-classified rows are skipped.

## Configuration

| Flag | Default | Meaning |
| --- | --- | --- |
| `--cost-cap-eur` | 0.50 | Stop after this much spent |
| `--column` | required | CSV column to classify |
| `--labels` | required | Comma-separated label list (min 2) |
| Env `CLAUDE_MODEL` | claude-sonnet-4-5 | Override model |

## Hire me for similar work

I build data engineering and automation systems on a fixed-price basis.
Typical projects: scrapers ($50-150), classifiers ($100-300), full pipelines ($300-1000).

Contact: Nordikdata@proton.me
Profiles: Freelancer.com/u/nordikdata · Reddit u/nordikdata
