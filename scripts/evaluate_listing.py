#!/usr/bin/env python3
"""Scrape a single listing, evaluate it with Claude Code, and display results.

Usage:
    python scripts/evaluate_listing.py 4244561
    python scripts/evaluate_listing.py https://eng.auto24.ee/vehicles/4244561
"""

import logging
import re
import sys
from pathlib import Path

from autoscout.config import load_config
from autoscout.evaluator import display_result, evaluate_listing, scrape_listing

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


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <listing_id_or_url>", file=sys.stderr)
        sys.exit(1)

    _search_cfg, score_weights, prompt, schema = load_config(CONFIG_DIR)
    listing_id = extract_listing_id(sys.argv[1])

    # Scrape
    logger.info("Scraping listing %s", listing_id)
    listing_dir = scrape_listing(listing_id, LISTINGS_DIR)

    # Evaluate and display
    evaluation, cost_usd = evaluate_listing(listing_dir, prompt, schema, score_weights)
    display_result(evaluation, score_weights)
    print(f"--- Cost: ${cost_usd:.2f} ---\n")


if __name__ == "__main__":
    main()
