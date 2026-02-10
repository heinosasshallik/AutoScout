# AutoScout — Project Plan

## Brief

A system that monitors auto24.ee for used car listings, evaluates them against
specific buyer criteria using AI, and produces a ranked list of cars worth seeing
in person. Runs 1-2x daily. Tracks what has been seen, evaluated, and acted on.

### User's Original Request

> Soov, mitte vajadus. Sõidan potentsiaalselt harva. Võibolla linnast välja aja
> veetmiseks ainult, võibolla talvel tööle ka. Peamine kriteerium on
> ülalpidamiskulud. Soovin ise lihtsamaid töid teha, seega mida vastupidavam ja
> lihtsasti hooldatav auto, seda parem. Samas välimus võiks meeldida.

Translation: A want, not a need. Drives potentially rarely — weekend trips out of
the city, possibly winter commute. Main criterion is maintenance costs. Wants to do
simpler work themselves, so the more durable and easily maintainable the car, the
better. Appearance should be appealing.

### Goals

1. **Daily monitoring:** Scrape auto24.ee, detect new and changed listings
2. **AI evaluation:** Score each listing against buyer preferences (mechanical
   reliability, cost of ownership, condition, value)
3. **Ranked output:** Produce a prioritized list of cars to go see first
4. **State tracking:** Know what has been looked at, evaluated, rejected, contacted
5. **Automation where reliable:** Auto-fetch photos, auto-check external services
   where APIs are stable. Manual fallback where they aren't (MNT, LKF)

### Future Goals (not in initial scope)

- Seller communication agent (draft Estonian messages, negotiate, track conversations)
- Price prediction from accumulated data
- Multi-source aggregation (autoportaal.ee, mobile.de for EU price comparison)
- Web dashboard for browsing results on phone
- Auto-scheduling viewings

---

## Buyer Preferences

### Context

- **Use case:** Want, not need. Occasional — weekend trips, possibly winter commute
- **Priority:** Lowest total cost of ownership
- **DIY:** Wants to do simpler maintenance/repairs. Durability and ease of service
  matter
- **Aesthetic:** Appearance should be pleasant

### Hard Requirements

| Criterion | Requirement |
|-----------|------------|
| Fuel | Petrol only, no hybrids (low annual km makes hybrid premium not worth it) |
| Transmission | Manual or torque converter auto. Reject belt-type CVT, eCVT (no hybrids), and DCT |
| Brands | Toyota, Lexus, Honda, Mazda (+ rebadges like Pontiac Vibe) |
| Safety | Multiple airbags, good crash test results |

### Injection Type Scoring

| Type | Treatment | Rationale |
|------|-----------|-----------|
| Port injection | Full score | No carbon buildup, simplest, cheapest long-term |
| Dual port + direct (D-4S) | Full score | Port injectors clean valves; best of both worlds |
| Direct injection only | -10 to -15 point penalty | Carbon buildup risk. Mazda SkyActiv-G is acceptable (engineered countermeasures, proven 300k+ miles) but ranks below equivalent port/dual injection cars. Honda 1.5T also acceptable with penalty |

### Soft Preferences

| Criterion | Preference |
|-----------|-----------|
| Aspiration | Naturally aspirated preferred. Turbo acceptable with small penalty |
| Oil changes | 6 months or 8,000 km ideal |
| Seller | Private preferred (no VAT). Dealer OK (some legal guarantees) |

### Preferred Engine Families

- 2ZR-FE (Toyota 1.8L port) — bulletproof
- 2ZR-FAE (Toyota 1.8L port, Valvematic) — same family
- 3ZR-FAE (Toyota 2.0L port) — Avensis
- K20/K24 (Honda 2.0-2.4L port) — legendary
- R18 (Honda 1.8L port) — excellent longevity
- SkyActiv-G 2.0/2.5 (Mazda, DI but well-engineered)

### Scoring Weights

| Category | Weight | What It Measures |
|----------|--------|-----------------|
| Mechanical reliability | 0.25 | Engine/transmission track record, known issues, mileage vs expected life |
| Maintenance cost outlook | 0.25 | Expected future costs: parts, fluids, special maintenance (carbon cleaning, timing belt, etc.) |
| Value for money | 0.20 | Price relative to market for comparable make/model/year/mileage |
| Cosmetic condition | 0.15 | Paint, rust, interior wear, panel gaps (assessed from photos) |
| Spec match | 0.10 | How well the car matches stated preferences (injection type, transmission, aspiration) |
| Seller trustworthiness | 0.05 | Private vs dealer, description quality, number of photos, red flags in listing |

### Priority Watch List

| Priority | Car | Why |
|----------|-----|-----|
| 1 | Toyota Corolla/Auris 1.8 (2007-2018) | 2ZR-FE/FAE port injection, nearly indestructible |
| 2 | Toyota Avensis 1.8-2.0 (2009-2018) | 2ZR-FAE/3ZR-FAE port injection, spacious |
| 3 | Honda Civic 1.8 (8th/9th gen, 2006-2015) | R18 port injection, sportier feel |
| 4 | Honda CR-V 2.0 (2007-2017) | K20 port injection, practical |
| 5 | Mazda3 SkyActiv (2013+) | Best driving dynamics. DI-only penalty applied |
| 6 | Mazda CX-5 SkyActiv (2013+) | Practical SUV. DI-only penalty applied |

Note: Hybrids excluded. At very low annual km (<7,000), the purchase premium and
battery replacement risk (calendar aging, not mileage) do not pay off. See
research.md for full hybrid analysis.

---

## System Architecture

### Pipeline

```
┌─────────┐   ┌────────┐   ┌──────┐   ┌────────┐   ┌──────────┐   ┌──────┐   ┌────────┐
│ SCRAPE  │──▶│ INGEST │──▶│ DIFF │──▶│ SCREEN │──▶│ EVALUATE │──▶│ RANK │──▶│ NOTIFY │
│ search  │   │ pages  │   │ new/ │   │ Haiku  │   │ Sonnet + │   │      │   │Telegram│
│ results │   │ + imgs │   │changed│  │ quick  │   │ photos   │   │      │   │+ HTML  │
└─────────┘   └────────┘   └──────┘   └────────┘   └──────────┘   └──────┘   └────────┘
```

#### Stage 1: SCRAPE
Fetch auto24.ee search result pages for pre-configured filters (brand + fuel +
price range + year range). Extract listing IDs and URLs. Use `httpx` +
`BeautifulSoup` (server-rendered PHP, no JS needed). Fall back to Playwright if
Cloudflare blocks. Polite: 5-10s random delay, respect robots.txt.

#### Stage 2: INGEST
Fetch individual listing pages for new/changed listings. Parse all structured
fields. Download listing photos (resized to max 1568px for Claude Vision). Store
raw HTML for re-parsing if parser improves. Upsert into `listings` table, create
snapshot in `listing_snapshots`.

#### Stage 3: DIFF
Compare current scrape against database. Categorize: new (never seen), changed
(price/description changed), removed (no longer listed), unchanged. Only new and
changed flow to evaluation. Log price changes — drops are interesting signals.

#### Stage 4: SCREEN (Haiku — cheap, fast)
Quick pass/fail against hard criteria:
- Is it actually petrol?
- Is the transmission manual, torque converter auto, or eCVT?
- Basic price sanity
- Known bad model years (e.g., 2011-2012 CT200h, 1999-2002 1ZZ-FE)

Cost: ~$0.005/listing. Rejects obvious mismatches before expensive evaluation.

#### Stage 5: EVALUATE (Sonnet + Vision — full analysis)
Only for listings that passed screening. Sends to Claude Sonnet:
- All structured listing data
- Description text (in Estonian — Claude handles it)
- All photos (rust, damage, interior, paint, panel gaps)
- Buyer preference profile
- Market context (avg prices for similar cars already seen)

Returns structured JSON with scores, flags, engine/transmission analysis, price
assessment, reasoning.

#### Stage 6: RANK
Weighted composite score from evaluation. Factor in:
- Price trends (recent drop = opportunity)
- Listing freshness (newly listed = less picked over)
- Spec match bonuses/penalties

#### Stage 7: NOTIFY
- **Telegram bot:** Push top 3-5 new finds with photo, price, score, key flags
- **HTML report:** Full ranked list with all details, generated as static file

### External Checks

| Service | Automation Level | When |
|---------|-----------------|------|
| auto24.ee scraping | Fully automated | Every run |
| Market price estimation | Fully automated (self-computed from scraped data) | Every evaluation |
| MNT vehicle check | Semi-manual: generate pre-filled links | Shortlisted cars |
| LKF damage check | Semi-manual: generate pre-filled links | Shortlisted cars |
| Google plate search | Could automate via search API | Shortlisted cars |

MNT (reCAPTCHA v3 + JSF) and LKF (Drupal session cookies) are hard to automate
reliably. For MVP, the system generates a checklist with direct links for manual
verification of shortlisted cars. Full automation can be attempted later with
Playwright.

---

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.12+ | Best ecosystem for scraping + AI + data pipelines |
| HTTP client | `httpx` (async) | Modern, async-native, connection pooling |
| HTML parsing | `BeautifulSoup4` | Robust, well-documented, handles malformed HTML |
| Browser fallback | `playwright` | For Cloudflare bypass if plain HTTP is blocked |
| Database | SQLite | Single-user, zero config, portable, JSON functions |
| Data models | `pydantic` | Validation + integrates with Claude structured outputs |
| AI SDK | `anthropic` | Official Claude SDK |
| Image processing | `Pillow` | Resize photos for Vision API |
| Notifications | `python-telegram-bot` or raw HTTP | Push to phone |
| Config | YAML (`pyyaml`) | Human-readable preference file |
| Scheduling | `cron` or `systemd timer` | 1-2x daily execution |

---

## File Structure

```
autoscout/
├── pyproject.toml
├── config.yaml                    # buyer preferences, search filters, API keys
├── docs/
│   ├── plan.md                    # this file — project plan and requirements
│   └── research.md                # car knowledge, platform research, sources
├── src/
│   └── autoscout/
│       ├── __init__.py
│       ├── main.py                # entry point, pipeline orchestration
│       ├── scraper.py             # auto24.ee search result fetching
│       ├── parser.py              # HTML → structured listing data
│       ├── db.py                  # SQLite schema, migrations, queries
│       ├── models.py              # Pydantic models (Listing, Evaluation, etc.)
│       ├── screener.py            # Stage 4: Haiku quick filter
│       ├── evaluator.py           # Stage 5: Sonnet + Vision full evaluation
│       ├── ranker.py              # Stage 6: composite scoring and ranking
│       ├── notifier.py            # Telegram bot + HTML report generation
│       └── external.py            # MNT/LKF link generation, market price calc
├── data/                          # runtime data (gitignored)
│   ├── autoscout.db               # SQLite database
│   └── photos/                    # downloaded listing photos
└── tests/
    └── ...
```

---

## Database Schema

```sql
CREATE TABLE listings (
    id TEXT PRIMARY KEY,              -- auto24 listing ID
    url TEXT NOT NULL,
    title TEXT,
    make TEXT,
    model TEXT,
    year INTEGER,
    mileage_km INTEGER,
    price_eur INTEGER,
    fuel_type TEXT,
    transmission TEXT,                -- manual / torque_converter_auto / ecvt / cvt / dct
    engine_cc INTEGER,
    power_kw INTEGER,
    body_type TEXT,
    drivetrain TEXT,
    color TEXT,
    location TEXT,
    seller_type TEXT,                 -- private / dealer
    seller_name TEXT,
    description_text TEXT,
    photo_urls TEXT,                  -- JSON array
    raw_html TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    listing_status TEXT DEFAULT 'active',  -- active / removed / sold
    eval_state TEXT DEFAULT 'new',         -- new / screened / evaluated / shortlisted / rejected / contacted / visited / purchased
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE listing_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT NOT NULL REFERENCES listings(id),
    price_eur INTEGER,
    snapshot_data TEXT,               -- JSON of all listing fields at this point
    captured_at TEXT NOT NULL
);

CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT NOT NULL REFERENCES listings(id),
    stage TEXT NOT NULL,              -- screen / full
    model_used TEXT,                  -- e.g. haiku-4.5, sonnet-4.5
    prompt_version TEXT,
    overall_score REAL,
    scores_json TEXT,                 -- JSON: {mechanical: 8, value: 7, ...}
    reasoning_text TEXT,
    flags_json TEXT,                  -- JSON: {red_flags: [...], green_flags: [...]}
    photo_analysis_json TEXT,
    price_assessment TEXT,
    estimated_fair_price_eur INTEGER,
    cost_usd REAL,
    evaluated_at TEXT NOT NULL
);

CREATE TABLE external_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT NOT NULL REFERENCES listings(id),
    check_type TEXT NOT NULL,         -- mnt_registry / lkf_damage / market_price / vin_check
    result_json TEXT,
    checked_at TEXT NOT NULL
);

CREATE TABLE state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id TEXT NOT NULL REFERENCES listings(id),
    old_state TEXT,
    new_state TEXT NOT NULL,
    reason TEXT,
    changed_at TEXT NOT NULL
);

CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    listings_scraped INTEGER,
    listings_new INTEGER,
    listings_changed INTEGER,
    listings_screened INTEGER,
    listings_evaluated INTEGER,
    status TEXT                       -- running / completed / failed
);
```

### Listing States

```
new → screened → evaluated → shortlisted ──→ contacted → visited → purchased
                    │                                        │
                    └──→ rejected                            └──→ rejected
```

### Resumability

- **Upsert on listing ID:** Re-running the same scrape produces the same state
- **Per-listing state tracking:** Each stage only processes listings in the
  appropriate `eval_state`. Crash mid-run → restart picks up where it left off
- **HTTP response caching:** Cache raw HTML by URL + date. Never re-fetch on retry
- **Run log:** Each pipeline execution recorded for debugging

---

## AI Evaluation Design

### Two-Stage Pipeline

**Stage 1 — Screen (Haiku 4.5):** Pass/fail against hard requirements. No photos.
Cost: ~$0.005/listing.

**Stage 2 — Evaluate (Sonnet 4.5 + Vision):** Full analysis with photos. Cost:
~$0.048/listing.

### Prompt Architecture

1. **System prompt (cached across all evaluations):**
   - Role: expert used car evaluator for Estonian market
   - Full scoring rubric with integer 1-10 scales and criteria definitions
   - Output JSON schema
   - 3-5 example evaluations (multishot) covering different scenarios

2. **Per-listing user message:**
   - Structured listing data in XML tags
   - Photos as image content blocks
   - Buyer preference summary
   - Market context (avg prices for similar cars seen so far)

3. **Structured output:**

```json
{
  "overall_score": 78,
  "scores": {
    "value_for_money": 8,
    "mechanical_reliability": 9,
    "maintenance_cost_outlook": 8,
    "cosmetic_condition": 6,
    "spec_match": 9,
    "seller_trust": 7
  },
  "engine_analysis": {
    "engine_code": "2ZR-FXE",
    "injection_type": "port",
    "known_issues": [],
    "carbon_buildup_risk": "none"
  },
  "transmission_analysis": {
    "type": "ecvt",
    "known_issues": [],
    "reliability": "excellent"
  },
  "red_flags": [],
  "green_flags": ["full service history", "single owner"],
  "price_assessment": "below_market",
  "estimated_fair_price_eur": 9500,
  "reasoning": "..."
}
```

---

## Config File Structure

```yaml
# config.yaml

search:
  brands:
    - {name: toyota, auto24_id: 76}
    - {name: lexus, auto24_id: 35}
    - {name: honda, auto24_id: TBD}
    - {name: mazda, auto24_id: TBD}
  fuel: petrol              # no hybrids — low annual km makes premium not worth it
  max_price_eur: 15000
  min_year: 2007
  max_mileage_km: 250000

preferences:
  injection:
    full_score: [port, dual_port_di]
    penalized: [direct]        # -10 to -15 points
  transmission:
    accepted: [manual, torque_converter_auto]
    rejected: [cvt, ecvt, dct]   # ecvt = hybrid only, excluded
  aspiration:
    preferred: naturally_aspirated
    accepted_with_penalty: turbo
  weights:
    mechanical_reliability: 0.25
    maintenance_cost: 0.25
    value_for_money: 0.20
    cosmetic_condition: 0.15
    spec_match: 0.10
    seller_trust: 0.05

api:
  anthropic_key: ${ANTHROPIC_API_KEY}
  screening_model: claude-haiku-4-5-20251001
  evaluation_model: claude-sonnet-4-5-20250929

notifications:
  telegram:
    bot_token: ${TELEGRAM_BOT_TOKEN}
    chat_id: ${TELEGRAM_CHAT_ID}
    top_n: 5                   # how many top cars to push

scraping:
  delay_min_s: 5
  delay_max_s: 10
  max_retries: 3
  cache_dir: data/cache
  photos_dir: data/photos
  photo_max_px: 1568           # max dimension for Claude Vision

database:
  path: data/autoscout.db
```

---

## Cost Estimates

### Claude API

| Model | Input/MTok | Output/MTok | Use |
|-------|-----------|------------|-----|
| Haiku 4.5 | $1 | $5 | Screening |
| Sonnet 4.5 | $3 | $15 | Full evaluation |

**Per-listing Sonnet evaluation (with 10 photos):**

| Component | Tokens | Cost |
|-----------|--------|------|
| System prompt (cached) | ~2,000 | ~$0.0006 |
| Listing text | ~1,500 | ~$0.0045 |
| 10 photos (~1,200 each) | ~12,000 | ~$0.036 |
| Structured output | ~500 | ~$0.0075 |
| **Total** | | **~$0.048** |

**Daily cost (100 listings scraped, ~30 pass screening):**

| Stage | Cost |
|-------|------|
| Haiku screening (100) | ~$0.50 |
| Sonnet evaluation (30) | ~$1.44 |
| **Daily total** | **~$1.94** |
| With Batch API (50% off) | **~$0.97** |

### Pre-Purchase (per shortlisted car)

| Service | Cost |
|---------|------|
| MNT background check | Free |
| LKF damage check | Free |
| autoDNA VIN report | ~1-10 EUR |
| Professional inspection | ~50-150 EUR |

---

## References

- Detailed research on auto24.ee platform, external services, car knowledge base,
  engine/transmission data, and market context: see [research.md](research.md)
