# Model Comparison: Listing 3872109

2018 Toyota Avensis Touring 1.8, 84,000 km, automatic (CVT), €14,225

## Results

|                          |   Opus |  Sonnet |  Haiku |
|--------------------------|--------|---------|--------|
| Weighted Score           |   6.20 |    6.05 |   7.65 |
| Verdict                  |   SKIP |    SKIP |   SKIP |
| Engine ID                | 2ZR-FAE| 2ZR-FAE | 2ZR-FAE |
| Transmission ID          | CVT (Multidrive S / K311) | CVT (Multidrive S) | CVT (Multidrive S) |
| Mechanical Reliability   |      7 |       6 |      9 |
| Maintenance Cost Outlook |      6 |       5 |      8 |
| Value For Money          |      7 |       6 |      8 |
| Safety                   |      9 |       9 |      9 |
| Cosmetic Condition       |      5 |       7 |      7 |
| Spec Match               |      1 |       3 |      2 |
| Seller Trustworthiness   |      5 |       6 |      8 |
| Red Flags                |      6 |      10 |      5 |
| Green Flags              |      8 |      10 |     11 |
| Cost (USD)               |    N/A |   $0.34 |  $0.06 |
| Time (seconds)           |    N/A |     159 |     96 |

## Key Finding

**All three models correctly identified the CVT and rejected the car.** This is the most
important test here — the listing says "automatic" but the Multidrive S is a belt-type CVT,
which violates the buyer's hard requirement. All three models caught this, researched the
K311 CVT properly, and gave a SKIP verdict.

**Haiku dramatically inflated non-transmission scores.** Despite correctly rejecting the car,
Haiku scored mechanical reliability at 9/10 and maintenance at 8/10 — as if the CVT didn't
matter for those categories. Opus and Sonnet appropriately penalized reliability and
maintenance for the CVT's known failure modes and expensive repair costs. Haiku also gave
seller trustworthiness 8/10 for a seller with no phone number and a feature-list description,
while Opus and Sonnet gave 5-6.

## Conclusion

- **Opus**: Correct verdict, balanced scoring. Appropriately harsh on spec match (1/10) and
  penalized reliability/maintenance for CVT. Conservative on non-relevant scores since the
  car is a SKIP anyway.
- **Sonnet**: Correct verdict, most thorough red flag analysis (10 flags). Slightly more
  generous on spec match (3/10) but still clearly communicated the hard rejection.
- **Haiku**: Correct verdict, but scores are unreliable. Giving 9/10 mechanical reliability
  to a CVT car the buyer explicitly rejects inflates the weighted score to 7.65 — misleadingly
  high for a car that should never be visited. If these scores were used for ranking, this
  SKIP car would outrank several MAYBE cars.
