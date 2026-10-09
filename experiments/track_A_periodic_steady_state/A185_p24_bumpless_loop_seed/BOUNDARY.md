# A185 - A184 with a bumpless loop seed (BOUNDARY)
Method: mixed (cosim, plant V5, RTL e1cf0a7 with cfg_ton_s; cfg only: ton_ns per board. Math: the seed formula below)
Track A, package layer. Written and committed before the runs.
Decision it changes: whether a 25 C factory seed ton_ns = T_ss + (kp + ki) (Vo_entry - vref) removes A184's handover
dips, so that t0 200 ns + mode-S trim + this seed becomes the start-up spec at 25 C. The hot case is a separate fix
(Vo-triggered handover, next).
Cheaper check done first: A184's 14 runs. Where the loop's first Ton after the kp step was within -2..+3 ns of its
steady Ton (S75, N75, N07), Vo never dipped (minimum 1.000 V). At -5 ns it dipped to 0.982-0.997 V, at -15 ns to
0.971 V. Budget: 11 runs, --jobs 6, ~2.5 h.

## 1. What and why
- A184 failed c6 on N0, F0, N13 and four modules at 25 C. Mode S at 200 ns ends with valleys at +25..+47 A, while
  mode P regulates -15.6 A. That charge gap turns the loop's first-Ton shortfall (seed + kp step below the steady
  Ton) into a Vo dip.
- Seed rule: the first sample gives Ton = seed - (kp + ki)(Vo - vref). Setting seed = T_ss + (kp + ki)(Vo_entry -
  vref) puts that Ton at T_ss. T_ss and Vo_entry come from A184's 25 C run of the same board (mode S is unchanged,
  g0). That run plays the factory's closed-loop measurement after the mode-S trim, so the 25 C test is
  in-sample by construction. Seeds (ns): S75 45.355, S0 54.563, N0 44.480, N75 35.577, N07 33.450, N13 55.541,
  F0 42.962, four modules 44.443 (seeds.json). The clamps follow (0.5x / 2x seed).
- Runs: every A184 25 C board (S75 and N0 full with +4.8 V / 1 us at 500 us; the rest and four modules to 500 us).
  N0 / S0 / S75 at 125 C keep the 25 C seed, as diagnostics.
- Not tested: other rows; the hot handover's fix; four modules at the corners.

## 2. Criteria (A184's definitions, a184_analyze; every module)
 g0 Sections before mode P's entry equal A184's run of the same condition, bit for bit (mode S is unchanged).
 c1 start-up / handover <= 200 A;  c2 post-step <= 200 A (full runs);  c3 V_DS <= 40 V, COMPLETED, 0 shoot-throughs
    / overlaps;  c4 Vo(143.5 us) in 0.99-1.17 V;  c5 450-495 us per-phase peaks within +-2 A of the t0 = 400 record.
 c6 at 25 C: handover Vo minimum (entry .. + 50 us) >= the t0 = 400 record's - 5 mV.
Diagnostic: c6 at 125 C (expected to fail: kp x (Vo_entry - vref) is 45-48 ns on the slow boards, so Ton sits on
the 0.5x clamp), the loop's first Ton - T_ss, and Ton's overshoot after entry.

## 3. Predictions (not criteria)
- g0 holds. First Ton within +-1 ns of T_ss on every 25 C board (ADC rounding, one ki step).
- 25 C handover Vo minima >= 0.995 V everywhere (A184's no-dip group: 1.000 V). Handover peaks within +-10 A of
  A184's.
- c5 holds (the clamps move but do not bind in steady state).
- 125 C: minima 0.975-0.99 V as in A184 (the seed is not the hot cause).

## 4. Decision rule
- g0 fails: code / cfg defect; stop.
- c1-c6 pass at 25 C: the start-up spec at 25 C is t0 200 ns + per-board mode-S trim (cfg_ton_s) + bumpless seed
  (ton_ns). FINAL_SPEC gets the start-up row at 25 C, and the hot handover stays open until the Vo-triggered
  handover is tested.
- c6 still fails at 25 C: the seed does not remove the dip (the valley gap alone causes it). Named; next is the
  handover's timing.
