# A114 - the 20% and 25% designs with the comparator phase-1 turn-off, on the standard matrix (RESULTS)

Track A.

**Boundary:** `BOUNDARY.md`, committed (2aa0c98) before any run.

**Records:** `cosim/run_*.json`; `a114_summary.json`
(`a114_analyze.py`).

**Physical model:** as A112 (Verilog RTL, A88 kernel2 plant, `slot_lo`,
25 C, one module), with phase 1's turn-off decided by the comparator.

## 0. Verdict

1. **The comparator turn-off keeps the steady state.**
   - **Efficiency:** 20% 90.18% (timed 90.17); 25% 90.15% (90.14).
   - The high side's level holds under mismatch and jitter.
   - No overlap in 32 runs.
2. **It fixes the load steps and the falling line steps in both
   designs:**
   - **load steps:** all within 1% in ≤ 11 µs;
   - **−4.8 V / 1 µs:** +13.5 / +15.8 mV, back in 2.7 / 2.8 µs. Timed:
     −25.7 / −34.0 mV, 75 / 182 µs.
3. **It breaks the rising line steps:**

   | row | 20% comparator / timed | 25% comparator / timed |
   |---|---|---|
   | +4.8 V / 1 µs | **290 A**, −75.5 mV / 199 A, −9.1 mV | **287 A**, −70.9 mV / 213 A, −12.8 mV |
   | +4.8 V / 10 µs | **250 A**, −52.2 mV / 200 A, −9.6 mV | **246 A**, −52.5 mV / 202 A, −11.6 mV |

   **Mechanism** (c25_l_p48_1us traced):
   - **Phase 1:** with the comparator it stays at its boundary (valley
     −31 A). Its rail rises, so its peak climbs (169 → 278 A) and its
     period stretches (302 → 441 ns).
   - **Phases 2-4** follow phase 1's period on their slots, but their
     rails have not risen. Their low sides stay on too long, and their
     valleys fall to −135 / −184 / −218 A. They pull charge from the
     output, and Vo dips.
   - **The loop** raises Ton (664 → 1060 LSB), which feeds phase 1's
     stretch.

   The timed turn-off fails the opposite way (A112: phase 1's valley
   rises on falling steps). At 5% both effects were small. A larger
   negative current magnifies them.
4. **Jitter costs** (registered bounds 1.3 at 30 ps, 1.8 at 100 ps):
   - 30 ps: 0.59-0.68 A against 0.41-0.48 A (×1.4, a miss);
   - 100 ps: 1.83-2.08 against 1.21-1.42 A (×1.46, within).
5. **The −8 V / 10 µs step** (to 40 V):
   - 20% recovers immediately: −9.1 mV, 0 µs. The registered "slow"
     missed: it is fast.
   - 25% takes 175 µs, as A113.

## 1. What the high-side zero-voltage work (A110-A114) establishes

**Physics.** The high side reaches zero voltage when the negative
current reaches the node's energy need.
- D57: 26.7% of the peak at Eq. (4)'s 1.47 nH. Measured: first at 25%.
- P24's 1-2% gives valley switching.

**Practical zero voltage (25%) and the efficiency optimum (20%).** Both
are stable in steady state and robust to driver mismatch and jitter.
- **Efficiency:** 90.1-90.2%, +2.2 points over the 5% design.
- **The high side's hard-turn-on loss:** 8.9 → 0.04 W (25%), 0.7 W
  (20%).

**The limit is fast line transients.** With a large negative current, a
fast rail change (≳ 0.5 V/µs) breaks "phase 1 at its boundary, phases
2-4 on slots".
- the timed phase-1 turn-off: on falling steps (slow oscillation);
- the comparator: on rising steps (runaway to 250-290 A).

Load steps and slow inputs are fine with the comparator.

**What would remove the limit** (a controller architecture change, not
a parameter):
- each phase keeps its own boundary (its own current-decided turn-off),
  with the interleave corrected toward the slots, instead of slots that
  ignore each phase's rail;
- or, at the system level, an input slew limit (A108 gives the numbers
  at 5%).

## 2. Registered criteria (BOUNDARY Section 1)

| criterion | result |
|---|---|
| no overlap | pass, 32 of 32 |
| steady state: high side ±0.3 V, low side ≤ 0 (m), efficiency ±0.2 | pass |
| jitter spread bounds | j30 **miss** (×1.4); j100 pass |
| load steps ≤ 15 µs | pass |
| ±4.8 V line steps ≤ 20 µs | +4.8 V / 10 µs **miss** (22.9 / 22.8 µs); the rest pass |
| −8 V / 10 µs slow (≥ 50 µs) | 25% as registered; **20% miss** (fast) |
| line peaks ≤ A112 + 5 A | **miss** in both rising steps of both designs (246-290 A) |
