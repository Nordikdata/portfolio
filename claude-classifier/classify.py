"""Batch-classify texts with the Claude API.

Usage:
    python classify.py --input reviews.csv --output classified.csv \\
        --column text --labels "positive,negative,neutral"

Features:
- Cost cap (--cost-cap-eur, default 0.50)
- Token usage logged per row
- Resumable: skips rows already processed in the output file
- Fixed-format output: original columns + label, confidence, reasoning

Designed for jobs where a client has a CSV/JSON of free-text and wants
each row tagged. Common use cases: support tickets, reviews, survey
responses, job postings, news articles, social media posts.
"""

import argparse
import csv
import os
import sys
from pathlib import Path

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")

# Sonnet 4.5 pricing (USD per 1M tokens) — adjust for your model
INPUT_USD_PER_M = 3.0
OUTPUT_USD_PER_M = 15.0
USD_TO_EUR = 0.92


def make_prompt(text: str, labels: list[str]) -> str:
    label_list = ", ".join(f"'{lab}'" for lab in labels)
    return (
        f"Classify the text below into exactly one of these labels: {label_list}.\n\n"
        f"Respond in this exact format:\n"
        f"LABEL: <one of the labels>\n"
        f"CONFIDENCE: <0-100>\n"
        f"REASONING: <one short sentence>\n\n"
        f"Text:\n{text}"
    )


def parse_response(text: str) -> dict:
    label, confidence, reasoning = "", 0, ""
    for line in text.splitlines():
        if line.startswith("LABEL:"):
            label = line.split(":", 1)[1].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                confidence = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
    return {"label": label, "confidence": confidence, "reasoning": reasoning}


def cost_eur(in_tokens: int, out_tokens: int) -> float:
    return (
        (in_tokens / 1_000_000) * INPUT_USD_PER_M
        + (out_tokens / 1_000_000) * OUTPUT_USD_PER_M
    ) * USD_TO_EUR


def already_processed(output_path: Path) -> set[int]:
    if not output_path.exists():
        return set()
    with output_path.open() as f:
        reader = csv.DictReader(f)
        return {int(row["_row_index"]) for row in reader if row.get("_row_index")}


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch classify a CSV with Claude")
    ap.add_argument("--input", required=True, help="Input CSV path")
    ap.add_argument("--output", required=True, help="Output CSV path")
    ap.add_argument("--column", required=True, help="Column to classify")
    ap.add_argument("--labels", required=True, help="Comma-separated label list")
    ap.add_argument("--cost-cap-eur", type=float, default=0.50)
    args = ap.parse_args()

    labels = [lab.strip() for lab in args.labels.split(",") if lab.strip()]
    if len(labels) < 2:
        print("Need at least 2 labels", file=sys.stderr)
        return 1

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY in your environment", file=sys.stderr)
        return 1

    in_path = Path(args.input)
    out_path = Path(args.output)
    if not in_path.exists():
        print(f"Input not found: {in_path}", file=sys.stderr)
        return 1

    done_rows = already_processed(out_path)
    if done_rows:
        print(f"Resuming, skipping {len(done_rows)} rows already in {out_path}")

    client = anthropic.Anthropic()
    total_cost = 0.0
    total_tokens_in = 0
    total_tokens_out = 0
    processed = 0

    with in_path.open() as fin, out_path.open("a", newline="") as fout:
        reader = csv.DictReader(fin)
        if args.column not in reader.fieldnames:
            print(f"Column '{args.column}' not in CSV (cols: {reader.fieldnames})", file=sys.stderr)
            return 1

        out_fields = list(reader.fieldnames) + ["label", "confidence", "reasoning", "_row_index"]
        writer = csv.DictWriter(fout, fieldnames=out_fields)
        if out_path.stat().st_size == 0:
            writer.writeheader()

        for idx, row in enumerate(reader):
            if idx in done_rows:
                continue
            if total_cost >= args.cost_cap_eur:
                print(f"Cost cap reached ({total_cost:.4f}€), stopping at row {idx}")
                break

            text = (row.get(args.column) or "").strip()
            if not text:
                continue

            try:
                msg = client.messages.create(
                    model=MODEL,
                    max_tokens=200,
                    messages=[{"role": "user", "content": make_prompt(text, labels)}],
                )
            except Exception as e:
                print(f"  row {idx}: API error: {e}", file=sys.stderr)
                continue

            parsed = parse_response(msg.content[0].text)
            in_tok = msg.usage.input_tokens
            out_tok = msg.usage.output_tokens
            row_cost = cost_eur(in_tok, out_tok)
            total_cost += row_cost
            total_tokens_in += in_tok
            total_tokens_out += out_tok
            processed += 1

            row.update({
                "label": parsed["label"],
                "confidence": parsed["confidence"],
                "reasoning": parsed["reasoning"],
                "_row_index": idx,
            })
            writer.writerow(row)
            fout.flush()
            print(f"  row {idx}: {parsed['label']} ({parsed['confidence']}) — {row_cost:.4f}€")

    print()
    print(f"Done. Processed {processed} rows.")
    print(f"Tokens: {total_tokens_in} in / {total_tokens_out} out")
    print(f"Total cost: {total_cost:.4f}€")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
