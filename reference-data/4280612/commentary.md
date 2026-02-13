# Model Comparison: Listing 4280612

2007 Toyota Corolla 1.6, 220,000 km, automatic, €3,250

## Results

|                          |   Opus |  Sonnet |  Haiku |
|--------------------------|--------|---------|--------|
| Weighted Score           |   6.10 |    5.40 |   6.50 |
| Verdict                  |  MAYBE |   MAYBE |  MAYBE |
| Engine ID                | 1ZR-FE | 1ZR-FE  | 3ZZ-FE |
| Transmission ID          | U340E/U341E TC auto | U341E TC auto | U-series TC auto |
| Mechanical Reliability   |      5 |       4 |      6 |
| Maintenance Cost Outlook |      6 |       3 |      6 |
| Value For Money          |      6 |       5 |      7 |
| Safety                   |      7 |       8 |      5 |
| Cosmetic Condition       |      5 |       6 |      7 |
| Spec Match               |      9 |       9 |      9 |
| Seller Trustworthiness   |      5 |       6 |      7 |
| Red Flags                |      8 |       8 |      7 |
| Green Flags              |      8 |       8 |      8 |
| Cost (USD)               |    N/A |   $0.36 |  $0.07 |
| Time (seconds)           |    N/A |     171 |     94 |

## Key Finding

**Haiku misidentified the engine as 3ZZ-FE.** The listing data shows 1598cc and 91kW, which
is conclusively the 1ZR-FE (E150 Corolla, 2007+). The 3ZZ-FE is the *previous generation*
engine (E120 Corolla, 2000-2007) and only produces 81kW. Haiku confused the generations.

**This cascading error affected the safety score.** Because Haiku thought it was an E120
Corolla, it looked up the E120's Euro NCAP rating (3 stars from the 2002 test) instead of the
E150's rating (5 stars). This dropped Haiku's safety score to 5/10 — the lowest among the
three models — while Opus and Sonnet correctly gave 7-8/10 for the 5-star E150.

Interestingly, Haiku's *overall* weighted score (6.50) is still the highest of the three,
because it inflated other categories (value 7, cosmetic 7, seller trust 7) enough to
compensate. This is the opposite error direction from listing 4281217, where Haiku's wrong
engine inflated scores — here the wrong engine *deflated* the safety score but Haiku's
generosity elsewhere masked the problem.

**Sonnet was the most pessimistic.** It gave maintenance cost 3/10 and called out that
repair costs "will likely exceed the car's value within 1-2 years." This is arguably too
harsh — at 220k km there are genuine risks, but the 1ZR-FE is simpler and more proven than
the 1ZR-FAE. Opus struck a better balance at 6/10.

## Conclusion

- **Opus**: Correct engine ID, balanced assessment. Best calibrated scores for a high-mileage
  but mechanically sound platform.
- **Sonnet**: Correct engine ID, most conservative. The 3/10 maintenance score may be
  overdone, but the 5.40 weighted score appropriately signals high risk.
- **Haiku**: Wrong engine ID (3ZZ-FE vs 1ZR-FE). Cascading error lowered safety score.
  Other scores inflated. The final 6.50 weighted score is unreliable.
