"""Configuration loading and validation."""

import json
from pathlib import Path

from autoscout.scraper import BRAND_IDS, FUEL_IDS, TRANSMISSION_IDS


def load_config(config_dir: Path) -> tuple[dict, dict, dict, str, dict]:
    """Load configuration from a config directory.

    Returns (search_cfg, score_weights, eval_cfg, prompt, schema).
    Raises ValueError if config is invalid.
    """
    search_cfg = json.loads((config_dir / "search.json").read_text(encoding="utf-8"))
    score_weights = json.loads((config_dir / "scoring.json").read_text(encoding="utf-8"))
    eval_cfg = json.loads((config_dir / "evaluation.json").read_text(encoding="utf-8"))
    prompt = (config_dir / "prompt.md").read_text(encoding="utf-8")
    schema = json.loads((config_dir / "eval-output-schema.json").read_text(encoding="utf-8"))

    validate_config(search_cfg, score_weights, schema)
    return search_cfg, score_weights, eval_cfg, prompt, schema


def validate_config(search_cfg: dict, score_weights: dict, schema: dict) -> None:
    """Validate configuration. Raises ValueError on problems."""
    _validate_search(search_cfg)
    _validate_score_weights(score_weights, schema)


def _validate_search(cfg: dict) -> None:
    """Check that search config values map to known IDs."""
    for brand in cfg.get("brands", []):
        if brand not in BRAND_IDS:
            raise ValueError(
                f"Unknown brand {brand!r} in search.json. "
                f"Valid brands: {sorted(BRAND_IDS)}"
            )

    for fuel in cfg.get("fuel", []):
        if fuel not in FUEL_IDS:
            raise ValueError(
                f"Unknown fuel type {fuel!r} in search.json. "
                f"Valid fuel types: {sorted(FUEL_IDS)}"
            )

    for trans in cfg.get("transmission", []):
        if trans not in TRANSMISSION_IDS:
            raise ValueError(
                f"Unknown transmission {trans!r} in search.json. "
                f"Valid transmissions: {sorted(TRANSMISSION_IDS)}"
            )


def _validate_score_weights(score_weights: dict, schema: dict) -> None:
    """Check that score weights sum to 1.0 and match schema categories."""
    # Check sum
    total = sum(score_weights.values())
    if abs(total - 1.0) > 0.001:
        raise ValueError(
            f"Score weights must sum to 1.0, got {total}"
        )

    # Check keys match schema
    schema_keys = set(schema["properties"]["scores"]["properties"].keys())
    weight_keys = set(score_weights.keys())

    missing = schema_keys - weight_keys
    if missing:
        raise ValueError(
            f"scoring.json is missing categories from schema: {sorted(missing)}"
        )

    extra = weight_keys - schema_keys
    if extra:
        raise ValueError(
            f"scoring.json has categories not in schema: {sorted(extra)}"
        )
