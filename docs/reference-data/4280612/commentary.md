# Model Comparison: Listing 4280612

2007 Toyota Corolla 1.6, 220,000 km, automatic, €3,250

## Results

|                          |   Opus |  Sonnet |  Haiku |
|--------------------------|--------|---------|--------|
| Weighted Score           |   6.10 |    5.40 |   6.50 |
| Verdict                  |  MAYBE |   MAYBE |  MAYBE |
| Engine ID                | 1ZR-FE | 1ZR-FE  | 3ZZ-FE |
| Transmission ID          | U340E/U341E TC auto | U341E TC auto | U-series TC auto |
| **Correct Transmission** | **MMT (robotized manual)** | **MMT** | **MMT** |
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

## Key Findings

### 1. All three models misidentified the transmission

**All three called it a torque converter automatic. It is almost certainly a 5-speed MMT
(MultiMode Manual Transmission) — a robotized single-clutch manual.**

Evidence:
- The European E150 Corolla 1.6 was **not offered** with a torque converter automatic. The
  only non-manual option in Europe was the MMT (a robotized manual based on the C-series
  gearbox). The 4-speed U341E torque converter auto was available in Asian/Middle Eastern
  markets only.
- The listing description includes **"gear change from steering wheel"** — this is the MMT's
  steering wheel paddle shifters for sequential gear changes. The U341E did not come with
  paddle shifters on the E150 Corolla.

**This is the most consequential error for the buyer.** All three models gave spec_match
9/10, praising the "torque converter automatic" as meeting the buyer's hard requirement.
But the MMT is not a torque converter automatic — it's a robotized manual with a notoriously
poor reliability record. The MMT actuator system is prone to failure, and clutch wear is
accelerated compared to a manual. Toyota-club.net notes that "rare owners of cars with MMT
drove more than 50-60 thousand without malfunctions."

Whether the MMT passes the buyer's criteria ("manual or torque converter auto only") is
debatable — it's technically a manual gearbox operated by a robot, not a CVT or DCT. But
the buyer likely specified "torque converter auto" because they want proven, smooth automatic
shifting, which the MMT does not provide.

### 2. Haiku misidentified the engine as 3ZZ-FE

The listing data shows 1598cc and 91kW, which is conclusively the 1ZR-FE (E150 Corolla,
2007+). The 3ZZ-FE is the *previous generation* engine (E120 Corolla, 2000-2007) and only
produces 81kW. Haiku confused the generations.

**This cascading error affected the safety score.** Because Haiku thought it was an E120
Corolla, it looked up the E120's Euro NCAP rating (3 stars from the 2002 test) instead of the
E150's rating (5 stars). This dropped Haiku's safety score to 5/10 — the lowest among the
three models — while Opus and Sonnet correctly gave 7-8/10 for the 5-star E150.

Interestingly, Haiku's *overall* weighted score (6.50) is still the highest of the three,
because it inflated other categories (value 7, cosmetic 7, seller trust 7) enough to
compensate.

**Sonnet was the most pessimistic.** It gave maintenance cost 3/10 and called out that
repair costs "will likely exceed the car's value within 1-2 years." This is arguably too
harsh — at 220k km there are genuine risks, but the 1ZR-FE is simpler and more proven than
the 1ZR-FAE. Opus struck a better balance at 6/10.

## Conclusion

- **Opus**: Correct engine ID, but wrong transmission (called it torque converter auto,
  actually MMT). The spec_match 9/10 is invalidated — this car may not meet the buyer's
  hard requirements.
- **Sonnet**: Correct engine ID, but same transmission error. Most conservative scorer —
  the 5.40 weighted score is the most appropriate given the MMT reliability concerns, even
  if Sonnet arrived at it for the wrong reasons.
- **Haiku**: Wrong engine ID (3ZZ-FE vs 1ZR-FE) AND wrong transmission. Cascading engine
  error lowered safety score. Other scores inflated. The 6.50 weighted score is unreliable.
