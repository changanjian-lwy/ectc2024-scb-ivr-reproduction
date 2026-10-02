# A111 - a zero-voltage valley for the high side's turn-on timing (BOUNDARY)

Track A, main line. **Written before any A111 run.**

**Source:** A110 RESULTS 0.2.
- At 30% negative current the node reaches the rail and the high side's
  reverse conduction clamps V_DS.
- The valley measurement then reports "flat" (no update), and the
  predictive turn-on drifts: phase 1's delay fell to 2.8 ns, there were
  hard turn-ons up to 15.7 V, 236 A peaks, and a −62.5 A step that did
  not recover.

## 1. The factor: cfg `valley_zero` = 1

- **The measured valley of the high side stops at its first V_DS ≤ 0,**
  the node's arrival at the rail. The A92 corrector then sets the
  predictive turn-on at that instant plus its target (93.75 ps). The
  high side turns on as the node arrives, with the least reverse
  conduction.
- **It changes nothing while V_DS stays above zero:** the minimum is
  then the same.
- **Code:** the Monitors' `vmin_zero`, built for A101's auxiliary
  branch, is now also reachable without a branch (`bridge.py`, one line;
  the default 0 keeps every earlier path).
- **A known risk from A101:** there, with the branch, `valley_zero` made
  the turn-off currents of phases 2-4 unstable. A111 tests it without
  the branch.

## 2. Runs (`make_cfgs.py`; each source configuration plus `valley_zero`)

| run | source | check |
|---|---|---|
| z5 | C02 s1_n0 (5%) | **identity:** V_DS never reaches 0, so every record equals C02's (`cfg` and `note` aside) |
| z20 | A110 n20 (20%, valleys 2.3-3.0 V) | **identity** with A110 n20 |
| z25 | A110 n25 | phase 4 reached zero in A110 |
| z30 | A110 n30 | the failing case |
| z30_s_p62, z30_s_m62, z30_j30 | A110's 30% steps and jitter | robustness |

## 3. Registered predictions and criteria (last 200 periods; before the step for step rows)

1. **z5, z20:** identical to their sources in every record except
   `cfg`, `note`, `wall_s` and `provenance`.
2. **z30:**
   - every phase's high-side turn-on V_DS ≤ +0.3 V (mean) and ≤ +1.0 V
     at its maximum: no hard turn-on;
   - peak ≤ 200 A over the run;
   - low-side turn-on V_DS ≤ 0;
   - turn-off sd ≤ 0.5 A (no instability of phases 2-4, the A101 risk);
   - Vo 1.000 V ± 1 mV;
   - late fires ≤ 5.
3. **z30 efficiency** (D62 middle case, measured waveforms, reverse
   conduction included): ≥ A110 n30's 89.42%, and within ±0.5 points
   of the 89.91% predicted for 30% in A110. Reverse conduction
   ≤ 0.5 W.
4. **z25:** every phase ≤ +0.9 V (mean). Phases 1-3 stay at ~0.7 V, as
   their valleys do not reach zero. Peak ≤ 200 A after the handover
   (A110: 204 A at 77 µs: not predicted to change, reported).
5. **z30 load steps:** within ±25% of C02's 5% steps (+11.30 /
   −14.59 mV) and back within 1% in ≤ 15 µs. **z30_j30:** turn-off sd
   within C02 s1_j30's × (1 ± 0.5); high side ≤ +0.5 V (mean).

**What would falsify it:**
- at 30%, hard turn-ons remaining (max > 1 V) or the A101 instability
  (sd > 0.5 A);
- in that case zero voltage needs a different turn-on rule, such as a
  current-zero turn-on, not this measurement.

## 4. What stays assumed

- The zero-crossing of V_DS is measured ideally (a comparator with no
  offset or delay, like the existing valley measurement).
- D62 middle case.
- The A110 assumptions.
