# A250 - the turn-on delay as a ladder lever: the start-up ladder in D63 with the clamp block (RESULTS)
Boundary and block: 2197119. Replays: a250_d63.py -> a250_summary.json (seconds; no cosim). Records replayed: A249
run_s_u_S75h_30 (fixed arm), A245 run_r_u_S75h_30 (learner). Board S75h, 75 A start-up (30 % load), D57 thresholds at
25 C.

## 0. Verdict
- **k1 passes, k2 and k3 miss.** By the rule, the learner's start-up benefit is something D63 lacks. The start-up
  ladder goes to the physical model (cosim). D63 cannot be used to design it.
- **The delay is a lever in D63, with the right sign.**
  - With the fixed arm's recorded delays, rail 1 rises to 15.8 V at 135 us. The deviation peaks at 4.1 V at 137 us
    (cosim 6.4 V at 137 us).
  - Phases 2-4 held at 13.5 ns (the deferred regime): 3.8 V. Held at 11 ns: no growth past the 3.0 V it starts with.
  - The longer the clamp, the higher rail 1.
- **D63 misses the first 15 us.**
  - From 98 to 110 us, D63 balances the ladder within 1 V.
  - In cosim, rail 1 of the fixed arm takes the whole Vin ramp: 11.8 -> 15.5 V. Rails 2-4 stay at 7-8 V.
  - In the same window the cosim's Ton differs between the arms: 21-26 ns fixed against 32-35 ns learner. The
    ladder's restoring force grows with Ton squared.
  - The gap involves the driver's lead ramp (0 -> 9.5 ns over 20 us), the interlock's deferral, and the voltage loop.
    None of these is in D63.
- **The learner's delays overcorrect in D63.** Rail 1 goes to 10.3 V at 140 us (deviation 1.65 V). The record has
  0.29 V there, though it too swings to 1.0 V at 150 us.
- **An event turn-on (V_DS comparator, clamp bounded to 1-2 ns) does not settle the ladder in D63.**
  - evt2: 1.52 V at 140 us but 2.0 V at 299 us.
  - evt1: 2.6 V at 140 us.
  - Not monotonic in the clamp. A comparator-triggered turn-on is not a ladder fix on this evidence.
- clamp_q (the clamp's reverse charge in the ladder) lowers the deviation slightly: 4.1 against 4.6 V. I had predicted
  the opposite.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| k1 | rec_s: peak within +-40 % of 6.4 V, within 15 us of 137 us, >= 3 V at 140 us | pass: 4.08 V at 137 us, 3.63 V at 140 us |
| k2 | rec_l: <= 1.5 V at 140 us | **miss**: 1.65 V (rail 1 low, 10.3 V) |
| k3 | evt1 or evt2: <= 1.5 V at 140 us, peak <= rec_l's | **miss**: evt2 1.52 V; evt1 2.60 V |

## 2. Literature (abstracts, except [2] and the patent; agent survey 2026-10-26)
- Per-phase rail x duty = Vo in a two-phase SCB:
  - Rmila, IntechOpen 2022, DOI 10.5772/intechopen.107975 (48 -> 5 V, GaN, 250 kHz).
  - Unequal on-times give a stable dc offset: Shenoy et al., ECCE 2015, DOI 10.1109/ECCE.2015.7309943.
- Timing mismatch unbalances flying / series capacitors:
  - Ye, Lei, Liao, Pilawa-Podgurski, TPEL 2022, DOI 10.1109/TPEL.2021.3119409 (gate-delay mismatch, FCML);
  - Rmila and Chen, e-Prime 2022, DOI 10.1016/j.prime.2022.100075 (dead-time mismatch, GaN SCB).
- Dead time as a balancing actuator, through body-diode conduction: only a patent (Delta, US12368390B2, 3-level
  flying-capacitor converter). No peer-reviewed source found.
- Start-up: published SCB practice pre-charges the capacitors and then soft-starts, with a window check:
  - Roberts, McRae, Prodic, EPE 2019, DOI 10.23919/EPE.2019.8915225 (4-phase SCB, 48 -> 1-1.8 V);
  - TI TPS54A20.

  No source balances an SCB ladder actively while Vin ramps.

## 3. Next
- Keep the learner for the start-up, where it is validated (A245 / A246), and hold its value afterwards (A251:
  dt_hold_periods). The start-up's own path stays the learner until a pre-charge or a balance loop is designed in
  cosim.
