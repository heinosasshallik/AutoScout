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
| 4281378 (1794cc, 95kW) | 2ZR-FE | **correct** | 2ZR-FAE | 2ZR-FAE |

| Model | Correct | Wrong | Accuracy |
|-------|---------|-------|----------|
| **Opus** | 6 | 0 | **100%** |
| **Sonnet** | 4 | 2 | 67% |
| **Haiku** | 3 | 3 | 50% |

### How engine errors affected evaluations

Each engine misidentification caused downstream scoring errors:

- **Haiku on 4281217**: Called it 2ZR-FE (1.8L) instead of 1ZR-FAE (1.6L). Inflated scores
  because the 2ZR-FE is simpler and more reliable. Weighted score 7.65 vs Opus's 6.70.

- **Haiku on 4280612**: Called it 3ZZ-FE (E120 generation) instead of 1ZR-FE (E150). Looked
  up the wrong Euro NCAP rating (3 stars instead of 5), dropping safety to 5/10. Cascading
  generation error.

- **Sonnet on 4280818**: Called it 2ZR-FE instead of 2ZR-FAE. Missed the Valvematic system
  entirely, called the engine "bulletproof," and gave reliability 8/10 and maintenance 8/10.
  Produced the highest weighted score in the entire comparison (7.80) for a car that Opus
  rated 5.70. **This is the most consequential error** — it would lead to prioritizing a
  risky, overpriced car.

- **Sonnet on 4281378**: Called it 2ZR-FAE instead of 2ZR-FE. Flagged Valvematic risks that
  don't exist on this car. Over-penalized maintenance cost.

- **Haiku on 4281378**: Same error as Sonnet. Called it 2ZR-FAE instead of 2ZR-FE.

## CVT Detection

All three models correctly identified the CVT transmission on both CVT-equipped cars
(3872109 and 4272435) and gave SKIP verdicts. This is the most critical safety check —
a model that misses a CVT would recommend a car that violates the buyer's hard requirements.

| Model | CVT Cars Caught | Accuracy |
|-------|----------------|----------|
| **Opus** | 2/2 | 100% |
| **Sonnet** | 2/2 | 100% |
| **Haiku** | 2/2 | 100% |

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

### Opus: Most Reliable (recommended for production use)

- **100% engine identification accuracy** — the only model with a perfect record.
- Most consistent scoring (lowest variance). Scores are well-calibrated and defensible.
- Best at detecting overpricing (gave 4/10 on value for the overpriced Avensis).
- Most conservative on seller trustworthiness — appropriately suspicious of sparse listings.
- Only model to give a GO SEE IT verdict (for the Corolla 4281217), showing willingness to
  commit when the evidence supports it.
- **Downside**: 2x the cost of Sonnet, 10x the cost of Haiku.

### Sonnet: Good but has blind spots

- Caught both CVTs correctly. Generally thorough analysis with good red flag identification.
- **2 engine misidentifications (67% accuracy)**. The 4280818 error is serious — it would
  have led the buyer to prioritize a risky car. The 4281378 error over-flagged nonexistent
  Valvematic issues.
- Most conservative scorer on average, which is good for a risk-averse buyer — but the
  conservatism collapses when it gets the engine wrong (7.80 for an overpriced high-mileage
  Avensis).
- Highest scoring variance — unreliable for consistent ranking across listings.
- **Good cost/quality tradeoff** at $0.33/eval, but the engine errors mean you can't fully
  trust the scores without cross-checking.

### Haiku: Too unreliable for evaluations

- **3 engine misidentifications (50% accuracy)**. Two different types of errors:
  wrong engine family (3ZZ-FE vs 1ZR-FE) and wrong engine variant (2ZR-FE vs 1ZR-FAE,
  2ZR-FAE vs 2ZR-FE).
- **Systematically inflated scores.** Haiku's weighted scores are consistently the highest,
  averaging 6.95 vs Opus's 6.11. A SKIP car (3872109) scored 7.65 — higher than several
  MAYBE cars from Opus and Sonnet.
- Score inflation makes rankings unreliable. If you sorted listings by Haiku's scores,
  you'd visit the wrong cars.
- Verdicts are correct (all SKIPs caught, all MAYBEs reasonable), so Haiku could work as
  a binary "skip or investigate" filter — but not for scoring or ranking.
- **Extremely cheap** at $0.07/eval. 10x cheaper than Sonnet, 10x cheaper than Opus.

### Recommendation

**Use Opus for evaluations.** The engine identification accuracy alone justifies the cost —
a wrong engine ID cascades into wrong reliability assessments, wrong maintenance predictions,
and wrong purchasing decisions. At ~$0.75 per listing, evaluating 50 cars costs ~$37.50,
which is trivial compared to the cost of buying the wrong car.

If cost is a hard constraint, **Sonnet is acceptable with manual verification** of the engine
code. Cross-check the engine identification against the listing's displacement and power
output before trusting the scores. Don't use Haiku for full evaluations.
