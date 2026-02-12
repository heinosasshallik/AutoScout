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
- **`scripts/evaluate_listing.py`** — Standalone evaluation script. Scrapes one listing, sends to Claude Code CLI (`claude -p`) with `--json-schema` for structured output, computes weighted scores, saves results. Uses `--allowedTools Read,WebSearch,WebFetch`.
- **`prompts/evaluate.md`** — Evaluation prompt: buyer profile, hard requirements, research instructions, scoring rubric.
- **`listings/{id}/`** — Runtime output. Each listing gets `listing.json` (scraped) and `evaluation.json` (AI evaluation).
- **`tests/`** — Unit tests for parser, integration tests for scraper, canary tests for detecting site changes.

### What's Next

Pipeline orchestration: a script that scrapes all matching listings, skips already-evaluated ones, evaluates the rest, and shows ranked results. Storage approach TBD — keeping it simple (files or lightweight SQLite) based on what the pipeline actually needs.

### Evaluation Details

- **Verdicts:** `GO SEE IT` / `MAYBE` / `SKIP` (enum in JSON schema)
- **Score weights:** Mechanical reliability 20%, Maintenance cost 20%, Value 20%, Safety 15%, Cosmetic 10%, Spec match 10%, Seller trust 5%
- **Cost:** ~$1-5 per evaluation (Claude Code with web search)

## Key Reference

### Brand IDs (auto24.ee)

```python
BRAND_IDS = {"toyota": 13, "lexus": 35, "honda": 1, "mazda": 6}
```

### Buyer Hard Requirements

- Petrol only (no hybrids)
- Manual or torque converter auto only (reject CVT, eCVT, DCT)
- Toyota, Lexus, Honda, Mazda only
- Port injection preferred; direct injection penalized (except Mazda SkyActiv-G)

### Docs

- **`docs/plan.md`** — Original project plan, requirements, database schema ideas, cost estimates
- **`docs/research.md`** — Car knowledge base, engine/transmission data, platform details
