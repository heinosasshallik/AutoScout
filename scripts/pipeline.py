#!/usr/bin/env python3
"""Search auto24.ee, evaluate new listings, and rank results.

Usage:
    python scripts/pipeline.py                # full run
    python scripts/pipeline.py --limit 2      # evaluate at most 2 new listings (for testing)
    python scripts/pipeline.py --dry-run      # search only, show what would be evaluated
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from autoscout.config import load_config
from autoscout.evaluator import (
    display_result,
    evaluate_listing,
    save_evaluation,
    scrape_listing_async,
)
from autoscout.scraper import BRAND_IDS, FUEL_IDS, TRANSMISSION_IDS, Auto24Scraper

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
LISTINGS_DIR = ROOT_DIR / "listings"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)


def is_evaluated(listing_id: str) -> bool:
    """Check if a listing already has an evaluation."""
    return (LISTINGS_DIR / listing_id / "evaluation.json").exists()


async def search_all_brands(search_cfg: dict) -> list[dict]:
    """Search auto24.ee for all configured brands and return unique listings.

    Returns list of dicts with at least 'id' and 'brand' keys.
    """
    fuel_ids = [FUEL_IDS[f] for f in search_cfg.get("fuel", [])]
    trans_ids = [TRANSMISSION_IDS[t] for t in search_cfg.get("transmission", [])]
    price_min = search_cfg.get("price_min")
    price_max = search_cfg.get("price_max")

    seen_ids: set[str] = set()
    all_listings: list[dict] = []

    async with Auto24Scraper(headless=True) as scraper:
        for brand in search_cfg["brands"]:
            brand_id = BRAND_IDS[brand]
            logger.info("Searching %s (brand_id=%d)...", brand, brand_id)

            results = await scraper.search_all_pages(
                brand_id=brand_id,
                price_min=price_min,
                price_max=price_max,
                fuel_types=fuel_ids or None,
                transmission_types=trans_ids or None,
            )

            for item in results:
                if item.id not in seen_ids:
                    seen_ids.add(item.id)
                    all_listings.append({
                        "id": item.id,
                        "brand": brand,
                        "title": item.title,
                        "price_eur": item.price_eur,
                        "year": item.year,
                        "mileage_km": item.mileage_km,
                    })

            logger.info("  %s: %d results (%d new)", brand, len(results),
                        sum(1 for r in results if r.id not in seen_ids or True))

    logger.info("Total unique listings found: %d", len(all_listings))
    return all_listings


async def scrape_new_listings(
    listing_ids: list[str],
) -> list[Path]:
    """Scrape listings that don't have listing.json yet. Returns output dirs."""
    to_scrape = [
        lid for lid in listing_ids
        if not (LISTINGS_DIR / lid / "listing.json").exists()
    ]

    if not to_scrape:
        logger.info("All listings already scraped")
        return [LISTINGS_DIR / lid for lid in listing_ids]

    logger.info("Scraping %d new listings...", len(to_scrape))
    async with Auto24Scraper(headless=True) as scraper:
        for lid in to_scrape:
            await scrape_listing_async(scraper, lid, LISTINGS_DIR)

    return [LISTINGS_DIR / lid for lid in listing_ids]


def load_existing_evaluations() -> list[dict]:
    """Load all existing evaluation.json files from listings/."""
    evaluations = []
    if not LISTINGS_DIR.exists():
        return evaluations
    for eval_path in LISTINGS_DIR.glob("*/evaluation.json"):
        try:
            evaluation = json.loads(eval_path.read_text(encoding="utf-8"))
            evaluation["_listing_id"] = eval_path.parent.name
            evaluations.append(evaluation)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Skipping bad evaluation %s: %s", eval_path, e)
    return evaluations


def display_rankings(evaluations: list[dict], score_weights: dict) -> None:
    """Display all evaluations ranked by weighted score."""
    ranked = sorted(evaluations, key=lambda e: e.get("weighted_score", 0), reverse=True)

    print("\n" + "=" * 60)
    print("  RANKINGS")
    print("=" * 60)

    for i, ev in enumerate(ranked, 1):
        v = ev.get("vehicle", {})
        verdict = ev.get("verdict", "?")
        score = ev.get("weighted_score", 0)
        lid = ev.get("_listing_id", "?")
        make = v.get("make", "?")
        model = v.get("model", "?")
        year = v.get("year", "?")
        mileage = v.get("mileage_km", 0)
        engine = v.get("engine_code", "?")

        print(f"\n  #{i}  [{verdict}]  {score}/10  —  {make} {model} ({year})")
        print(f"       {engine}, {mileage:,} km  —  listing {lid}")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="AutoScout pipeline")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max new listings to evaluate (for testing)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Search only — show what would be evaluated, don't run Claude",
    )
    args = parser.parse_args()

    search_cfg, score_weights, eval_cfg, prompt, schema = load_config(CONFIG_DIR)

    # Step 1: Search
    logger.info("Step 1: Searching auto24.ee...")
    found = asyncio.run(search_all_brands(search_cfg))

    if not found:
        logger.info("No listings found matching search criteria")
        sys.exit(0)

    # Step 2: Filter out already-evaluated
    new_ids = [item["id"] for item in found if not is_evaluated(item["id"])]
    already = len(found) - len(new_ids)
    logger.info("Found %d listings: %d new, %d already evaluated",
                len(found), len(new_ids), already)

    if args.limit is not None:
        new_ids = new_ids[:args.limit]
        logger.info("Limiting to %d new listings", len(new_ids))

    if args.dry_run:
        print(f"\nDry run: {len(new_ids)} listings to evaluate:")
        for lid in new_ids:
            item = next(i for i in found if i["id"] == lid)
            print(f"  {lid}: {item['title']} — €{item.get('price_eur', '?')}")
        sys.exit(0)

    # Step 3: Scrape new listings
    total_cost = 0.0
    if new_ids:
        logger.info("Step 2: Scraping %d new listings...", len(new_ids))
        asyncio.run(scrape_new_listings(new_ids))

        # Step 4: Evaluate with Claude
        logger.info("Step 3: Evaluating %d listings with Claude...", len(new_ids))
        for i, lid in enumerate(new_ids, 1):
            listing_dir = LISTINGS_DIR / lid
            logger.info("Evaluating %d/%d: listing %s", i, len(new_ids), lid)
            try:
                evaluation, cost_usd = evaluate_listing(
                    listing_dir, prompt, schema, score_weights,
                    model=eval_cfg["model"],
                    max_budget_usd=eval_cfg["max_budget_usd"],
                )
                total_cost += cost_usd
                display_result(evaluation, score_weights)
                logger.info("  Cost: $%.2f (running total: $%.2f)", cost_usd, total_cost)
            except Exception as e:
                logger.error("Failed to evaluate listing %s: %s", lid, e)
    else:
        logger.info("No new listings to evaluate")

    # Step 5: Rank all evaluated listings
    logger.info("Step 4: Ranking all evaluated listings...")
    all_evaluations = load_existing_evaluations()
    if all_evaluations:
        display_rankings(all_evaluations, score_weights)
    else:
        logger.info("No evaluations to rank")

    # Cost summary
    if total_cost > 0:
        print(f"--- Total evaluation cost: ${total_cost:.2f} ({len(new_ids)} listings) ---\n")


if __name__ == "__main__":
    main()
