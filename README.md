# AutoScout

Scrapes [auto24.ee](https://www.auto24.ee) for used car listings, evaluates them
with Claude AI, and surfaces the best cars to go see in person.

Built for a specific use case: finding a reliable, low-maintenance petrol car in
Estonia (Toyota, Lexus, Honda, Mazda) with the lowest total cost of ownership.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m playwright install chromium
./install_playwright_deps.sh
```

## Configuration

Edit the files in `config/` to customize your search and evaluation criteria:

- **`config/search.json`** — Search filters (brands, fuel type, price range)
- **`config/scoring.json`** — Score category weights for ranking
- **`config/prompt.md`** — Evaluation prompt sent to Claude AI (buyer profile, hard requirements, scoring rubric)
- **`config/eval-output-schema.json`** — JSON output schema for Claude's structured response

## Usage

Evaluate a single listing:

```bash
python scripts/evaluate_listing.py 4281217
python scripts/evaluate_listing.py https://eng.auto24.ee/vehicles/4281217
```

Results are saved to `listings/{id}/evaluation.json`.

## Docs

- [Project plan](docs/plan.md) — requirements, architecture, cost estimates
- [Research](docs/research.md) — car knowledge base, platform details, sources
