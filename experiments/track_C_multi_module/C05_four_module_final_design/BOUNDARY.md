# C05 - Four modules of the final single-module design (BOUNDARY)
Track C. Written and committed before the C05 runs. Looked at beforehand: C03/C04 results and cfgs, A129 cfgs; one 200 us smoke run of n0 (timing 52 s, no overlap, peak 163 A, locked) - not analysed further.
Decision it changes: whether the multi-module summary (written for A105's 1 MHz module) can be re-stated for the final design (A124 2.5 MHz + A129 gated vff), i.e. whether "x4 modules" holds there.
Cheaper check done first: none; structure is x4 by construction (cfg differs from A129's only by `"modules": 4`, load steps x4), what is untested is interleave at T/16 = ~25 ns and sharing at the new design. Budget: 18 runs, ~5 min each, --jobs 6, ~17 min.

## 1. What and why
- Configs from `make_cfgs.py`: A129 `g125_<row>` + `modules 4`; load steps x4. 16 matrix rows (n0; m1n m1p m3n m3p; j30 j100; s_m25 s_p25 s_m62 s_p62; l_p48_1us l_p48_5us l_m48_1us l_m48_5us l_m80_10us) + ls_p5, ls_p10 (slave 1's L x1.05 / x1.10). Step at 800 us, ends 1000/1200 us as A129.
- Reference per row: A129's single-module `run_g125_<row>`; ls_* against this experiment's n0.
- Not tested: module-to-module Cs / R spread (C04 covers the old design), thermal, shared-input impedance.

## 2. Criteria (C03's, on the final design; window = last 200 master periods, before the step for step rows)
1. No overlap in any module. Peak <= 200 A (step rows: peak after the step, max highoffs i_a, t >= 800 us).
2. Locked: slave periods = master's within 0.1 ns; the 16 gaps within T/16 +- 0.1 ns at m = 0, sigma = 0 (T/16 ~ 25 ns).
3. Per module vs the single-module row (n0, m, j rows): valleys within +-0.5 A; HS turn-on V_DS within +-0.2 V; LS turn-on V_DS max <= single + 0.3 V; turn-off sd within x(1+-0.3) or +-0.05 A when < 0.17 A.
4. Steps: Vo extreme within +-10% of the single module's; back within 1% within single + 2 us; ladder deviation peak <= single + 0.01.
5. ls_p5 / ls_p10: slave 1 carries -4.6 +- 1.5% / -9 +- 3% of a nominal slave (current ~ 1/L); its LS turn-on V_DS <= 0 and valleys <= -2.5 A. Valley and HS shifts reported, no band (old-design bands do not carry over).
6. Late fires <= single module's row (+6 in jitter rows).

## 3. Predictions (not criteria)
All criteria expected to pass as in C03 (72 module-runs, all within bounds). Risk: the 25 ns T/16 spacing and the 8 V falling row (single 170.9 A at 10 us); a ls_p10 slave with 15.6 A target valley has more margin than the old 5% design.

## 4. Decision rule
All criteria pass -> the multi-module summary gets a one-block addendum for the final design; the remaining 1 MHz-design text stays as the record. Misses are listed with their numbers; a hard-constraint miss (overlap, > 200 A) would be a finding to diagnose on Opus, not fixed here.
