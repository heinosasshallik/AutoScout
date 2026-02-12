#!/usr/bin/env python3
"""Scrape a listing, evaluate it with Claude Code, and display results.

Usage:
    python scripts/evaluate_listing.py 4244561
    python scripts/evaluate_listing.py https://eng.auto24.ee/vehicles/4244561
"""

import asyncio
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

from autoscout.config import load_config
from autoscout.scraper import Auto24Scraper

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
LISTINGS_DIR = ROOT_DIR / "listings"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


def extract_listing_id(arg: str) -> str:
    """Extract numeric listing ID from a URL or bare ID string."""
    if re.fullmatch(r"\d+", arg):
        return arg
    m = re.search(r"/vehicles/(\d+)", arg) or re.search(r"[?&]id=(\d+)", arg)
    if m:
        return m.group(1)
    raise ValueError(f"Cannot extract listing ID from: {arg}")


async def scrape_listing(listing_id: str) -> Path:
    """Scrape a listing and save its data as JSON. Returns the output directory."""
    out_dir = LISTINGS_DIR / listing_id
    out_dir.mkdir(parents=True, exist_ok=True)

    async with Auto24Scraper(headless=True) as scraper:
        listing = await scraper.get_listing(listing_id)

    data = listing.model_dump(exclude={"raw_html"})
    out_path = out_dir / "listing.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved listing data to %s", out_path)
    return out_dir


def run_claude_evaluation(listing_dir: Path, prompt: str, schema: dict) -> dict:
    """Run Claude Code against the listing and return structured evaluation."""
    schema_json = json.dumps(schema)

    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "json",
        "--json-schema", schema_json,
        "--max-budget-usd", "5",
        "--allowedTools", "Read,WebSearch,WebFetch",
    ]

    logger.info("Running Claude Code evaluation...")
    result = subprocess.run(
        cmd,
        cwd=listing_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Claude Code failed (exit %d): %s", result.returncode, result.stderr)
        sys.exit(1)

    response = json.loads(result.stdout)
    return response


def compute_weighted_score(scores: dict, score_weights: dict) -> float:
    """Compute weighted overall score from category scores."""
    total = sum(scores[k] * score_weights[k] for k in score_weights)
    return round(total, 2)


def display_result(evaluation: dict, weighted_score: float, score_weights: dict) -> None:
    """Print a formatted evaluation report."""
    v = evaluation["vehicle"]
    print("\n" + "=" * 60)
    print(f"  {v['make']} {v['model']} ({v['year']})")
    print(f"  Engine: {v['engine_code']} ({v['injection_type']})")
    print(f"  Transmission: {v['transmission_type']}")
    print(f"  Mileage: {v['mileage_km']:,} km")
    print("=" * 60)

    print(f"\n{evaluation['summary']}\n")

    print("--- Scores ---")
    scores = evaluation["scores"]
    reasoning = evaluation["score_reasoning"]
    for key, weight in score_weights.items():
        label = key.replace("_", " ").title()
        print(f"  {label}: {scores[key]}/10 (weight {weight:.0%})")
        print(f"    {reasoning[key]}")
    print(f"\n  WEIGHTED OVERALL: {weighted_score}/10\n")

    if evaluation["green_flags"]:
        print("--- Green Flags ---")
        for flag in evaluation["green_flags"]:
            print(f"  + {flag}")
        print()

    if evaluation["red_flags"]:
        print("--- Red Flags ---")
        for flag in evaluation["red_flags"]:
            print(f"  ! {flag}")
        print()

    print("--- Research ---")
    print(f"  {evaluation['research_findings']}\n")

    verdict = evaluation["verdict"]
    print(f"--- Verdict: {verdict} ---")
    print(f"  {evaluation['verdict_reasoning']}\n")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <listing_id_or_url>", file=sys.stderr)
        sys.exit(1)

    search_cfg, score_weights, prompt, schema = load_config(CONFIG_DIR)
    listing_id = extract_listing_id(sys.argv[1])

    # Step 1: Scrape
    logger.info("Scraping listing %s", listing_id)
    listing_dir = asyncio.run(scrape_listing(listing_id))

    # Step 2: Evaluate with Claude Code
    response = run_claude_evaluation(listing_dir, prompt, schema)
    evaluation = response.get("structured_output") or json.loads(response.get("result", "{}"))

    # Step 3: Score and display
    weighted_score = compute_weighted_score(evaluation["scores"], score_weights)
    display_result(evaluation, weighted_score, score_weights)

    # Save full evaluation
    eval_path = listing_dir / "evaluation.json"
    evaluation["weighted_score"] = weighted_score
    eval_path.write_text(json.dumps(evaluation, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved evaluation to %s", eval_path)


if __name__ == "__main__":
    main()
