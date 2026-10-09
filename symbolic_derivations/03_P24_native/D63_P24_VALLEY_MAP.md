# D63 - the cycle-by-cycle valley map

2026-10-03, extended 2026-10-06 (Sections 9-10: the blocks added after A118, accuracy at 2.5 MHz, later limits).
Code: `src/scb_ivr/p24_valley_map.py`. Validation and design map:
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
   ≤ 4.7 A (≤ 5.5 A, 4.8 A from 2 µs, with D57's threshold below 8 V instead of the table's
   8 V end value; D81 Section 2).
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

(As of A118; the limits found later are in Section 10.)

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
- At 3 µF, a +4.8 V / 5 µs step runs away with the comparator, as the
  map diverges.
- The falling 1 µs step, where it also diverges, does not run away
  (208 A).

**Not explained:** the 3 µF handover's ~1.1 ms oscillation to 517 A.
- `handover()` from the true state (the ladder near balance, Vo
  1.070 V) gives 149 A.
- The co-simulation's section samples put C1 ~1 V low at 3 µF: its
  in-cycle low, as in steady state. They are not the ladder's mean and
  must not be fed to the map.
- The in-cycle ripple, not in the map, is the likely cause.
- The comparator's rising-step failure at 15 µF does not end with
  slower slews (225 A at 50 µs).

**Not modelled, now measured:** the in-cycle Cs ripple at 3 µF shifts
the turn-ons (phases 1/4 +1.1 V, phases 2/3 −0.8 V) at no efficiency
cost.

## 8. Tested by A118 (the floor, an RTL option; 13 step rows registered from D63)

- **The floor behaves as the map's "floor" mode:**
  - phase 1 held at −14.5 to −14.7 A;
  - the load decrease recovers: +25.6 / +26.4 mV against +27.2;
  - the controls without it cross as the map says (t6 −62.5 A runs away).
- **Peaks within 10% in 6 of 7 bounded rows** (f15 −4.8 V / 5 µs: 211
  against 187 A).
- **The rising rows flagged weak were close at 6 µF** (206 / 208, 193 /
  191, 183 / 169 A), but 18% under at 15 µF (241 / 204).
- **The map's recovery times run short with the floor** (17.6 against
  31.8-46.8 µs).

## 9. 2.5 MHz and the blocks added after A118 (A124-A150)

Every block is off by default; the earlier results are unchanged.

| block | what it adds | for | against the co-simulation |
|---|---|---|---|
| `ton_cap` (`a134_predict.Law`) | scb_vff's absolute phase-1 cap k / rail | A134 | reproduces the L+ lock: s_p62 locked from L × 1.05 (cosim: cap-bound at 1.05, locked at 1.1) |
| RTL-exact feed-forward (`a135_predict.VffRTL`, A136's low-pass cap, A140's slope gate; in the experiment folders, passed as `rule` / `ton_cap`) | the adopted vff | A135-A140 | A138 / A139's prior, A143's cheap check |
| `Design.von` (`von_table`) | each phase's turn-on V_DS: D57's free node at t_tr | A148 | phase 1 p90 0.01 V (hard turn-ons 0.42 V) over 193 k turn-ons; phases 2-4 read 0.46 V low |
| `floor_keeps_dlo` | a floor turn-off keeps dlo, as scb_phase does | A148 | found mid-run (the map rewrote dlo) |
| `lo_add` | an offset on phase 1's timed edge (the volt-second law) | A148 | |
| `Design.sh` | SH_k peak = rail_(k−1) + rail_k + f(turn-on V_DS of phase k−1), f per (L, turn-off di/dt) from A144 / A145 | A149 | held out: rising rows +0.15..+0.68 V, falling −0.56..−1.21 V; 1.7-1.9 V conservative on A149's post hoc runs |

**Accuracy at 2.5 MHz and over the registered rows:**
- **A124:** load step +16.8 / −10.1 mV against +15.9 / −12.0 mV; the refitted crossing rule held prospectively
  (t125_s_m62 recovers).
- **A125 (43 registered rows, A117-A124):** the co-simulated peak is −1.3 % to +18.4 % of D63. The map
  under-predicts, so the conformal band is asymmetric.
- **A138 / A139 (the 200 A line-step boundary over L / Cs × 0.7-1.3):** cosim − D63 mean −0.9 A, sd 5.7 A
  (A138). Classification rising 0.85 / falling 0.55 against the GP's 0.90 / 0.90; MAE 4.2 / 15.8 A. The falling
  residual (+7.8 ± 19.6 A) is tied to L.
- **A149:** peaks L0 199 / 196 against 196.5 / 193.1 A; L × 1.3 205.7 against 200.8 A; L × 0.7 202 against
  202 / 199 A.

## 10. Limits found after A118

- **No dt_pred block** (A143). Phases 2-4 learn their turn-on delay from the error; after a stretched period it
  falls from 11 to 2-4 ns and the phases swing with Cs (~4.6 µs). The map, with a fixed t_tr, stays damped:
  196 A on +4.8 V / 5 µs where A149's laws gave 325 / 223 A, and it missed A142's comparator-phase oscillation.
- **Period-stretching laws** (A148-A150): Vo excursions 2-3× too small; the shape (dip, stretch-end rebound) is
  right.
- **Falling line steps** are its weakest class (classification 0.55, A139).
- **No RTL arbitration:** duplicate turn-ons and floor-first races (A140-A142, C13) need the event logs and the
  oracles.
- **No start-up:** mode S and the handover are not in the map; A152's start-up Ton came from short
  co-simulations (D68 derives it).
- **Package:** the SH block knows 72 A/ns turn-on edges only; the slow turn-on (A151) is D68's.
- Vo extreme sign flips on 9 of 43 rows (A125); recovery time good to about ×3.

## 11. Validity checks (D81, 2026-10-09, after an external review)

The map now says when it leaves its tables or a formula's range; numbers inside the range are unchanged (the archived
D63 / A117 / A118 / A124 / A134 / A135 outputs are reproduced value for value, apart from runs that had already
diverged).
- **Records:** `rec["flags"]`: `ith_rail` (a rail outside the I_th table, 8-17 V by default; the end value is used),
  `past_level` (phase 1 at or below its turn-off level when its high side ends: the comparator fires at once),
  `von_grid` / `sh_grid` (A148 / A149 tables). `metrics()` counts them after the step (`flag_periods`).
- **seg_time** returns `inf` for a level the current never reaches (it returned a negative time when the level was
  behind); r = 0 uses the ramp limit (it divided by zero).
- **steady_ton** refuses an interval without a root and checks the residual; **simulate** checks the warm-up end
  state (`steady_check`: periodic within a lag of 16 periods, Vo to 10 µV, valleys to 1 mA, Ton codes equal) and
  reports it in the first record and as `metrics()["warm_settled"]`. Scripts with their own warm-up loop
  (A134 / A135 / A138 / A140 / A148, ml_rl*) can call steady_check; they do not yet.
- What the checks found in the archived runs is in D81 Section 2.
