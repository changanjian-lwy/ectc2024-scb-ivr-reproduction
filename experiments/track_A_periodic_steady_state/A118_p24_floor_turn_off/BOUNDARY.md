# A118 - the timed phase-1 turn-off with a comparator floor (BOUNDARY)

Track A, main line. **Written before any A118 run.**

**The design:** A115's 1 MHz 10% design (`cfg_n10`): timed phase-1
turn-off, D59 loop at 60 kHz, Eq. (4)'s 7.333 nH.

**One factor:** the floor (cfg `lo_floor` 1, `lo_floor_a` 2 A; RTL
option of this commit, `src/scb_ivr/cosim/CHANGELOG.md`).
- Phase 1's low side turns off at the earlier of the timed edge and its
  current reaching i_target − 2 A (−14.5 A).
- **Origin:** D63's proposal; A120's surrogate search put it, with Cs
  ≲ 8 µF, in most of the feasible region once the bus slew is ≥ 5 µs.

**Second factor:** Cs, 6 µF (A120's band) and 15 µF (A115's). Controls
without the floor at 6 µF.

**Rows** (`make_cfgs.py`, 14):

| group | rows |
|---|---|
| f6 (floor, 6 µF) | n0 (start-up included); ±62.5 A; ±4.8 V over 1, 5 and 20 µs |
| f15 (floor, 15 µF) | −62.5 A; ±4.8 V over 5 µs |
| t6 (timed, no floor, 6 µF) | −62.5 A; −4.8 V over 5 µs |

## 1. Registered predictions (D63, `a118_predict.py` → `a118_predictions.json`)

| row | D63 peak | Vo, back | phase 1's valley min | D63 outcome |
|---|---|---|---|---|
| f6_s_m62 | 140 A | +27.2 mV, 17.6 µs | −14.5 A | ok |
| f6_s_p62 | 173 A | −15.9 mV, 9.8 µs | −12.9 A | ok |
| f6_l_m48_1us | 203 A | +91.0 mV, 65 µs | −14.5 A | peak (marginal) |
| f6_l_m48_5us | 174 A | +66.4 mV, 67 µs | −14.5 A | ok |
| f6_l_m48_20us | 143 A | +17.0 mV, 23 µs | −14.5 A | ok |
| f6_l_p48_1us | 208 A | +20.2 mV, 6.1 µs | −14.4 A | peak (marginal), **D63 weak** |
| f6_l_p48_5us | 191 A | +16.0 mV, 8.5 µs | −14.5 A | ok, **D63 weak** |
| f6_l_p48_20us | 169 A | +4.9 mV, 0 | −14.5 A | ok, **D63 weak** |
| f15_s_m62 | 140 A | +27.2 mV, 17.6 µs | −14.5 A | ok (A115 without the floor: runaway) |
| f15_l_m48_5us | 187 A | +126.6 mV, 75 µs | −14.5 A | ok |
| f15_l_p48_5us | 204 A | +17.4 mV, 8.5 µs | −14.5 A | peak (marginal), **D63 weak** |
| t6_s_m62 | 140 A | - | **−33.8 A** (19.2 A × 44) | slow or runaway |
| t6_l_m48_5us | 186 A | - | **−81.4 A** (69.9 A × 13) | ok by the refitted rule (13 periods) |

**"D63 weak":** on rising steps the floor is not reached. The design is
then the timed 60 kHz design, where D63 missed A116's runaway (D63
Section 3).

**n0 (f6_n0):**
- **Steady state:** the floor never acts, since the valley stays at
  −12.5 A against the floor at −14.5 A. So the steady state is the timed
  design's:
  - turn-off sd ≤ 0.02 A;
  - efficiency within 0.1 points of A115 n10.
  - The high-side turn-ons move with the in-cycle Cs ripple, about half
    of A117's 3 µF shifts (±0.5 V).
- **The start-up at 6 µF is not predicted.** D63 cannot see A117's 3 µF
  handover oscillation. 15 µF had 158 A, 3 µF 517 A. Registered as the
  open question it is.

## 2. Criteria

**Outcome after the step:** peak from the high-side turn-offs after
2000 µs; recovery by `step_stats`.

1. **The floor holds:** in every f row, phase 1's low-side turn-off
   current after the step ≥ −15.5 A (the floor −14.5 A and 1 A for the
   front end's delay).
2. **The load decrease is fixed:** f15_s_m62 and f6_s_m62 recover, with
   the extreme within +27.2 ± 8 mV and back ≤ 30 µs (A115: runaway).
3. **Peaks within ±10% of D63** in the rows not flagged weak.
4. **Hard constraints** in f6's load steps and its ±4.8 V steps over 5
   and 20 µs:
   - no overlap; peak ≤ 200 A;
   - back within 1% ≤ 100 µs;
   - no runaway (late fires ≤ 100, peak ≤ 400 A).
5. **f6_n0:**
   - no overlap; Vo ±1 mV; turn-off sd ≤ 0.02 A;
   - efficiency within 0.1 points of A115 n10;
   - the start-up peak reported against 200 A.
6. **Controls:** t6_s_m62 shows phase 1's valley below −20 A after the
   step (no floor, as A115).

**Decision rule:** if criteria 1, 2 and 4 hold (and 5's start-up ≤ 200 A),
"floor + Cs 6 µF" is the 1 MHz controller candidate, given a bus slew
spec ≥ 5 µs. It then goes to the standard matrix.

## 3. What stays assumed

- A115's design otherwise.
- The floor's 2 A is A120's median, not optimised.
- The front end's delay (t_async 1 ns + t_drv 10 ns) moves the floor
  turn-off ~1.5 A below its threshold at 0.136 A/ns.
