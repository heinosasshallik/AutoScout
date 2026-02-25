#!/usr/bin/env python3
"""Run evaluations across multiple models for comparison.

This was a one-off research script used to compare Opus, Sonnet, and Haiku
on the same set of listings. Results are in this directory. See aggregate-report.md
for findings.

Usage (from repo root):
    python docs/reference-data/run_model_comparison.py
"""

import json
import logging
import time
from pathlib import Path

from autoscout.config import load_config
from autoscout.evaluator import (
    compute_weighted_score,
    parse_evaluation_response,
    run_claude_evaluation,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT_DIR / "config"
LISTINGS_DIR = ROOT_DIR / "listings"
REFERENCE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

LISTING_IDS = ["3872109", "4272435", "4280612", "4280818", "4281378"]
MODELS = ["sonnet", "haiku"]


def main() -> None:
    _search_cfg, score_weights, _eval_cfg, prompt, schema = load_config(CONFIG_DIR)

    for listing_id in LISTING_IDS:
        listing_dir = LISTINGS_DIR / listing_id
        if not listing_dir.exists():
            logger.warning("Listing dir %s not found, skipping", listing_dir)
            continue

        for model in MODELS:
            out_dir = REFERENCE_DIR / listing_id / model
            eval_path = out_dir / "evaluation.json"

            if eval_path.exists():
                logger.info("Already exists: %s — skipping", eval_path)
                continue

            out_dir.mkdir(parents=True, exist_ok=True)

            logger.info("=== Evaluating %s with %s ===", listing_id, model)
            start = time.time()

            try:
                response = run_claude_evaluation(
                    listing_dir, prompt, schema,
                    model=model, max_budget_usd=5,
                )
                elapsed = time.time() - start
                cost_usd = response.get("total_cost_usd", 0.0)

                evaluation = parse_evaluation_response(response)
                evaluation["weighted_score"] = compute_weighted_score(
                    evaluation["scores"], score_weights
                )
                evaluation["_meta"] = {
                    "model": model,
                    "listing_id": listing_id,
                    "cost_usd": round(cost_usd, 4),
                    "elapsed_seconds": round(elapsed, 1),
                }

                eval_path.write_text(
                    json.dumps(evaluation, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                logger.info(
                    "Done: %s/%s — score=%.2f, verdict=%s, cost=$%.2f, time=%.0fs",
                    listing_id, model,
                    evaluation["weighted_score"],
                    evaluation["verdict"],
                    cost_usd, elapsed,
                )

            except Exception:
                logger.exception("Failed: %s/%s", listing_id, model)
                continue


if __name__ == "__main__":
    main()
