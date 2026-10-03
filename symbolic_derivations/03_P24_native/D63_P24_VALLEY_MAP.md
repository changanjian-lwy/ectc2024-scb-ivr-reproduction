# D63 - the cycle-by-cycle valley map

2026-10-03. Code: `src/scb_ivr/p24_valley_map.py`. Validation and design map:
`scripts/p24_valley_map.py` → `diagnostics/D63_valley_map.json`. Tests:
`tests/test_p24_valley_map.py`.

## 1. Why

The trade-off map (`reports/TRADEOFF_SCORECARD.md` Section 4) closes on
the valley margin, I_th − i_neg. One link was not quantified: how far a
transient moves the valleys.
- **D60** keeps every valley at the target (boundary conduction), so it
  cannot see the excursion.
- **D59** has no valleys at all.

D63 keeps them as states.

## 2. The map (one step = one phase-1 period)

1. **Loop:** D59's PI on Ton, sampled at phase 1's turn-on.
   - Ton is quantised to the LSB and clamped to 0.5-2 × the mode-S value.
   - Every phase on in the period uses the new value, phase 1 included:
     `scb_phase` compares the turn-off with the live `ton`.
2. **Rails from the ladder:** V_rail,1 = Vin − V_1, V_rail,k = V_(k−1) − V_k,
   V_rail,4 = V_3.
3. **Each phase starts its high side from its previous valley v:**
   - **−v ≤ I_th(rail):** at ~0 A (the valley turn-on).
   - **v ≥ 0:** the node falls, and the low side's reverse conduction
     ramps the current down at (Vo + v_rev)/L until the predictive turn-on
     at t_tr. It starts at max(0, v − (Vo + v_rev) t_tr / L).
   - **−v > I_th (a crossing, depth −v − I_th):**
     - the node reaches the rail at t_reach = (2 t_tr/π) asin(I_th/−v),
       with −√(v² − I_th²) left;
     - the high side's reverse conduction then ramps the current up at
       (V_rail + v_rev − Vo)/L until t_tr;
     - so it starts at min(0, that). **This is the memory.** It carries a
       crossing into the next period only when the crossing is deep: at
       1 MHz (t_tr 16.9 ns), from ~−23 A on phase 4.
4. **Rise and fall:** linear-R segments.
5. **Phase 1's turn-off:**
   - **comparator (I1):** at the target, capped by the restart timer;
   - **timed (I2):** after dlo, with A100's adaptive crossing-report
     step;
   - **floor:** a proposal, Section 5.
6. **Phases 2-4 turn off on their slots,** t_lo1 + (k − 1) T_avg/4. T_avg is
   the mean of phase 1's last two periods; this rule was read back from
   the co-simulation (A116 c60_s_p62: the spacing × 4 equals that mean to
   0.1 ns).
7. **Co with the resistive load:** an exact RC step.
8. **The ladder:** Cs dV_k = Q_on,k − Q_on,k+1 per period.
9. **The input:** a linear ramp.

**Inputs:**
- I_th(rail): D57 on a 0.5 V grid, cached in the diagnostics file;
- t_tr: D57's valley time at the design point (phase 1's and phase 4's
  nodes);
- v_rev = 2.0 V: the plant's clamp is −2.1 to −2.2 V at turn-on, and
  fit_fig8 gives 2.09 V + 6 mΩ per device.

## 3. Validation (25 co-simulated transients)

| class | result |
|---|---|
| steady orbit | Ton 93.78 against 93.80 ns, period 1194.8 against 1195.1 ns (A115) |
| comparator load steps (5 cases) | extreme within 10%, back within 1 µs (e.g. c60 −62.5 A: +28.9 against +28.0 mV, 16.5 against 16.1 µs; c30 +62.5 A: −50.2 against −48.2 mV) |
| timed +62.5 A (4 cases) | extreme 20-30% small (1 MHz: −15.9 against −19.9 mV) |
| line-step peaks (6 cases) | 1% (5 MHz 5% timed: 209 / 207 A; 5 MHz 25% comparator: 287 / 287; 1 MHz t30: 231 / 233), 5% (5 MHz 20% timed: 209 / 199; c60 −4.8 V: 216 / 206), 9% (c60 +4.8 V: 372 / 341) |
| line-step Vo | mixed: c60 −4.8 V +169 against +94 mV |

**Every slow or runaway outcome shows a phase-1 crossing** (depth × periods):

| case | phase 1 crossing in the map | co-simulation |
|---|---|---|
| 1 MHz 10% timed 60 kHz −62.5 A | 19.2 A × 44 (51 µs) | runaway |
| 1 MHz 10% timed 30 kHz −62.5 A | 17.3 A × 44 | 200 µs oscillation |
| 1 MHz 5% timed −62.5 A | 8.6 A × 27 (31 µs) | slow, 45 µs |
| 5 MHz 25% timed −62.5 A | 13.5 A × 46 (14 µs) | slow, 183 µs |
| 5 MHz 25% timed −4.8 V / 1 µs | 119 A × 1313 | slow, 182 µs |
| 1 MHz 10% timed 60 kHz −4.8 V / 1 µs | 105 A × 13 (16 µs) | runaway |
| 5 MHz 5% timed −4.8 V / 1 µs | 37 A × 13 (**3 µs**) | ok |

**No case without a phase-1 crossing was slow, with one exception
below.**

**Empirical rule (7 cases):** a phase-1 crossing deeper than ~8 A that
lasts longer than ~5 µs gives a slow recovery or a runaway.
- Phase 1 is the timing reference: its period sets every slot.
- Crossings in the slotted phases alone, even deep ones, did not break
  the timing (c60 +4.8 V: 148 A; it fails on peak current only).

**Not reproduced (the map's limit):** the timed design at 60 kHz runs
away on +4.8 V / 1 µs (A116 t60: 546 A).
- **The map shows** phase 1's valley positive, slots crossing 39 A, a
  213 A peak, and no phase-1 crossing.
- **Likely cause:** the controller's learning loops (dt_pred from flat
  valleys, early reports), which the map does not have.
- **So for the timed design with the 60 kHz loop, a "safe" rising-step
  prediction needs the co-simulation.** At 30 kHz the same step is
  reproduced (231 / 233 A).

## 4. The design map at 1 MHz 10% (60 kHz loop; the diagnostics file has every row)

**Peak current (A) and phase-1 crossing for ±4.8 V over the slew shown:**

| Cs, rule | 1 µs | 5 µs | 10 µs | 20 µs | 50 µs | ±62.5 A |
|---|---|---|---|---|---|---|
| 15 µF comparator | 372 / 216 | 364 / 194 | 332 / 163 | 286 / 149 | 208 / 140 | ok / ok |
| 15 µF timed | 213 / 212, phase 1 −105 A | 204 / 205, −94 A | 196 / 189, −68 A | 191 / 166, −32 A | 180 / 145, −9.5 A | phase 1 −19 A / ok |
| 15 µF floor 2 A | 213 / 210 | 204 / 187 | 196 / 161 | 191 / 151 | 180 / 141 | ok / ok |
| 3 µF comparator | **diverges** | diverges / 181 | 217 / 146 | 175 / 140 | 154 / 140 | ok / ok |
| 3 µF timed | 202 / 180, −75 A | 181 / 169, −50 A | 165 / 154, −24 A | 160 / 146, −10 A | 154 / 142 | phase 1 −19 A / ok |
| **3 µF floor 2 A** | 202 / 200 | **181 / 163** | 165 / 143 | 160 / 141 | 154 / 141 | **ok / ok** |

**What the map says:**
1. **At Cs 15 µF no rule meets 200 A for a 1 µs step.**
   - **The comparator fails rising steps at every slew up to 50 µs:**
     phase 1 stretches, and the slots follow with unchanged rails.
   - **The timed rule fails falling steps and load decreases:** phase 1
     crosses.
2. **A smaller Cs (3 µF) speeds the ladder 5× and helps every rule but
   the comparator.**
   - With the comparator the map diverges on fast rising steps: the
     faster ladder and the slots' memory couple. **This needs the
     co-simulation.**
3. **The floor** (Section 5) **with 3 µF meets every row from 2 µs**
   (197 / 189 A) and both load steps, with phase 1's crossing held to
   ≤ 4.7 A.
4. **Cs is a new trade:** 3 µF costs ~1 V of high-side turn-on in steady
   state (A107's 0.6 µF at 5 MHz had the same Q/Cs). D63 does not model
   the in-cycle ripple, so that cost comes from A107.

## 5. A proposal the map found: the timed turn-off with a comparator floor

**The rule:** phase 1's low side turns off at the earlier of
- the timed edge (dlo), and
- the current reaching i_tgt − floor.

**Why it works:**
- In steady state and on rising steps the timed edge comes first. The
  timed design's low jitter and its rising-step robustness stay.
- On falling steps and load decreases the floor comes first, so phase
  1's valley cannot cross. This is the comparator's strength there.
- It resolves T13's mirror failure in the map.

**What it needs:**
- an RTL option (arm the front end in timed mode, at the floor
  threshold);
- the co-simulation to check the timed design's 60 kHz rising-step
  runaway, which the map does not reproduce.

## 6. Limits

- No controller learning beyond dlo: dt_pred, error correctors, early
  reports, the trim.
- No comparator or driver delay; no in-cycle Cs ripple.
- The node at the turn-on is D57's free swing. Coss hysteresis and
  ringing are not modelled.
- Breakdown after a crossing is not modelled. The map reports the
  trigger (depth, duration) and stays physical only while the memory is
  bounded; it stops at 1000 A.

## 7. Tested by A117 (14 co-simulations, registered before the runs)

**Peaks hold:** within 10% in all 5 bounded rows (286 / 286, 225 / 208,
201 / 194, 174 / 175, 143 / 140 A).

**The outcome rule of Section 3, as registered, is falsified.** 6 of the
10 reliable rows miss.
- **Three sit on the class edges:** 61.6 µs against 60; 201 A against
  200.
- **Three are real:** the 8 A threshold is too low (9.5 A × 50 and
  23.5 A × 12 did no harm), and the 3 µF comparator's falling 1 µs step
  does not diverge (208 A, 32 µs).

**Refit on all 10 phase-1 crossings co-simulated:** "deeper than ~12 A
for ~25 periods or more" separates the slow and runaway outcomes from
the others. The exception is the timed 60 kHz design on 1 µs steps.
**It is fitted after the runs; the next test must register it.**

**Confirmed:**
- Cs 3 µF couples the faster ladder with the loop in large fast
  transients. The handover oscillates for ~1.1 ms to 517 A, and a
  +4.8 V / 5 µs step runs away with the comparator.
- The comparator's rising-step failure at 15 µF does not end with
  slower slews (225 A at 50 µs).

**Not modelled, now measured:** the in-cycle Cs ripple at 3 µF shifts
the turn-ons (phases 1/4 +1.1 V, phases 2/3 −0.8 V) at no efficiency
cost.
