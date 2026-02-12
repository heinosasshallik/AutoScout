# Car Listing Evaluation

You are evaluating a used car listing from auto24.ee for a buyer in Estonia. Read the listing data, research the specific car online, and produce a thorough evaluation.

## Listing Data

Read the file `listing.json` in the current directory. It contains structured data from the listing page.

## Buyer Profile

- **Use case:** A want, not a need. Occasional driving — short city trips and weekend trips out of the city a few times per year, possibly winter commute. Low annual km (<7,000).
- **Top priority:** Lowest total cost of ownership. Simple, reliable, cheap.
- **Size:** Nothing too small — no Yaris-sized cars. Anything Corolla-sized and up is fine.
- **Safety:** Important. Multiple airbags, good Euro NCAP crash test results.
- **Location:** Estonia (cold winters, salt roads, relevant for rust and cold-weather issues).

## Hard Requirements (reject if violated)

- **Fuel:** Petrol only. No hybrids (low annual km makes the hybrid premium not worth it).
- **Transmission:** Manual or torque converter automatic only. Reject belt-type CVT, eCVT, and dual-clutch (DCT).
- **Brands:** Toyota, Lexus, Honda, Mazda (and known rebadges like Pontiac Vibe).

## Research Instructions

Use web search to investigate:

1. **Engine identification:** Determine the exact engine code from the make, model, year, displacement, and power. Is it port injection, direct injection, or dual (D-4S)?
2. **Known issues:** What are the documented problems for this specific engine/model/year? Timing chain vs belt? Oil consumption? Carbon buildup?
3. **Transmission:** What type is fitted to this specific variant? Any known issues?
4. **Model-specific concerns:** Recalls, TSBs, common failure points at this mileage.
5. **Estonian relevance:** Cold-weather issues, rust-prone areas, salt road concerns for this model.
6. **Safety:** Look up Euro NCAP rating for this model/generation. How many airbags? Any safety-related recalls?
7. **Market value:** Is the asking price reasonable for this make/model/year/mileage in Estonia?

## Scoring Rubric

Score each category on a 1-10 integer scale:

| Category | What to assess |
|----------|----------------|
| Mechanical reliability | Engine/transmission track record, known issues, mileage vs expected lifespan |
| Maintenance cost outlook | Expected future costs: parts, fluids, timing belt/chain, any special maintenance needed |
| Value for money | Price vs market for comparable make/model/year/mileage |
| Cosmetic condition | No visible body damage or rust that would be costly to repair. Aesthetics don't matter — just structural/functional cosmetic issues (note: photos not yet available) |
| Safety | Euro NCAP rating, number of airbags, active safety features, any safety recalls |
| Spec match | How well it matches buyer preferences (injection type, transmission, aspiration) |
| Seller trustworthiness | Private vs dealer, description quality, number of photos, red flags |

### Injection type scoring guidance

- Port injection: full score on spec match
- Dual injection (D-4S): full score on spec match
- Direct injection only: -2 to -3 points on spec match. Exception: Mazda SkyActiv-G is acceptable (engineered countermeasures, proven 300k+ miles) but still ranks below port/dual injection.

### Transmission scoring guidance

- Manual: full score
- Torque converter auto (Aisin, Mazda SkyActiv-Drive): full score
- Honda CVT: reject (hard requirement)
- Belt-type CVT: reject (hard requirement)
- DCT: reject (hard requirement)

## Preferred Engine Families (for reference)

- **2ZR-FE/FAE** (Toyota 1.8L port) — bulletproof
- **3ZR-FAE** (Toyota 2.0L port) — Avensis
- **K20/K24** (Honda 2.0-2.4L port) — legendary
- **R18** (Honda 1.8L port) — excellent longevity
- **SkyActiv-G 2.0/2.5** (Mazda, DI but well-engineered)

## Output

You MUST respond with valid JSON matching the required schema. No markdown, no commentary outside the JSON.
