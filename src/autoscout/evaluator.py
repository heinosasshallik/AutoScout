"""Evaluate a car listing using Claude Code CLI."""

import json
import logging
import subprocess
from pathlib import Path

from autoscout.models import Listing
from autoscout.scraper import Auto24Scraper

logger = logging.getLogger(__name__)


def scrape_listing(listing_id: str, listings_dir: Path) -> Path:
    """Scrape a listing and save its data as JSON. Returns the output directory."""
    import asyncio

    out_dir = listings_dir / listing_id
    out_dir.mkdir(parents=True, exist_ok=True)

    async def _scrape() -> Listing:
        async with Auto24Scraper(headless=True) as scraper:
            return await scraper.get_listing(listing_id)

    listing = asyncio.run(_scrape())
    data = listing.model_dump(exclude={"raw_html"})
    out_path = out_dir / "listing.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved listing data to %s", out_path)
    return out_dir


async def scrape_listing_async(
    scraper: Auto24Scraper, listing_id: str, listings_dir: Path
) -> Path:
    """Scrape a listing using an existing scraper session. Returns the output directory."""
    out_dir = listings_dir / listing_id
    out_dir.mkdir(parents=True, exist_ok=True)

    listing = await scraper.get_listing(listing_id)
    data = listing.model_dump(exclude={"raw_html"})
    out_path = out_dir / "listing.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved listing data to %s", out_path)
    return out_dir


def run_claude_evaluation(
    listing_dir: Path, prompt: str, schema: dict,
    model: str = "sonnet", max_budget_usd: float = 5,
) -> dict:
    """Run Claude Code against a listing directory and return the structured evaluation."""
    schema_json = json.dumps(schema)

    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "json",
        "--json-schema", schema_json,
        "--model", model,
        "--max-budget-usd", str(max_budget_usd),
        "--allowedTools", "Read,WebSearch,WebFetch",
    ]

    logger.info("Running Claude Code evaluation for %s...", listing_dir.name)
    result = subprocess.run(
        cmd,
        cwd=listing_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude Code failed (exit {result.returncode}): {result.stderr}"
        )

    response = json.loads(result.stdout)
    return response


def parse_evaluation_response(response: dict) -> dict:
    """Extract the evaluation dict from a Claude Code JSON response."""
    return response.get("structured_output") or json.loads(response.get("result", "{}"))


def compute_weighted_score(scores: dict, score_weights: dict) -> float:
    """Compute weighted overall score from category scores."""
    total = sum(scores[k] * score_weights[k] for k in score_weights)
    return round(total, 2)


def save_evaluation(evaluation: dict, listing_dir: Path) -> Path:
    """Save evaluation JSON to listing directory. Returns the file path."""
    eval_path = listing_dir / "evaluation.json"
    eval_path.write_text(
        json.dumps(evaluation, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Saved evaluation to %s", eval_path)
    return eval_path


def evaluate_listing(
    listing_dir: Path, prompt: str, schema: dict, score_weights: dict,
    model: str = "sonnet", max_budget_usd: float = 5,
) -> tuple[dict, float]:
    """Full evaluation flow: run Claude, compute score, save.

    Returns (evaluation_dict, cost_usd).
    """
    response = run_claude_evaluation(listing_dir, prompt, schema, model, max_budget_usd)
    cost_usd = response.get("total_cost_usd", 0.0)
    evaluation = parse_evaluation_response(response)
    evaluation["weighted_score"] = compute_weighted_score(
        evaluation["scores"], score_weights
    )
    save_evaluation(evaluation, listing_dir)
    return evaluation, cost_usd


def display_result(evaluation: dict, score_weights: dict) -> None:
    """Print a formatted evaluation report."""
    v = evaluation["vehicle"]
    weighted_score = evaluation["weighted_score"]

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
