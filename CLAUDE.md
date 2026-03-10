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

### What's Next

- **Evaluator market pricing is unreliable.** The evaluator uses WebSearch to find comparable prices but gets stale/sold listings it can't distinguish from active ones, making the "value for money" score untrustworthy. Needs research.


### Docs

- **`docs/plan.md`** — Original project plan, requirements, database schema ideas, cost estimates
- **`docs/research.md`** — Car knowledge base, engine/transmission data, platform details
