# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AutoScout is a web scraper and AI-powered car evaluator for finding reliable used cars on auto24.ee (Estonia's largest vehicle classifieds site). The system scrapes listings, evaluates them with Claude AI against specific buyer criteria (focusing on reliability, maintenance costs, and value), and produces a ranked list of cars worth seeing in person.

**Key Goal:** Find low-maintenance, reliable petrol cars (Toyota, Lexus, Honda, Mazda) with the lowest total cost of ownership.

## Development Commands

### Setup

```bash
# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Install Playwright browsers and system dependencies
python -m playwright install chromium
./install_playwright_deps.sh  # Installs system libs (will prompt for sudo)
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py

# Run only unit tests (skip integration tests that hit real services)
pytest -m "not integration"

# Run with verbose output
pytest -v

# Run specific test class or method
pytest tests/test_parser.py::TestParsePrice
pytest tests/test_parser.py::TestParsePrice::test_euro_sign_suffix
```

**Note:** Integration tests against real HTML fixtures require running the scraper discovery mode first to fetch fixtures. See "Scraper Discovery Mode" below.

### Running the Scraper

The scraper uses Playwright with stealth mode to handle auto24.ee's Cloudflare protection. Currently implemented scraper features:

```python
# Example usage (from Python REPL or script):
from autoscout.scraper import Auto24Scraper, BRAND_IDS

async with Auto24Scraper(headless=True) as scraper:
    # Search for Toyota listings from 2007-2020
    results = await scraper.search(
        brand_id=BRAND_IDS["toyota"],
        year_min=2007,
        year_max=2020
    )

    # Get full listing details
    listing = await scraper.get_listing("4244561")
```

**Scraper Discovery Mode:** Fetch real HTML fixtures for parser testing:

```python
from autoscout.scraper import Auto24Scraper, BRAND_IDS

async with Auto24Scraper(headless=False) as scraper:
    await scraper.fetch_and_save_fixtures(brand_id=BRAND_IDS["toyota"])
```

This saves `search_results.html` and `listing_{ID}.html` to `tests/fixtures/`.

## Architecture

### Pipeline Overview

```
SCRAPE → INGEST → DIFF → SCREEN → EVALUATE → RANK → NOTIFY
```

1. **SCRAPE:** Playwright fetches auto24.ee search results for configured filters
2. **INGEST:** Parse listing pages, download photos, store in SQLite
3. **DIFF:** Detect new/changed/removed listings vs. database state
4. **SCREEN:** Quick AI pass/fail with Haiku (~$0.005/listing) against hard criteria
5. **EVALUATE:** Full AI analysis with Sonnet + Vision (~$0.048/listing) including photos
6. **RANK:** Weighted composite scoring based on buyer preferences
7. **NOTIFY:** Telegram push notifications + HTML report

### Current Implementation Status

**Implemented:**
- ✅ Web scraping with Playwright + stealth mode (handles Cloudflare, pagination, photo extraction)
- ✅ HTML parsing for search results and listing pages
- ✅ Pydantic models for structured data
- ✅ Comprehensive unit and integration tests

**Planned:**
- ⏳ Database layer (SQLite with schema in `docs/plan.md`)
- ⏳ AI screening stage (Haiku)
- ⏳ AI evaluation stage (Sonnet + Vision)
- ⏳ Ranking algorithm
- ⏳ Telegram notifications
- ⏳ HTML report generation

### Key Modules

- **`scraper.py`**: Playwright-based scraper for auto24.ee. Uses playwright-stealth for bot detection evasion. Handles Cloudflare challenges, pagination, polite delays (5-10s), response body capture (fallback if page crashes).

- **`parser.py`**: BeautifulSoup HTML parsers. Selectors built against real Feb 2026 HTML fixtures. If auto24.ee changes markup, update selectors here.

- **`models.py`**: Pydantic models (`SearchResultItem`, `Listing`). Used for validation and will integrate with Claude structured outputs.

- **Database** (planned): SQLite with tables for listings, snapshots, evaluations, external checks, state history, runs. See schema in `docs/plan.md:238-323`.

- **AI evaluation** (planned): Two-stage pipeline using Claude Haiku for screening and Sonnet for full evaluation with vision.

## Code Conventions

### HTML Parsing Patterns

Parser functions follow these conventions:

1. **Helper functions**: Prefixed with `_` (e.g., `_parse_price`, `_text`)
2. **Parsing extractors**: Named `_extract_*` for pulling data from soup objects
3. **Regex-based parsers**: Used for prices, mileage, years, engine specs (see `parser.py:45-95`)
4. **Main parsers**: `parse_search_results()` and `parse_listing()` are public APIs

When auto24.ee markup changes, update CSS selectors in parser.py. The current selectors target:
- Search results: `div.result-row` structure
- Listing pages: `table.main-data`, `div.vImages`, `div.vTechData`

### Test Fixtures

- Tests use HTML fixtures from `tests/fixtures/` (gitignored, generated by scraper)
- Fixture loading uses `conftest.py::load_fixture()` which auto-skips if fixture missing
- To regenerate fixtures: run scraper discovery mode (see "Running the Scraper" above)

### Async Patterns

The scraper uses async/await throughout:
- Use `async with Auto24Scraper() as scraper:` for proper lifecycle management
- All scraper methods are async: `await scraper.search(...)`, `await scraper.get_listing(...)`

### Polite Scraping

Built-in politeness features:
- Random delays between requests: 5-10s (configurable via `delay_min`, `delay_max`)
- Cloudflare challenge detection and automatic waiting
- User agent spoofing (recent Chrome on Windows)
- Playwright-stealth for evasion of common bot detection techniques
- Respect for robots.txt (manual check required)

## Important Notes

### Brand IDs

Auto24.ee uses numeric brand IDs in search URLs. Known mappings in `scraper.py:26-31`:

```python
BRAND_IDS = {
    "toyota": 13,
    "lexus": 35,
    "honda": 30,
    "mazda": 56,
}
```

### Playwright-Stealth

The scraper uses `playwright-stealth` (v2.0+) to evade bot detection. The stealth configuration is applied to each page after creation:

```python
from playwright_stealth import Stealth

stealth_config = Stealth()
await stealth_config.apply_stealth_async(page)
```

This patches various browser properties (navigator.webdriver, Chrome runtime, etc.) to make Playwright less detectable.

### Buyer Preferences

See `docs/plan.md` for detailed buyer criteria. Key points:

- **Hard requirements**: Petrol only (no hybrids), manual or torque converter auto (no CVT/DCT), specific brands
- **Engine scoring**: Port injection preferred, direct injection penalized -10 to -15 points (except Mazda SkyActiv-G)
- **Scoring weights**: Mechanical reliability 25%, Maintenance cost 25%, Value 20%, Cosmetic 15%, Spec match 10%, Seller trust 5%

### External Documentation

- **`docs/plan.md`**: Complete project plan, requirements, architecture, database schema, config structure, cost estimates
- **`docs/research.md`**: Car knowledge base, platform details, external services (MNT, LKF), engine/transmission data

## Future Development

When implementing new stages:

1. **Database layer**: Use schema from `docs/plan.md:238-323`. Create migrations, add upsert logic for listings.

2. **AI screening**: Implement in `screener.py`. Use Haiku 4.5, structured output, hard criteria only (no photos). Cost target: ~$0.005/listing.

3. **AI evaluation**: Implement in `evaluator.py`. Use Sonnet 4.5 with vision, send all photos (resized to 1568px). Return structured JSON with scores, flags, reasoning. Cost target: ~$0.048/listing.

4. **Ranking**: Implement in `ranker.py`. Apply weights from buyer preferences, factor in price trends and listing freshness.

5. **Notifications**: Implement in `notifier.py`. Use python-telegram-bot for push notifications, generate static HTML report for full ranked list.
