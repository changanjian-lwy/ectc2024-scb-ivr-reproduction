# A131 - node devices 1 high + 2 low against 2 + 3, paper level (RESULTS)
Track A, main line (P24 Table 3 vs P24 Sec. IV / P25). Paper-level only: D57 + A115's orbit + D62, 2.5 MHz, L 2.933 nH. No cosim, no BOUNDARY: the calculation was the value gate and it closed the question (run before any BOUNDARY, so nothing here is a registered prediction).
Records: a131_predict.py -> a131_predictions.json. R scaled by the duty-weighted on-resistance (2+3: 0.540 mOhm, 1+2: 0.842 mOhm).
## 0. Verdict
- Check of the method: 2+3 at 12.5% gives 90.43% (A124's registered prediction; measured 90.61%), so the budget reproduces the main line.
- **1+2 lowers D57's threshold 18.9% -> 14.4% and the 12.5% high-side turn-on 3.9 V -> 1.5 V (ph 4: 0.5 V); at 15% it is zero voltage (-0.5 V).**
- **It costs 1.8 points of efficiency:** 88.59% vs 90.43% at 12.5% (conduction 21.0 vs 13.4 W, gate drive 2.1 vs 3.4 W). Best 1+2: 88.69% (10%); best 2+3: 90.45% (15%).
- **What full ZVS is worth here: hard turn-on is only 0.7 W at 12.5% (2+3), 0.2 W at 15%.** The remaining soft-switching gain is <= 0.7 W (0.25 points); 1+2 spends ~7 W more in conduction to get it.
- Decision: keep 2+3 (L9 unchanged); no cosim. Nothing to evaluate for Mihai except that P24's 1+2 (Sec. IV) is the worse choice at this operating point.
## 1. Limits
- D62 middle scenario, 25 C; R scaling by duty weighting is approximate (1+2 may differ by a few % in conduction).
- Reverse-conduction energy not included (A124: +0.18 points measured over prediction, both configs).
