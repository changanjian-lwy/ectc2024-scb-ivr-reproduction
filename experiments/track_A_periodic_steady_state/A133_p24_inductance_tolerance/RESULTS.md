# A133 - L tolerance and floors on phases 2-4 (RESULTS)
Boundary: 6cb668d. Records: cosim/run_*.json (96), identity reruns in tmp/identity_a133/; a133_summary.json.

## 0. Verdict
- **C06's floor on phases 2-4 is invalid in the SCB ladder - not adopted.** A floor makes a phase's turn-on follow its
  own current instead of the slot order. Phase k's high side then turns on while phase k-1's is still on, and the
  two rails add up. Nominal, +4.8 V / 5 us: phase 4 turns on at 109.518 us inside phase 3's high interval
  (109.515-109.546 us), at V_DS 23.2 V and +8.9 A, and reaches 368 A. Floors fire 1543 times after that step.
- Off, the floors change nothing (identity bit for bit). On, the nominal steady state is unchanged (no fire after
  600 us), but they fire at the handover (145 us): run peaks 242-273 A (163 A without them), and the matrix is 0/8.
- They do not remove the L +30 % limit cycle either. pl13_n0 ends unbalanced (valleys -13 / -9.5 / -8.5 A, Vo pp 27 mV,
  859 / 340 / 257 fires).
- **L tolerance of the adopted design (no floors), the useful result:** L x 0.7 is balanced; the +4.8 V rows reach
  206 / 201 A (phase 1, recovered in 14-18 us). L x 1.1: n0 pilot only, balanced. **L x 1.2 is bistable:** it is
  balanced after start-up (rail 1 swings to 16.5 V and returns), but the +62 A load step (s_p62) throws it into the
  ladder limit cycle (212 A, Vo -95 mV, no recovery by the end). L x 1.3 is in the limit cycle from start-up (rails
  13.7 / 11.5 / 11.4 / 11.4 V, peaks 199-228 A). So the design holds L only within about -30 % / +10 %.
- The limit cycle is co-simulation-only: D63 from the balanced state stays balanced at L x 1.2-1.3. It is not the
  loop's start value: the pilot started at Ton x 1.3 and gave the same cycle.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | identity (off) | pass: g125_n0, g125_l_p48_1us bit-identical |
| 2 | nominal steady state | pass: tail equal, no fire after 600 us (start-up fires 0 / 151 / 20 / 30) |
| 3 | nominal disturbances | **fail**: step peaks 368 / 337 / 170 / 173 / 169 / 178 / 214 A (A129 175-182, 144 A); matrix 0/8 (run peak 240-286 A from the handover) |
| 4 | L x 1.3 balanced | **fail**: limit cycle persists (see Verdict) |
| 5 | l07 / l12 / c07l13 balanced | **fail**: l07, l12 balanced; c07l13 not (Vo pp 27 mV, V_DS < 0) |
| 6 | corners l07 / l12 / l13 | **fail**: no overlap; matrix 0/8 at each; s_p62 runaway at l12 (437 A) and l13 (380 A) |
| 7 | c07l13 step rows | **fail**: peaks 205-464 A |
Predictions: the floored peaks (174-187 A) assumed silent floors; they were not, so they were not tested.

## 2. Limits
- The diagnosis rests on one traced event (phase 4 inside phase 3's high interval, rails added). Other large peaks
  are attributed to the same cause by their timing (floor-driven turn-ons), not traced one by one.
- L x 1.1 has the n0 pilot only. The upper bound of +10 % is not yet checked against the step rows and the matrix.
- One module; the same L spread on the four-module design (C05/C06) has not been run.
