# Model Comparison: Aggregate Report

Comparison of Opus, Sonnet, and Haiku across 6 car listing evaluations.

## Summary Table

| Listing | Car | Opus | Sonnet | Haiku |
|---------|-----|------|--------|-------|
| 3872109 | 2018 Avensis 1.8 CVT, 84k km, €14,225 | 6.20 SKIP | 6.05 SKIP | 7.65 SKIP |
| 4272435 | 2016 Corolla 1.6 CVT, 123k km, €11,499 | 5.80 SKIP | 4.70 SKIP | 6.45 SKIP |
| 4280612 | 2007 Corolla 1.6 auto, 220k km, €3,250 | 6.10 MAYBE | 5.40 MAYBE | 6.50 MAYBE |
| 4280818 | 2017 Avensis 1.8 manual, 151k km, €13,300 | 5.70 MAYBE | **7.80** MAYBE | 6.35 MAYBE |
| 4281217 | 2012 Corolla 1.6 manual, 170k km, €3,800 | 6.70 GO SEE | 6.45 MAYBE | 7.65 MAYBE |
| 4281378 | 2009 Avensis 1.8 manual, 270k km, €2,300 | 6.15 MAYBE | 6.05 MAYBE | 7.10 MAYBE |

## Engine Identification Accuracy

The most critical task: given displacement + power output, identify the correct engine code.

| Listing | Correct Engine | Opus | Sonnet | Haiku |
|---------|---------------|------|--------|-------|
| 3872109 (1798cc, 108kW) | 2ZR-FAE | **correct** | **correct** | **correct** |
| 4272435 (1598cc, 97kW) | 1ZR-FAE | **correct** | **correct** | **correct** |
| 4280612 (1598cc, 91kW) | 1ZR-FE | **correct** | **correct** | 3ZZ-FE |
| 4280818 (1798cc, 108kW) | 2ZR-FAE | **correct** | 2ZR-FE | **correct** |
| 4281217 (1598cc, 97kW) | 1ZR-FAE | **correct** | **correct** | 2ZR-FE |
| 4281378 (1794cc, 95kW) | **1ZZ-FE** | 2ZR-FE | 2ZR-FAE | 2ZR-FAE |

| Model | Correct | Wrong | Accuracy |
|-------|---------|-------|----------|
| **Opus** | 5 | 1 | **83%** |
| **Sonnet** | 4 | 2 | 67% |
| **Haiku** | 3 | 3 | 50% |

**Correction (4281378):** The original report listed the correct engine as 2ZR-FE and credited
Opus with a correct identification. This was wrong. The listing shows **1794cc** and **95kW**.
The 2ZR-FE displaces **1798cc** (bore 80.5 × stroke 88.3), not 1794cc. The engine with
exactly 1794cc (bore 79.0 × stroke 91.5) and 95kW is the **1ZZ-FE** — a completely different,
older engine family (ZZ series, not ZR series). The 1ZZ-FE was used in the Avensis T250
(2nd generation, 2003-2008). A "2009 Avensis" with 1794cc/95kW is a late-production T250,
not a T270. All three models got this wrong — Opus called it 2ZR-FE, Sonnet and Haiku called
it 2ZR-FAE. None identified the correct engine family.

### How engine errors affected evaluations

Each engine misidentification caused downstream scoring errors:

- **All models on 4281378**: All three identified the engine as a 2ZR variant (ZR family)
  when it's actually a 1ZZ-FE (ZZ family). The 1ZZ-FE has significantly worse oil consumption
  issues (Toyota issued warranty extensions for undersized piston rings) than any 2ZR variant.
  All three also assumed the car is a T270 (3rd gen Avensis) when it's a T250 (2nd gen),
  meaning they referenced wrong safety ratings, wrong known issues, and wrong chassis
  characteristics. Sonnet and Haiku additionally flagged Valvematic risks (2ZR-FAE) that
  don't exist on this engine.

- **Sonnet on 4280818**: Called it 2ZR-FE instead of 2ZR-FAE. Missed the Valvematic system
  entirely, called the engine "bulletproof," and gave reliability 8/10 and maintenance 8/10.
  Produced the highest weighted score in the entire comparison (7.80) for a car that Opus
  rated 5.70. **This is the most consequential engine error** — it would lead to prioritizing
  a risky, overpriced car.

- **Haiku on 4281217**: Called it 2ZR-FE (1.8L) instead of 1ZR-FAE (1.6L). Inflated scores
  because the 2ZR-FE is simpler and more reliable. Weighted score 7.65 vs Opus's 6.70.

- **Haiku on 4280612**: Called it 3ZZ-FE (E120 generation) instead of 1ZR-FE (E150). Looked
  up the wrong Euro NCAP rating (3 stars instead of 5), dropping safety to 5/10. Cascading
  generation error.

## Transmission Identification

### MMT misidentification on listing 4280612

**All three models misidentified the transmission on the 2007 Corolla 1.6 automatic.**

| Model | Called It | Actual |
|-------|----------|--------|
| Opus | 4-speed Aisin U340E/U341E torque converter auto | **5-speed MMT (robotized manual)** |
| Sonnet | 4-speed U341E torque converter auto | **5-speed MMT (robotized manual)** |
| Haiku | U-series torque converter auto | **5-speed MMT (robotized manual)** |

The European E150 Corolla 1.6 was **not offered** with a torque converter automatic — the only
non-manual option was the MMT (MultiMode Manual Transmission), a robotized single-clutch
manual. The 4-speed U341E was available only in Asian/Middle Eastern markets. The listing
description contains "gear change from steering wheel" — the MMT's paddle shifters — which
the U341E did not have.

**Impact:** All three models gave spec_match 9/10 praising the "torque converter automatic"
as meeting the buyer's hard requirement. The MMT is not a torque converter automatic. It has
a notoriously poor reliability record (actuator failures, premature clutch wear). This error
means all three evaluations gave an inflated spec_match score and may have recommended the
buyer visit a car with a problematic transmission.

### CVT Detection

All three models correctly identified the CVT transmission on both CVT-equipped cars
(3872109 and 4272435) and gave SKIP verdicts. This is the most critical safety check —
a model that misses a CVT would recommend a car that violates the buyer's hard requirements.

| Model | CVT Cars Caught | Accuracy |
|-------|----------------|----------|
| **Opus** | 2/2 | 100% |
| **Sonnet** | 2/2 | 100% |
| **Haiku** | 2/2 | 100% |

## Euro NCAP Inconsistency

Opus reported **different Euro NCAP adult occupant scores** for the same Avensis generation:
- Listing 3872109 (2018 Avensis): "98% adult occupant protection"
- Listing 4280818 (2017 Avensis): "93% adult occupant protection"

These are the same T270 generation, tested in the same 2015 Euro NCAP evaluation. The actual
result is 93%. Opus hallucinated the 98% figure for listing 3872109.

## Verdict Agreement

| Listing | Opus | Sonnet | Haiku | Agreement |
|---------|------|--------|-------|-----------|
| 3872109 | SKIP | SKIP | SKIP | unanimous |
| 4272435 | SKIP | SKIP | SKIP | unanimous |
| 4280612 | MAYBE | MAYBE | MAYBE | unanimous |
| 4280818 | MAYBE | MAYBE | MAYBE | unanimous |
| 4281217 | GO SEE | MAYBE | MAYBE | Opus differs |
| 4281378 | MAYBE | MAYBE | MAYBE | unanimous |

Verdicts agree in 5/6 cases. Only listing 4281217 differs: Opus gave GO SEE IT while Sonnet
and Haiku gave MAYBE. Opus was more confident in the 1ZR-FAE Corolla at 170k km; Sonnet
was more cautious about the Valvematic system and seller transparency.

## Scoring Patterns

### Average weighted scores across all 6 listings

| Model | Mean Score | Std Dev |
|-------|-----------|---------|
| **Opus** | 6.11 | 0.33 |
| **Sonnet** | 6.08 | 1.03 |
| **Haiku** | 6.95 | 0.54 |

### Scoring tendencies by category (averages across all 6 listings)

| Category | Opus | Sonnet | Haiku |
|----------|------|--------|-------|
| Mechanical Reliability | 6.2 | 5.5 | 6.8 |
| Maintenance Cost | 5.8 | 4.7 | 6.5 |
| Value For Money | 5.5 | 5.5 | 7.0 |
| Safety | 8.3 | 8.3 | 8.0 |
| Cosmetic Condition | 5.0 | 6.7 | 6.7 |
| Spec Match | 6.3 | 5.5 | 6.3 |
| Seller Trustworthiness | 4.7 | 6.2 | 7.0 |

Key observations:
- **Haiku is the most generous scorer** in every category except safety.
- **Sonnet is the harshest on maintenance** (avg 4.7 vs Opus 5.8 and Haiku 6.5).
- **Opus is the harshest on seller trustworthiness** (avg 4.7), heavily penalizing sparse
  listings and missing service history.
- **Sonnet has the highest variance** (std dev 1.03) — its scores swing between very low
  (4.70 for the CVT Corolla) and very high (7.80 for the misidentified Avensis). Opus is
  the most consistent (0.33).

## Cost and Speed

| Metric | Opus | Sonnet | Haiku |
|--------|------|--------|-------|
| Avg cost per eval | ~$0.75* | $0.33 | $0.07 |
| Avg time per eval | ~246s* | 155s | 96s |
| Total cost (6 evals) | ~$4.50* | $2.00 | $0.41 |
| Total time (6 evals) | ~25 min* | ~16 min | ~10 min |
| Cost ratio vs Opus | 1.0x | 0.44x | 0.09x |

*Opus cost/time estimated from the 4281217 comparison; exact per-listing data not captured
for the other 5 Opus evaluations.

## Conclusions

### Opus: Best available, but not infallible

- **83% engine identification accuracy** (5/6). Got 4281378 wrong — called it 2ZR-FE when
  the 1794cc displacement and 95kW output identify it as a 1ZZ-FE (different engine family,
  different car generation). This error was present in the original report but went undetected
  because the reviewer also assumed 2ZR-FE was correct.
- **Missed the MMT transmission** on 4280612 — called it a torque converter automatic when
  the European E150 Corolla 1.6 only came with MMT. All three models made this same error.
- **Hallucinated a Euro NCAP score** — cited 98% adult occupant for the 2018 Avensis when
  the actual result is 93%.
- Most consistent scoring (lowest variance). Best at detecting overpricing.
- Most conservative on seller trustworthiness — appropriately suspicious of sparse listings.
- Only model to give a GO SEE IT verdict (for the Corolla 4281217).
- **Still the best model** — its errors are less consequential than Sonnet's or Haiku's, and
  its scoring consistency is the strongest. But manual verification is needed.

### Sonnet: Good but has blind spots

- Caught both CVTs correctly. Generally thorough analysis with good red flag identification.
- **2 engine misidentifications (67% accuracy)**. The 4280818 error is the most consequential
  in the entire comparison — it would have led the buyer to prioritize a risky car.
- Also got 4281378 wrong (2ZR-FAE instead of 1ZZ-FE), like all three models.
- Most conservative scorer on average, which is good for a risk-averse buyer — but the
  conservatism collapses when it gets the engine wrong (7.80 for an overpriced high-mileage
  Avensis).
- Highest scoring variance — unreliable for consistent ranking across listings.
- **Good cost/quality tradeoff** at $0.33/eval, but the engine errors mean you can't fully
  trust the scores without cross-checking.

### Haiku: Too unreliable for evaluations

- **3 engine misidentifications (50% accuracy)**. Two different types of errors:
  wrong engine family (3ZZ-FE vs 1ZR-FE) and wrong engine variant (2ZR-FE vs 1ZR-FAE,
  2ZR-FAE vs 1ZZ-FE).
- **Systematically inflated scores.** Haiku's weighted scores are consistently the highest,
  averaging 6.95 vs Opus's 6.11. A SKIP car (3872109) scored 7.65 — higher than several
  MAYBE cars from Opus and Sonnet.
- Score inflation makes rankings unreliable. If you sorted listings by Haiku's scores,
  you'd visit the wrong cars.
- Verdicts are correct (all SKIPs caught, all MAYBEs reasonable), so Haiku could work as
  a binary "skip or investigate" filter — but not for scoring or ranking.
- **Extremely cheap** at $0.07/eval. 10x cheaper than Sonnet, 10x cheaper than Opus.

### Recommendation

**Use Opus for evaluations, but verify engine codes manually.** Opus is the most accurate and
consistent model, but its 83% engine accuracy and the MMT miss show that no model can be
fully trusted on technical identification. Cross-check the engine code against the listing's
displacement and power output — a 4cc discrepancy (1794 vs 1798) was enough to indicate a
completely different engine family. Also verify transmission type against the specific
market/generation, since auto24.ee labels both torque converter autos and MMTs as "automatic."

At ~$0.75 per listing, evaluating 50 cars costs ~$37.50, which is trivial compared to the
cost of buying the wrong car.

If cost is a hard constraint, **Sonnet is acceptable with manual verification** of both the
engine code and transmission type. Don't use Haiku for full evaluations.
