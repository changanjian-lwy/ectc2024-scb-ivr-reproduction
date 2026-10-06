# A156 - the formula spec at its limit, on A152's robustness matrix (RESULTS)
Boundary: 7fb6a8b. Records: release records-a156 (14 runs). Outputs: a156_summary.json (a156_analyze.py), a156_predictions.json.

## 0. Verdict
- **4/5 as registered (criterion 3 fails), so by the registered rule the adopted drive stays at x_on <= 1.8 V.**
- **The voltage rule holds on the whole matrix at x_on = 3.0 V** (125 pH, turn-on 24 A/ns, turn-off 72): every row and
  four modules <= 40 V, worst L x 1.3 l_p48_1us 39.5 V (predicted 39.7), four modules 39.3 V, nominal 39.2 V. The
  ramp rows read 0.5-0.9 V above the offset prediction (slew2 39.2 V), so x_on 3.2 V on the matrix is extrapolated.
- **Start-up with A155's ton:** 144-153 A (L x 0.7 196 A, its ideal reference ~200 A); post-step peaks <= 182 A.
- **Criterion 3's misses, none with a peak, voltage or Vo consequence:**
  - late fires (a timed edge whose target had passed, fired at once): l_m80_10us 16 (13 on phase 4; ref 2), L x 0.7
    rows 5 (ref 2). On l_m80_10us they grow with the loop: 0 / 6 / 16 at 50 / 100 / 125 pH (A152 S50, S100, here),
    whatever x_on. Post-step peak there 159 A, V_DS 34.9 V.
  - slew2 / slew5: one phase-1 duplicate each (dup_other), a low-off and turn-on recorded twice 0.0-0.2 ns apart at a
    clock-window boundary; valley -20.3 A and peaks 140 A normal - the race family of K1 / K5, not a known class.
- Reading: the drive's voltage limit is x_on <= 3.0 V (checked) to 3.2 V (D68); the full controller criteria hold at
  x_on 1.8 V and 50 pH (S50). Larger loops add late fires on falling -8 V ramps, which is one more reason to bound the
  loop.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | V_DS <= 40 V, 13 rows | PASS (<= 39.5 V) |
| 2 | start-up <= max(200, ref + 5) A | PASS (144-196 A) |
| 3 | post-step <= min(ref + 5, 200), 0 NEW, late <= ref + 2 | FAIL: l_m80_10us late 16, L07 rows late 5, slew2 / slew5 one dup_other each |
| 4 | Vo extreme / back | PASS |
| 5 | four modules, criteria 1-3 | PASS (39.3 V, 153 / 173 A, late 0) |

## 2. Limits
- One point (125 pH, 24 A/ns, Q 7); the late-fire trend with L rests on three points (50 / 100 / 125 pH) of one row.
- The late fires' mechanism (phase 4's slot after a falling ramp) is not traced here.
