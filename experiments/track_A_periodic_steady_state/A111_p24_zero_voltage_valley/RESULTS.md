# A111 - a zero-voltage valley for the high side's turn-on timing (RESULTS): falsified

Track A. One factor: cfg `valley_zero` = 1 (the high side's measured
valley stops at its first V_DS ≤ 0).

**Boundary:** `BOUNDARY.md`, committed with the code (945e4ac) before
any run.

**Records:**
- `cosim/run_*.json`;
- `a111_summary.json` (`a111_analyze.py`, on A110's statistics).

**Physical model:** as A110 (Verilog RTL, A88 kernel2 plant, A105 I2
with `slot_lo`, 25 C).

## 0. Verdict

1. **The zero-voltage valley does not stabilise 25-30%. It makes them
   worse**, as with A101's branch.

   | run | high-side turn-on, mean (max), phases 1/2/3/4 | turn-off sd | peak | efficiency |
   |---|---|---|---|---|
   | A110 n25 | +0.86 / +0.69 / +0.70 / −0.16 V | ≤ 0.2 A | 204 A | 90.14% |
   | z25 | +2.36 / +0.99 / +1.39 / +3.27 V (to 10.35 V) | 8-17 A | 227 A | 89.73% |
   | A110 n30 | +1.16 / −1.27 / −0.84 / +1.59 V | ≤ 0.2 A* | 236 A | 89.42% |
   | z30 | +1.87 / +0.15 / +0.21 / +2.10 V (to 7.87 V) | 7-16 A | 243 A | 89.37% |

   \* A110 n30's spread grew to 7-20 A with jitter.

   - **The other symptoms at z30:**
     - 39-314 late fires per phase;
     - the low side up to +0.44 V;
     - load steps of −25.7 / −19.5 mV recovering in 27 / 91 µs;
     - 270 A with jitter.
   - **Why:** targeting the node's arrival at the rail turns the high
     side on while a large negative current is still flowing. Small
     timing changes then move the phase's charge, and through the
     series capacitors the other phases'. The slotted phases (and phase
     4 most) lose their timing. That is A101's instability without the
     branch.
2. **The identity checks failed as written, for a reason found:**
   - z5 and z20 diverge from their sources at 72.69 µs, just after the
     handover to mode P. In the first mode-P cycles V_DS does reach zero
     at 5% too, so the measurement differs there.
   - **The steady states agree:**
     - z5 against C02: the high side 8.96 / 8.91 / 8.91 / 9.07 V both,
       efficiency 87.92% both;
     - z20 against A110 n20: within 0.05 V and 0.01 points.
   - **Except z20's run peak:** 199 A against 170 A, after the handover.
3. **`valley_zero` is not adopted.** The default stays 0, and the code
   change is a single opt-in line.

## 1. What A110 and A111 together say about high-side zero voltage

- **Practical zero voltage is reached at 25% with the existing
  controller** (A110 n25).
  - Phase 4 is at −0.16 V and phases 1-3 at ~0.7 V of the 12 V rail.
  - The high side's hard-turn-on loss is 0.04 W against 8.9 W at 5%:
    99.5% of it removed.
  - The steady state is stable (sd ≤ 0.2 A).
  - **Open:** a 204 A peak 5 µs after the handover to mode P.
- **The efficiency optimum is 20%** (90.17%), with the high side at
  2.3-3.0 V: 0.66 W of hard turn-on.
- **Full zero voltage on every phase at 30%** needs a turn-on rule other
  than the valley.
  - The plain valley drifts once the node clamps (A110).
  - The zero-arrival target destabilises the phases (A111).
  - A rule based on the current's zero would be the candidate. It is not
    built.

## 2. Registered criteria (BOUNDARY Section 3)

| # | criterion | result |
|---|---|---|
| 1 | z5, z20 identical to their sources | **miss** (handover transient; steady states agree, 0.2) |
| 2 | z30: HS mean ≤ 0.3 V, max ≤ 1 V; peak ≤ 200 A; LS ≤ 0; sd ≤ 0.5 A; Vo; late ≤ 5 | **miss** in all but Vo and overlap |
| 3 | z30 efficiency ≥ A110 n30, within 0.5 of 89.91%; reverse conduction ≤ 0.5 W | **miss** (89.37%); reverse conduction 0.08 W pass |
| 4 | z25: HS ≤ 0.9 V; peak | **miss** (3.27 V; 227 A) |
| 5 | z30 steps ±25%, back ≤ 15 µs; j30 sd, HS ≤ 0.5 V | **miss** |

## 3. Next

- **The candidate design is A110's 20% or 25%.** They need:
  - the robustness rows (driver mismatch, jitter, load and line steps);
  - for 25%, the handover peak.
- **A112:** both through the standard matrix.
