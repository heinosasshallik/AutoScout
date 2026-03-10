# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutoScout is a web scraper and AI-powered car evaluator for finding reliable used cars on auto24.ee (Estonia's largest vehicle classifieds site). It scrapes listings, evaluates them with Claude AI against specific buyer criteria (reliability, maintenance costs, value), and surfaces the best cars to go see in person.

**Key Goal:** Find low-maintenance, reliable petrol cars (Toyota, Lexus, Honda, Mazda) with the lowest total cost of ownership. Personal project — keep things simple.

## Development Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m playwright install chromium
./install_playwright_deps.sh

# Tests
pytest                                    # all tests
pytest -m "not integration"               # unit tests only
pytest -m integration                     # hits real auto24.ee
pytest tests/test_parser.py::TestParsePrice  # specific test

# Evaluate a single listing
python scripts/evaluate_listing.py 4281217
python scripts/evaluate_listing.py https://eng.auto24.ee/vehicles/4281217
```

## Architecture

### What's Built

- **`src/autoscout/scraper.py`** — Playwright + stealth scraper for auto24.ee. Handles Cloudflare, pagination, polite delays (5-10s).
- **`src/autoscout/parser.py`** — BeautifulSoup HTML parsers for search results and listing pages. CSS selectors target `div.result-row`, `table.main-data`, `div.vImages`, `div.vTechData`.
- **`src/autoscout/models.py`** — Pydantic models (`SearchResultItem`, `Listing`).
- **`src/autoscout/evaluator.py`** — Core evaluation logic: runs Claude Code CLI, parses structured output, computes weighted scores, saves results.
- **`src/autoscout/config.py`** — Config loading and validation (score weights sum to 1.0, categories match schema, search values map to known IDs).
- **`scripts/evaluate_listing.py`** — Standalone evaluation script. Scrapes one listing, sends to Claude Code CLI (`claude -p`) with `--json-schema` for structured output, computes weighted scores, saves results. Uses `--allowedTools Read,WebSearch,WebFetch`.
- **`scripts/pipeline.py`** — Pipeline orchestrator. Scrapes all matching listings across configured brands, skips already-evaluated ones, evaluates the rest with Claude, and displays ranked results. Supports `--limit` and `--dry-run`.
- **`config/`** — All user-editable configuration:
  - `search.json` — search filters (brands, fuel, transmission, price range)
  - `scoring.json` — score category weights (must sum to 1.0, categories must match eval-output-schema.json)
  - `evaluation.json` — evaluation model and max budget per listing
  - `prompt.md` — evaluation prompt sent to Claude (buyer profile, hard requirements, scoring rubric)
  - `eval-output-schema.json` — JSON schema for structured Claude output (verdict enum, score categories, etc.)
- **`listings/{id}/`** — Runtime output. Each listing gets `listing.json` (scraped) and `evaluation.json` (AI evaluation).
- **`tests/`** — Unit tests for parser, integration tests for scraper, canary tests for detecting site changes.
- **`scripts/discovery/`** — One-off scripts for discovering/verifying auto24.ee search form parameters.

### What's Next

- **Evaluator market pricing is unreliable.** The evaluator uses WebSearch to find comparable prices but gets stale/sold listings it can't distinguish from active ones, making the "value for money" score untrustworthy. Needs research.

### Evaluation Details

- **Verdicts:** `GO SEE IT` / `MAYBE` / `SKIP` (enum in JSON schema)
- **Score weights:** Defined in `config/scoring.json` (must sum to 1.0, categories must match `eval-output-schema.json`)
- **Model:** Configured in `config/evaluation.json` (currently `opus`)
- **Cost:** ~$0.50-$1.50 per evaluation (Claude Code with web search)

## Key Reference

### auto24.ee ID Mappings (in `scraper.py`)

```python
BRAND_IDS = {"toyota": 13, "lexus": 35, "honda": 1, "mazda": 6}
FUEL_IDS = {"petrol": 1, "diesel": 2, "hybrid": 5, "electric": 6}
TRANSMISSION_IDS = {"manual": 1, "automatic": 2}
```

### Buyer Hard Requirements (defined in `config/prompt.md`)

- Petrol only (no hybrids)
- Manual or torque converter auto only (reject CVT, eCVT, DCT)
- Toyota, Lexus, Honda, Mazda only
- Port injection preferred; direct injection penalized (except Mazda SkyActiv-G)

### Docs

- **`docs/plan.md`** — Original project plan, requirements, database schema ideas, cost estimates
- **`docs/research.md`** — Car knowledge base, engine/transmission data, platform details
