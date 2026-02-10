# AutoScout Research

Comprehensive research for building an auto24.ee car finder system tailored to a
reliability-focused buyer in Estonia.

---

Reference material for the AutoScout project. For the project plan, buyer
preferences, architecture, and cost estimates, see [plan.md](plan.md).

## Table of Contents

1. [auto24.ee Platform](#1-auto24ee-platform)
2. [External Services](#2-external-services)
3. [Car Knowledge Base](#3-car-knowledge-base)

---

## 1. auto24.ee Platform

### Overview

Estonia's largest vehicle classifieds database. Owned by Baltic Classifieds Group.
~14 million page views and ~400,000 unique users per week. Supports Estonian,
Russian, and English (`eng.auto24.ee`).

### No Public API

There is no publicly documented API. A dealer/partner API exists (e.g.
`/api/autosky`) but is undocumented and limited to dealer inventory. The mobile app
is a WebView wrapper, not a native app with a separate API. An RSS feed exists at
`/export/xml/news.rss` but only for news content, not listings.

### URL Structure

**Search results:**
```
https://www.auto24.ee/kasutatud/nimekiri.php?{parameters}
https://eng.auto24.ee/kasutatud/nimekiri.php?{parameters}
```

**Individual listings:**
```
https://www.auto24.ee/used/{numeric_id}
```

**Legacy format (may still work):**
```
https://www.auto24.ee/kasutatud/auto.php?id={numeric_id}
```

### Search Parameters

| Parameter | Meaning | Example Values |
|-----------|---------|----------------|
| `a` | Vehicle category | `100` (passenger+SUV), `101` (passenger), `102` (SUV) |
| `b` | Make/brand ID | `76` (Toyota), `35` (Lexus), `25` (Kia) |
| `bw` | Model ID | Numeric |
| `bn` | Listing type | `2` |
| `ae` | Sort/region | `1`, `2`, `8` |
| `af` | Results per page | `50`, `200` |
| `ak` | Pagination offset | `0`, `50`, `100` |
| `g1` | Max price (EUR) | `10000` |
| `l2` | Max mileage (km) | `100000` |
| `w1` | Min engine displacement (cc) | `500` |
| `h[0]` | Fuel type (array) | `1` |
| `i[0]` | Transmission type (array) | `2` |
| `j[0]` | Body type (array) | `28` |
| `by` | Sort option | `1` |
| `otsi` | Search trigger | `otsi` |

Brand IDs of interest: Toyota=`76`, Lexus=`35`, Honda=TBD, Mazda=TBD. Exact IDs
need to be confirmed by inspecting the search form.

### Listing Data Fields

A typical listing contains:

- **Identification:** Make, Model, Year
- **Pricing:** Price (EUR), VAT indication, monthly payment estimate
- **Technical:** Power (kW), Engine displacement, Fuel type, Transmission,
  Drivetrain, Body type
- **Usage:** Mileage (km)
- **Media:** Up to 15 photos (private), 30 (dealer)
- **Seller:** Contact info (phone, name), Location, Seller type (private/dealer)
- **Text:** Free-text description
- **Missing:** Publication date is NOT displayed (long-standing user complaint)

### Scraping Feasibility

| Aspect | Detail |
|--------|--------|
| Backend | PHP (server-side rendered, NOT a JavaScript SPA) |
| Anti-bot | Cloudflare WAF (returns 403 on non-browser user agents) |
| JS required? | Listing data is in initial HTML. No JS rendering needed for core data |
| Existing scraper | [kevinkliimask/auto24-scraper](https://github.com/kevinkliimask/auto24-scraper) uses Selenium + ChromeDriver |
| Recommended approach | `httpx` + `BeautifulSoup` first, fall back to Playwright if Cloudflare blocks |

### Scraping Politeness

- Check and respect `robots.txt`
- 5-10 second random delay between requests
- Exponential backoff on errors (429, 503)
- Cache responses — never re-fetch in the same run
- For 50-200 listings/day this means requests spread over 10-30 minutes

---

## 2. External Services

### MNT Vehicle Background Check (Transpordiamet)

**URL:** `https://eteenindus.mnt.ee/public/soidukTaustakontroll.jsf`

**Input:** Registration plate (basic) or plate + VIN (full history).

**Returns:**
- Vehicle registration and technical details
- Technical inspection history with mileage at each inspection (critical for
  odometer fraud detection)
- Transaction/ownership history
- Active insurance status
- Restrictions or liens

**Technical:** Java Server Faces + PrimeFaces, protected by reCAPTCHA v3. No public
API. Full automation requires browser + reCAPTCHA solving. Authentication (ID-card,
Mobile-ID, Smart-ID) required for extended data.

**Automation difficulty:** High. Best approach for MVP: generate direct links with
pre-filled plate numbers for manual checking of shortlisted cars.

### LKF Insurance Damage Check

**URL:** `https://www.lkf.ee/et/kahjukontroll`

**Input:** Registration plate or VIN.

**Returns:**
- Whether vehicle was involved in MTPL (third-party liability) insurance events
- Whether vehicle was involved in casco (comprehensive) insurance events
- Damage amounts
- "Vehicle destroyed" flag for total-loss vehicles

**Limitations:** Only shows incidents processed by insurers. Does not show:
unreported incidents, cash settlements, single-vehicle accidents without casco,
incidents before Estonian registration.

**Technical:** Drupal CMS, AJAX POST to `/et/kahjukontroll?ajax_form=1`, session
cookies designed to block automation.

**Automation difficulty:** Medium-high. Feasible with Playwright session management
but fragile. Same approach as MNT for MVP: generate pre-filled links.

### auto24.ee Market Price Query (Turuhinna Paring)

**URL:** `https://www.auto24.ee/ostuabi/?t=soiduki-turuhinna-paring`

Calculates average price of comparable vehicles from auto24.ee data. Provides
price range, graphs showing price changes over up to 7 years, distribution by
price group. Historical data back to 2009. May be a paid service.

**Better approach for our system:** Self-compute market prices from our own scraped
data. After accumulating listings, compute percentiles for make/model/year/mileage
to detect over- and under-priced listings.

### Other Useful Services

| Service | URL | Purpose |
|---------|-----|---------|
| auto24 VIN query | `eng.auto24.ee/vin/index.php` | VIN-based vehicle data |
| autoDNA | `autodna.com` | Third-party VIN history (paid, ~1-10 EUR/report) |
| checkcar.vin | `checkcar.vin` | VIN history covering Estonia |
| Google plate search | Google `"{plate_number}"` | Find previous sale listings |
| auto24 purchase assistance | `auto24.ee/ostuabi/` | Professional inspection 89 EUR |

### Odometer Fraud in Estonia

A significant concern: 5.9-13.6% of cars checked in Estonia have tampered
readings. 35-40% of imported used cars across Eastern EU may have tampered
odometers. Diesel cars disproportionately affected. Always cross-reference current
odometer with MNT inspection records.

---

## 3. Car Knowledge Base

### Target Brands

| Brand | Sold in Europe? | Notes |
|-------|----------------|-------|
| Toyota | Yes | #1 selling brand in Estonia |
| Lexus | Yes | Toyota's luxury division. Shares Toyota platforms/engines |
| Honda | Yes (limited lineup) | Scaled back in Europe. Civic, CR-V, Jazz, HR-V, ZR-V |
| Mazda | Yes | Full European lineup: Mazda2/3, CX-3/30/5/60 |
| Scion | **No** | North America only (2003-2016). Rebadged Toyotas. If found in Estonia, it's a US import |
| Acura | **No** | North America only. Honda's luxury division. Equivalent models sold as Honda in Europe |

### Toyota Engines (European Market)

#### Port Injection Only (no carbon buildup concern)

| Engine | Displacement | Models | Notes |
|--------|-------------|--------|-------|
| 1KR-FE | 1.0L I3 | Yaris, Aygo | Basic, economical |
| 1NR-FE | 1.3L I4 | Yaris, Corolla Verso | Since 2008 |
| 2ZR-FE | 1.8L I4 | Corolla, Auris | Bulletproof |
| 2ZR-FAE | 1.8L I4 | Corolla, Auris (Valvematic) | Port + Dual VVT-i |
| 2ZR-FXE | 1.8L I4 | Prius, Corolla/Auris Hybrid, Lexus CT200h | Atkinson cycle hybrid. Port injection |
| 3ZR-FAE | 2.0L I4 | Avensis | Port + Valvematic |
| 2AR-FE | 2.5L I4 | Camry, RAV4 (pre-2018) | Multi-port, proven |
| 1NZ-FXE | 1.5L I4 | Prius (Gen 2) | Hybrid, port injection |
| M15A-FXE | 1.5L I3 | Yaris Hybrid, Yaris Cross Hybrid (2020+) | New-gen hybrid, port injection |

#### Dual Injection (Port + Direct, D-4S — best of both worlds)

| Engine | Displacement | Models | Notes |
|--------|-------------|--------|-------|
| M20A-FKS | 2.0L I4 | Corolla (E210), RAV4 (XA50) | Dynamic Force, 2018+ |
| M20A-FXS | 2.0L I4 hybrid | Corolla Hybrid 2.0, C-HR Hybrid | Miller cycle hybrid |
| A25A-FKS | 2.5L I4 | Camry, RAV4 (2018+) | 40% thermal efficiency |
| A25A-FXS | 2.5L I4 hybrid | RAV4 Hybrid, Camry Hybrid | D-4S hybrid |

#### Direct Injection Only (carbon buildup concern)

| Engine | Displacement | Models | Notes |
|--------|-------------|--------|-------|
| M15A-FKS | 1.5L I3 | Yaris (non-hybrid) | DI only, 13:1 compression |
| 3GR-FSE | 3.0L V6 | Lexus GS300 (2005-2011) | Known carbon issues |

### Toyota Transmissions

| Type | Models | Reliability |
|------|--------|-------------|
| 6-speed manual | Yaris, Corolla, Auris, Avensis | Highest reliability, simplest |
| eCVT (Hybrid Synergy Drive) | All hybrids: Prius, Yaris Hybrid, Corolla Hybrid, etc. | Extremely reliable. No belts, clutches, or torque converter. Planetary gear set only. 20+ years proven. Arguably the most reliable auto transmission ever made |
| Torque converter auto (Aisin 6/8-speed) | Older Camry, RAV4, larger models | Very reliable, proven |
| Belt-type CVT (K-series) | Yaris auto, Corolla 2.0 auto, RAV4 2.0 auto | Better than Nissan CVTs but less proven than eCVT |

### Honda Engines (European Market)

#### Port Injection (proven reliability)

| Engine | Displacement | Models | Notes |
|--------|-------------|--------|-------|
| L13A | 1.3L I4 | Jazz (Fit) | MPI, economical |
| L15A | 1.5L I4 (NA) | Jazz, City | MPI, VTEC |
| R18A2/R18Z4 | 1.8L I4 | Civic (8th & 9th gen) | Port injection, i-VTEC, excellent longevity |
| K20A/K24A | 2.0-2.4L I4 | Accord, Civic Type R (older), CR-V | Legendary K-series. Over-engineered, cast-iron sleeves, routinely exceeds 300k+ km |

#### Direct Injection Only

| Engine | Displacement | Models | Notes |
|--------|-------------|--------|-------|
| L15B (turbo) | 1.5L I4 | Civic (2016+), CR-V (2017+) | DI only. Honda claims minimal carbon via engineering countermeasures |

Honda does **not** use dual injection (port + direct). They go fully port or fully
direct.

### Honda Transmissions

| Type | Models | Notes |
|------|--------|-------|
| 6-speed manual | Most models | Gold standard |
| CVT | Civic (2016+), CR-V, Accord | Among the best CVTs. 200k+ km common. But expensive to replace (4,500-9,000 EUR) |
| 5-speed torque converter auto | Older Civic, CR-V | Very reliable, proven |

### Lexus (Toyota Equivalents)

| Lexus | Toyota Equivalent | Shared Engine | Notes |
|-------|-------------------|---------------|-------|
| CT200h | Prius (Gen 3 drivetrain) | 2ZR-FXE hybrid | Port injection, eCVT. Avoid 2011-2012 (battery/airbag issues), 2013+ excellent |
| LBX | Yaris Cross | M15A hybrid | Same TNGA-B platform |
| NX250 | RAV4 | Same 2.5L | Most direct platform sharing |
| NX350h | RAV4 Hybrid | A25A-FXS | D-4S dual injection |
| ES | Camry | Same platform & engines | Most "rebadged" current Lexus |
| IS200 (1998-2005) | Altezza (Japan) | 1G-FE 2.0L I6 | Port injection, understressed |
| IS300 (1st gen) | Altezza RS300 | 2JZ-GE 3.0L I6 | Legendary |
| RX350 | Highlander platform | 2GR-FE 3.5L V6 | Excellent engine |
| LX | Land Cruiser | Same platform | Luxury Land Cruiser |

### Mazda Engines (SkyActiv-G — All Direct Injection)

All SkyActiv-G petrol engines use direct injection only. Mazda does not offer port
injection or dual injection on any petrol model. However, Mazda engineered specific
countermeasures that make their DI engines significantly better than competitors
for carbon buildup.

#### Mazda's Carbon Buildup Countermeasures

1. **Hot intake valves by design:** Coolant passages deliberately routed away from
   intake valves to keep them above ~200C. Carbon deposits form below this
   threshold, so keeping valves hot prevents accumulation.
2. **13:1 compression ratio:** Higher combustion temperatures help burn off deposits.
3. **4-2-1 exhaust headers:** Reduce heat soak into the cylinder head.
4. **Advanced PCV oil separator:** Large separator under intake manifold filters oil
   mist before it reaches intake valves.
5. **Warm-up calibration updates:** Post-2013 models received software updates
   specifically targeting carbon buildup.

#### Real-World Carbon Buildup Evidence

- Teardown at 130,000 km: some deposits found, but after cleaning there was **no
  change in power or fuel economy**. Owner concluded the engine handles carbon
  without negative effects.
- Multiple owners report 200k+ miles with zero carbon cleaning and no issues.
- One 2012 Mazda3 reached 338,810 miles with only routine maintenance.
- Dealership shuttle CX-5 reached 280,000 km on routine maintenance alone.

**Comparison to other DI engines (worst to best):**
1. VW/Audi EA888 TSI — worst, walnut blasting often needed by 100k km
2. BMW N54/N55 — very bad
3. Hyundai/Kia Theta-II — notable issues
4. Ford EcoBoost — problematic at high mileage
5. **Mazda SkyActiv-G — significantly better than all above**
6. Toyota D-4S (dual injection) — non-issue (port injectors clean the valves)

Carbon buildup on SkyActiv-G is "closer to 240k-320k km before it causes concerns"
vs 60k-130k km on VW/BMW engines.

#### SkyActiv-G Models

| Engine | Displacement | Models | Notes |
|--------|-------------|--------|-------|
| SkyActiv-G 1.5 | 1.5L I4 | Mazda2, CX-3 | Some oil consumption reports |
| SkyActiv-G 2.0 | 2.0L I4 | Mazda3, CX-30, CX-5 | Rare camshaft wear, cold-start knocking (normal) |
| SkyActiv-G 2.5 | 2.5L I4 | Mazda3, Mazda6, CX-5 | MAF sensor failures around 100k km (contamination) |

#### Mazda-Specific Concerns for Estonia

1. **Fuel dilution in cold weather:** Short trips in sub-zero temps cause unburned
   fuel to dilute engine oil (up to 11% fuel contamination measured). Burns off on
   highway driving. Mitigation: one 25+ minute highway drive per week, synthetic
   oil, shorter oil change intervals in winter.
2. **Exhaust water freezing:** Water from combustion can freeze in the exhaust
   silencer during cold starts, causing misfire codes. Covered by TSB 01-007/19.
3. **Rust:** European/Canadian owners flag rust on rear sills and front-lower rear
   wheel arch. Cavity wax treatment strongly recommended for Estonian salt roads.
4. **Engine runs cool:** On cold highway driving, oil may not exceed 60C.
   Block heater recommended for Estonian winters.

#### Mazda Transmission

SkyActiv-Drive: 6-speed torque converter automatic with torque converter clutch
locked above ~8 km/h. Gives CVT-like efficiency with traditional auto durability.
Generally excellent reliability — forum consensus is no known systematic failures.

**Critical:** Mazda markets this as "sealed for life" fluid. This is misleading.
Periodic fluid changes are strongly recommended (every 60-80k km).

### Mazda vs Toyota: Reliability Comparison

| Source (Year) | Mazda | Toyota |
|---------------|-------|--------|
| J.D. Power 2025 VDS | 2nd (161 PP100) | 3rd (162 PP100) |
| Consumer Reports 2025 | 6th | 3rd |
| Consumer Reports 2020 | 1st | 2nd |
| Consumer Reports used/long-term | 3rd | 2nd |
| What Car? UK 2025 | Not top 10 | 4th |
| RepairPal | 4.0/5.0 | Higher model-specific |
| iSeeCars 2025 | 7.9/10 | 7.8/10 |

**Summary:** Both top-tier. Mazda and Toyota trade places depending on the survey
and year. The gap is small for established models (Mazda3, CX-5). Mazda's newer
large SUVs (CX-70, CX-90) dragged down recent scores but are irrelevant to us.

### Mazda vs Toyota: Cost of Ownership

| Metric | Mazda3 | Toyota Corolla |
|--------|--------|----------------|
| Annual repair cost (RepairPal) | $433 | $362 |
| 10-year maintenance | ~$4,330 | ~$4,008 |
| RepairPal reliability rank | 9th of 36 compacts | 1st of 36 compacts |
| Potential carbon cleaning cost | 0-600 EUR (once, if ever) | $0 (port injection) |

**10-year total gap: ~$700-$1,300 ($70-$130/year).** Modest.

### Mazda Verdict for This Project

**Include Mazda, but apply a scoring penalty for DI-only injection.** Rationale:
- Reliability is genuinely close to Toyota (A vs A+)
- SkyActiv-G carbon buildup is a managed non-issue for most owners
- The annual cost difference is ~$70 — negligible
- Better driving dynamics and interior quality than equivalent Toyotas
- The cold-weather fuel dilution concern is real but mitigatable

### Walnut Blasting (if ever needed)

| Detail | Value |
|--------|-------|
| Cost in Europe | 350-700 EUR (independent), 600-1000 EUR (dealer) |
| When needed on SkyActiv-G | Most owners: never. Worst case: 150k-200k+ km |
| DIY feasible? | Yes, moderate difficulty, 4-6 hours. Needs media blaster + compressor |

### Rebadged Vehicles Worth Knowing

| Badge | What It Really Is |
|-------|-------------------|
| Pontiac Vibe (2003-2010) | Toyota Matrix/Corolla. 1ZZ-FE or 2ZZ-GE engine. US import only |
| Toyota Aygo | = Peugeot 108 = Citroen C1 (built at same Czech factory) |
| Toyota GT86 / GR86 | = Subaru BRZ (Subaru boxer engine) |
| Toyota Supra (A90+) | BMW Z4 platform, BMW B58 engine |
| Toyota ProAce | = Peugeot Expert = Citroen Dispatch |
| Geo/Chevrolet Prizm | Toyota Corolla (NUMMI plant). US import only |

### Most Bulletproof Engines (ranked by proven reliability)

**Toyota:**
- 2ZR-FE/FXE (1.8L, port) — routinely exceeds 300k+ km
- 2GR-FE (3.5L V6, port) — one of Toyota's best
- 2JZ-GE (3.0L I6) — legendary, found in older Lexus IS300/GS300
- 1NZ-FXE (1.5L hybrid) — Prius workhorse
- A25A-FKS (2.5L, D-4S) — very good, more complex

**Honda:**
- K20A/K24A (2.0-2.4L, port) — universally considered Honda's most reliable.
  Over-engineered, cast-iron sleeves
- R18 (1.8L, port) — 8th/9th gen Civic, excellent longevity
- L13A/L15A (1.3-1.5L NA, port) — Jazz/Fit, simple and reliable

**Mazda:**
- SkyActiv-G 2.0 (DI) — proven to 300k+ miles, no systematic failures
- SkyActiv-G 2.5 (DI) — same block, watch MAF sensor at 100k km

### Transmission Reliability Ranking (best to worst)

1. **Manual** — simplest, cheapest. Clutch replacement at 150-250k km (300-800 EUR)
2. **Toyota eCVT** — simplest automatic ever. No belts, clutches, torque converter.
   Just planetary gears. Zero wear parts besides bearings and fluid. 20+ year track
   record. Failures are exceptionally rare
3. **Torque converter automatic** (Toyota Aisin, Honda 5-speed, Mazda SkyActiv-Drive)
   — complex but proven over decades. Robust with regular fluid changes (60-80k km)
4. **Honda CVT** — among the best belt-type CVTs. 200k+ km common. But 4,500-9,000
   EUR replacement when they fail
5. **Toyota belt-type CVT (K-series)** — better than Nissan/Subaru, less proven than
   eCVT
6. **Nissan/Subaru CVTs** — worst reputation. Avoid

### Ideal Cars to Watch For

| Priority | Car | Why |
|----------|-----|-----|
| 1 | Toyota Corolla/Auris Hybrid (2013-2018) | 2ZR-FXE port injection + eCVT. Cheapest to run |
| 2 | Toyota Prius Gen 3/4 (2010-2018) | Same drivetrain, often cheaper |
| 3 | Lexus CT200h (2013+) | Prius drivetrain, premium feel. Avoid 2011-2012 |
| 4 | Toyota Yaris Hybrid (2015+) | Smallest/cheapest hybrid option |
| 5 | Toyota Corolla/Auris 1.8 manual | 2ZR-FE port injection, nearly indestructible |
| 6 | Honda Civic 1.8 manual (8th/9th gen) | R18 port injection, sportier feel |
| 7 | Mazda3/CX-5 SkyActiv (2013+) | Best driving dynamics. DI-only (scoring penalty) |

### Approximate Estonian Market Prices

| Model | Years | Price Range (EUR) |
|-------|-------|-------------------|
| Toyota Corolla/Auris Hybrid | 2013-2018 | 7,000-13,000 |
| Toyota Prius Gen 3/4 | 2010-2018 | 5,000-12,000 |
| Lexus CT200h | 2013-2017 | 8,000-14,000 |
| Toyota Yaris Hybrid | 2015-2020 | 6,000-12,000 |
| Toyota Corolla/Auris 1.8 | 2007-2013 | 3,000-6,000 |
| Toyota Avensis 1.8-2.0 | 2009-2015 | 4,000-8,000 |
| Honda Civic 1.8 | 2007-2015 | 3,000-7,000 |
| Mazda3/CX-5 SkyActiv | 2013-2018 | 6,000-14,000 |
| Toyota Corolla (E210) | 2019-2022 | 15,000-22,000 |
| Toyota RAV4 Hybrid | 2016-2020 | 15,000-25,000 |

Prices fluctuate with condition, mileage, and trim. For accurate current prices,
the system will self-compute from scraped data.

### Estonian Car Market Notes

- Toyota is #1 selling brand in Estonia for 5+ consecutive years
- Most used cars are imported from Germany, Sweden, or Finland
- Financing APR on auto24 is ~15% — buying cash is much better
- Private sellers: no VAT, generally lower prices, but no legal guarantees
- Dealers: VAT included, some consumer protection guarantees required by law

---

## Sources

### auto24.ee and Estonian Services
- [auto24.ee](https://eng.auto24.ee/)
- [Estonian Transport Administration e-service](https://eteenindus.mnt.ee/main.jsf?lang=en)
- [LKF damage check](https://www.lkf.ee/en/queries)
- [kevinkliimask/auto24-scraper](https://github.com/kevinkliimask/auto24-scraper)
- [Estonian car buying cheat sheet (CarExamer)](https://carexamer.com/blog/estonia-car-buying-cheat-sheet-what-you-need-to-know/)
- [Baltic States used car quality (CarExamer)](https://carexamer.com/blog/baltic-states-used-car-market-quality-struggles-the-facts/)

### Reliability and Cost Data
- [Consumer Reports reliability rankings](https://www.consumerreports.org/cars/car-reliability-owner-satisfaction/who-makes-the-most-reliable-cars-a7824554938/)
- [J.D. Power 2025 VDS](https://www.jdpower.com/business/press-releases/2025-us-vehicle-dependability-study-vds)
- [RepairPal Mazda3 vs Corolla](https://repairpal.com/cars/compare/mazda-3-vs-toyota-corolla)
- [CarEdge lowest cost of ownership 2025](https://caredge.com/guides/lowest-cost-of-ownership-cars-2025)

### Engine and Transmission Technical
- [Toyota engine codes (Continental Motors)](https://continentalmotors.pro/toyota-engine-codes/)
- [Toyota D-4S system (Import Car)](https://www.import-car.com/toyota-direct-injection-port-injection-why-not-both/)
- [Toyota Dynamic Force engine (Wikipedia)](https://en.wikipedia.org/wiki/Toyota_Dynamic_Force_engine)
- [Toyota ZR engine (Wikipedia)](https://en.wikipedia.org/wiki/Toyota_ZR_engine)
- [Hybrid Synergy Drive (Wikipedia)](https://en.wikipedia.org/wiki/Hybrid_Synergy_Drive)
- [Honda K-series reliability (TopSpeed)](https://www.topspeed.com/honda-most-reliable-engine-family/)
- [Mazda SkyActiv (Wikipedia)](https://en.wikipedia.org/wiki/Skyactiv)
- [Mazda SkyActiv service tips (Import Car)](https://www.import-car.com/mazda-skyactiv-service-tips/)

### Carbon Buildup Research
- [Mazda3Revolution carbon investigation](https://www.mazda3revolution.com/threads/intake-valve-carbon-investigation.235229/)
- [BobIsTheOilGuy SkyActiv valve deposits](https://bobistheoilguy.com/forums/threads/skyactiv-intake-valve-deposits-photos.328668/)
- [Intake Cleaning Australia worst cars for carbon](https://intakecleaning.com.au/the-worst-modern-cars-for-carbon-build-up/)
- [CorkSport valve cleaning guide](https://corksport.com/blog/how-to-clean-your-intake-valves/)

### Mazda Long-Term Ownership
- [BobIsTheOilGuy SkyActiv bulletproof](https://bobistheoilguy.com/forums/threads/skyactiv-engines-have-proven-to-be-bulletproof.312595/)
- [Mazda3Revolution 203K miles](https://www.mazda3revolution.com/threads/203k-miles-on-a-2012-mazda3-2-0l-skyactiv-now-what.247686/)
- [Mazda3Revolution longevity reassurance](https://www.mazda3revolution.com/threads/the-quest-for-skyactiv-longevity-reassurance.242067/)

### Technical Architecture
- [ScrapingBee best Python scraping libraries 2025](https://www.scrapingbee.com/blog/best-python-web-scraping-libraries/)
- [Crawlee for Python](https://crawlee.dev/python/)
- [Claude API documentation](https://platform.claude.com/docs/en/)
- [Claude Vision API](https://platform.claude.com/docs/en/build-with-claude/vision)
- [Claude structured outputs](https://platform.claude.com/docs/en/build-with-claude/batch-processing)
- [Simon Willison sqlite-history](https://simonwillison.net/2023/Apr/15/sqlite-history/)
