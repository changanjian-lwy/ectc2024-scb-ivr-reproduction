# Trade-off scorecard - the P24 module's controller, A92 to A100

2026-10-01. **One table for every design on the adopted line, with the same
metrics.** The purpose is to tell real improvements from moves along a
trade-off curve, and to stop the project from cycling between them. Every
future design change is scored on this table (Section 5).

**Conditions for every number:**
- P24 single module, 4 phases, Verilog RTL co-simulated with A88's plant:
  datasheet Coss(V), reverse drop, 25 C;
- ZVS target -6.25 A (the "5%" case), resistive load of about 250 A;
- statistics over the last 200 cycles.

**Sources:**
- each experiment's RESULTS;
- `experiments/track_A_periodic_steady_state/A98_jitter_amplification/a98_summary.json`,
  `A99_.../a99_summary.json`, `A100_.../a100_summary.json`;
- the mathematical models D52-D55.

## 0. Correction (2026-10-01): the largest switching loss was missing

**The high side does not turn on at zero voltage in any design here.** It
turns on at the resonance valley.
- High-side V_DS at turn-on is about 9 V of the ~12 V it blocks. The low
  side does turn on at zero voltage (−0.01 V).
- The orbit's turn-on V_DS against the negative-current target (D47):

  | target | high-side turn-on V_DS |
  |---|---:|
  | 2% | 9.9 V |
  | 3% | 9.7 V |
  | **5% (used)** | **9.0 V** |
  | 7.5% | 8.0 V |

- The co-simulation agrees: 8.9-9.0 V.

**The scorecard's "hard-on loss (A91's estimate)" row counts only early
low-side turn-ons.** It is renamed below.

**The high-side valley turn-on loss** is estimated with A91's method from
the datasheet Coss: a lower bound Eoss(V) of the 2 high-side devices, an
upper bound Qoss(V)·V of the 5 devices on the node.

| target | 2% | 3% | **5%** | 7.5% |
|---|---|---|---|---|
| loss, all phases | 3.9-20 W | 3.7-19 W | **3.1-16 W** | 2.4-12 W |

At 5% that is 1-6% of the ~250 W output. **It is 30-100 times larger than
every loss the A92-A100 changes moved** (P_rev ≤ 0.17 W, early low-side
turn-ons ≤ 0.1 W). It is the same in every design on this table, because
none of them changes the orbit's turn-on voltage.

**Why (estimate, not yet a computed orbit).**
- The node carries 5 EPC2067 (about 2 nF each at 9 V, about 10 nF in
  total) against L = 1.47 nH, so Z ≈ 0.38 Ω.
- A full 12 V swing would need roughly 30 A of negative current, about
  25% of the peak.
- Extrapolating the 2-7.5% trend gives the same order.
- P24 states that 1-2% is enough. That discrepancy is the most important
  open question for Mihai: the snubber or node capacitance, and the
  devices on the node.

**Consequence for priorities.** The jitter and tracking work (A98-A100)
moves second-order losses. The first-order item is the high-side turn-on:
- the trade-off between the negative-current target (conduction loss of
  the circulating current) and the turn-on voltage;
- and the paper's ZVS claim.

## 1. The designs

| design | what it changed | status |
|---|---|---|
| **A92** | error-based correctors (94 ps targets, gain 1/2), fixed slots | was adopted |
| **A93** | slots follow the last period (T/nP) | not adopted |
| **A97** | slots from the two-period average, with the missed-slot guard | **adopted (current preset)** |
| A98 g4 | A97 with corrector gain 1/4 | not adopted |
| A99 | A97 with phase 1's turn-off timed, dlo ±1 LSB | not adopted |
| **A100** | A99 with an adaptive dlo step (cap 32 LSB) | **recommended, pending this review** |

## 2. The scorecard

**Hard constraints:** no cross-conduction, peaks ≤ 200 A. **Every design
listed meets them in every run made.**

| metric | A92 | A93 | **A97** | A98 g4 | A99 | **A100** |
|---|---|---|---|---|---|---|
| **start-up:** peak current at m = -3.4 ns (handover) | **827 A** | 172 A | 156 A | - | 156 A¹ | 156 A¹ |
| **steady state:** windowed dither, no jitter | 0.49 A | 1.31 A | 0.57 A | - | **0.04 A** | **0.04 A**² |
| turn-off current spread, phases 2-4, no jitter | 0.16-0.17 A | 0.28-0.55 A | 0.18-0.21 A | - | **0.018 A** | **0.021 A**² |
| **30 ps jitter:** spread, phases 2-4 | 0.52-0.61 A | 0.71-0.98 A | 0.56-0.66 A | 0.56-0.62 A | **0.39-0.42 A** | 0.42-0.47 A |
| 30 ps: period spread | 0.60 ns | 0.57 ns | 0.59 ns | 0.59 ns | **0.19 ns** | 0.37 ns |
| 30 ps: high-side turn-ons before the valley, phases 2-4 | 21-27% | 29-37% | 22-26% | **12-16%** | 16-18% | 17-18% |
| **100 ps jitter:** spread, phases 2-4 | 1.39-1.61 A | 1.95-2.69 A | 1.59-1.79 A | 1.65-1.88 A | **1.02-1.16 A** | 1.03-1.20 A |
| 100 ps: reverse-conduction loss P_rev | 91 mW | 89 mW | 89 mW | **172 mW** | 74 mW | 74 mW |
| 100 ps: early low-side turn-on loss (A91's estimate; low side only) | 31-102 mW | 30-102 mW | 31-102 mW | **12-39 mW** | 30-99 mW | 30-99 mW |
| **high-side valley turn-on loss** (turn-on at about 9 V; Section 0) | 3.1-16 W | 3.1-16 W | 3.1-16 W | 3.1-16 W | 3.1-16 W | 3.1-16 W |
| **phase 1's own turn-off current spread** (its ZVS margin), 30 / 100 ps | **0.17 / 0.19 A** | 0.17 / 0.19 A | 0.17 / 0.19 A | 0.17 / 0.19 A | 0.39 / 1.13 A | 0.43 / 1.16 A |
| **load steps ±25 A / ±62.5 A:** phase 1's largest turn-off current deviation | (comparator: 0.37 A, the trim) | - | 0.37 A | - | **19-23 A** (±62.5 A) | 0.6-0.7 / 1.4-1.7 A |
| load steps: Vo excursion ±25 A / ±62.5 A | - | - | 50 / 122-127 mV | - | 83-103 mV³ | 49-50 / 120-126 mV |
| **driver mismatch m = ±1, +3.4 ns** | tolerated | tolerated | tolerated | - | not tested | not tested |
| **RTL size** (cells) | 38 456 | 39 571 | 40 296 | 40 296 | 41 605 | 43 924 |

**Notes:**
1. Bit-identical to A97 before phase 1's switch to timed mode (A99's
   gate); the handover is still comparator-decided.
2. From the 300-400 us interval of A100's step runs, before the step and
   without jitter.
3. Smaller only because phase 1 runs far from its operating point (turn-off
   current +16.9 / -24.9 A).

"-": not run for that design.

## 3. Real improvements and trades

**The frequency-resolved jitter response** shows the difference (D53/D54,
average-slot orbit, phase 4's turn-off current per unit edge jitter, ratio
to A97):

| ω/π | 0.12 | 0.25 | 0.33 | 0.5 | 0.67 | 0.75 | 1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A92 fixed slots | 0.93 | 0.82 | 0.76 | **0.71** | 0.76 | 0.82 | 1.00 |
| A93 follow slots | 0.98 | 0.96 | 0.97 | 1.07 | 1.29 | 1.45 | **1.93** |
| A99 timed phase 1 | 0.74 | 0.63 | 0.58 | **0.54** | 0.57 | 0.61 | 0.74 |

**A move along the curve** shifts gain between frequency bands or between
metrics:
- A92 → A93 → A97, the slot rule. Bode's sensitivity integral (the
  "waterbed") limits loop shaping.

**A structural change lowers the whole curve:**
- A99's timed turn-off is lower at every frequency. It removes a source of
  amplification (phase 1's comparator, ×10.5) rather than reshaping a loop.
- Its costs then appear in other metrics.

## 4. The trade-offs found, and where a loop could form

| # | trade-off | evidence | resolution so far | loop risk |
|---|---|---|---|---|
| T1 | **Start-up starvation ↔ mid-band jitter** (slot rule) | A92 starves at m3n (827 A); A93 fixes it but raises the two-cycle dither (×1.93); A97 removes that peak but stays 1.2-1.4× above A92 at mid frequencies | A97: the start-up won | **High.** Going back to fixed slots for jitter brings the starvation back. Lower jitter has to come from elsewhere: A99/A100. |
| T2 | **Turn-ons before the valley ↔ reverse conduction** (corrector gain) | A98: gain 1/4 halves early turn-ons; P_rev 89 → 172 mW at 100 ps, hard-on saved 19-63 mW | rejected on loss | Medium. Early turn-ons are not a loss by themselves: score losses, not proxies. |
| T3 | **Early-step size ↔ protection** | D53: a smaller early step makes early turn-ons more frequent (25 → 32-36%) | kept at 0.2 ns | Low. |
| T4 | **Period jitter of phases 2-4 ↔ phase 1's turn-off current** (comparator vs timed turn-off) | A99/A100: phases 2-4 −24 to −38%, period −37 to −82%; phase 1's spread 0.17 → 0.4-1.2 A | structural; the cost is moved onto phase 1's ZVS margin | Medium. If phase 1's ZVS margin becomes the binding constraint, the next fix would push the jitter back. **Phase 1's margin needs a hard limit before adoption.** |
| T5 | **Load-step tracking ↔ jitter** (dlo rule) | D55/A100: ±1 → ADM32 costs +7-13% spread at 30 ps, buys tracking (19-23 A → 1.4-1.7 A) | ADM32 | **High, and coupled to T6.** |
| T6 | **Voltage-loop speed ↔ the dlo rule's tracking burden** (not yet tested) | The required dlo moves 10× faster than Ton. A faster voltage loop (Vo now moves ±12% for ±25% steps) would make Ton, and so dlo, move faster. | open | **The most likely next loop:** a faster voltage loop → a larger dlo step → more jitter → ... It should be designed together with dlo, on this table. |
| **T8** | **High-side turn-on voltage ↔ circulating current** (the negative-current target) | D47: 2% → 9.9 V, 7.5% → 8.0 V. ZVS would need about 25% (estimate). | **not yet studied; the largest loss term** | Not a loop yet. It is the first-order trade-off and must be mapped (loss against target) before further second-order work. |
| T7 | **Prediction ↔ reaction** (a recurring pattern: A89 low-side turn-on, A92 correctors, A99/A100 turn-off) | Each predicted edge removes a comparator's noise but needs learning and tracking, and moves the error elsewhere | design by design | Structural: each step is a new trade-off, not a reversal. |

## 5. How every change is scored from now on

1. **The standard matrix**, the same for every candidate:
   - n0 (0 ps);
   - m3n (start-up), m ±1 ns, m3p;
   - j30, j100;
   - load steps ±25 A and ±62.5 A.
   Every row of Section 2 is measured; "-" is not allowed for a candidate.
2. **Hard constraints** (pass/fail):
   - no cross-conduction;
   - peaks ≤ 200 A;
   - phase 1's turn-off current within a limit to be set (Section 6).
3. **Objectives** are scored with explicit weights (Section 6). A candidate
   is adopted only if it meets the constraints and improves the weighted
   score, or is Pareto-better.
4. **The mathematical model maps the trade-off curve before any choice.**
   - Frequency response for loop-shaping changes;
   - tracking against noise for adaptive rules.
   - One point is chosen, with the weights, instead of correcting one
     metric at a time.

## 6. Decisions needed (priorities)

These are design priorities, for the user and Mihai:
- **Phase 1's ZVS margin.** What is the acceptable range of its turn-off
  current? At 100 ps, A100 goes from -8.7 to -3.3 A; the comparator design
  stays at -6.7 to -5.8 A.
- **Jitter against tracking.** How much spread at 30 ps is acceptable for
  how fast a load step?
- **The voltage loop.** Is ±12% on a ±25% step acceptable? If not, T6
  makes it the next item, designed together with dlo.
- **The complexity budget.** A100 is +9% cells over A97.

## 7. Not yet known

- **For the timed designs (A99/A100):** m ≠ 0, other loads and ZVS
  targets, temperature, line steps.
- **The learning length:** 1024 cycles, chosen for this start-up.
- **Losses:** only P_rev and A91's hard-on estimate are scored. Gate
  charge, conduction and overlap losses are not modelled yet.
