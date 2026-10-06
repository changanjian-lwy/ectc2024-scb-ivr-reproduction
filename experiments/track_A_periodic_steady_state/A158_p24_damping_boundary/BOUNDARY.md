# A158 - where the loop-damping boundary lies (BOUNDARY)
Method: mixed (math: harness ring residuals and two competing rules; RTL cosim cfg only, frozen design)
Track A, package layer. Written and committed before the runs, after A157.
Decision it changes: whether the damping requirement is a fixed "ring Q <= 30" (A157, tested at 50 pH only) or must
tighten with the loop inductance.
Cheaper check done first: A145's harness turn-off ring at 72 A/ns: ring period 2.4 / 3.4 ns at 50 / 100 pH; pk-pk ring
left 20 ns after the peak 1.5 V (50 pH, Q 30), 7.2 V (100 pH, Q 30), 3.0 / 3.7 V (50 pH, Q 100 / 300), 12.4 V (100 pH,
Q 100). But 300 pH at Q 7 (7.5 V left) held in A154, so the residual alone does not decide; hence two rules.
Budget: 5 runs, ~1 h.

## 1. What and why
- Rows (A152's s100_l_p48_1us cfg: +4.8 V / 1 us at 1000 us, turn-off 72 A/ns, start-up ton by A155): q15_s100,
  q30_s100, q100_s100 (100 pH, turn-on 18 A/ns), q100_s50, q300_s50 (50 pH, 36 A/ns).
- A row "holds" when A152's judge (against the ideal-plant l_p48_1us reference) finds no V_DS, start-up, post-step,
  NEW, late-fire or Vo miss.
- H1 (Q only): holds iff Q <= 30. H2 (residual): holds iff the harness's 20 ns residual <= 4 V.

## 2. Criteria
1. H1's hold / fail call is right on all 5 rows.
2. q30_s100 holds (A157's "Q <= 30" carries to 100 pH).

## 3. Predictions (a158_predictions.json)
H1: q15_s100, q30_s100 hold; q100_s100, q100_s50, q300_s50 fail. H2: q15_s100, q100_s50, q300_s50 hold;
q30_s100, q100_s100 fail. The two disagree on 3 rows.

## 4. Decision rule
- 1 and 2 pass: the spec keeps "ring Q <= 30" for L <= 100 pH, and Q 100 is outside it.
- 2 fails: the requirement tightens with L (Q <= 15 at 100 pH, or the bound in the rule that fits).
- 1 fails elsewhere: report the boundary as measured; the rule is whichever of H1 / H2 (or neither) matches.
