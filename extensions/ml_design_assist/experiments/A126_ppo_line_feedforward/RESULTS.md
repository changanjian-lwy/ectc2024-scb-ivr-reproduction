# A126 - PPO per-phase Ton feed-forward in D63 (RESULTS)

**Boundary:** f0f8aef.

**Records:**
- `a126_policy_*.npz` (3 sensor sets × 3 seeds, 600 iterations);
- `a126_summary.json` (held-out set and A124's rows);
- `a126_baselines.json`;
- `a126_steady_check.json` (600 periods, no disturbance; post hoc).

## 0. Verdict

1. **The registered criteria pass nominally but the policies are not
   valid. PPO gamed the reward.**
   - The held-out returns look excellent: vin −10.2 / −30.7 / −10.5
     against cap_vin's −103.4.
   - On A124's rising rows, vin s0 reaches 172 / 163 A.
   - **But 7 of 9 policies change the steady state.**
     - Vo oscillates: peak-to-peak 7-16 mV, against 0.01 mV with no
       feed-forward.
     - The ladder sits 1.3-2.7 V off Vin/4.
     - Steady peaks reach up to 187 A.
     - It grows past the 120-period training horizon.
   - **vin s1 converged to a uniform scale of 1.25** on all phases. That
     is a loop-gain change, not a feed-forward.
2. **This is why "rtl" (no Vin sensor) "fixed" the rising step**
   (160-189 A). It runs a different operating point; it does not
   anticipate the step. Criterion 3 misses for that reason.
3. **Cause: a specification error, not a learning error.**
   - The reward priced the transient only. The steady state was free,
     even though the ZVS margin, efficiency and ripple depend on it.
   - The horizon was too short to see slow oscillations.
   - The registered criteria had no steady-state or long-horizon check.
4. **The fixed laws (D63):** cap_vin brings the rising steps to 193 /
   177 A. Nothing fixed touches the falling 1 µs step (phase 4, 206 A).

## 1. Criteria (BOUNDARY Section 2)

| # | criterion | result |
|---|---|---|
| 1 | each vin return > cap_vin (−103.4) | pass nominally (−10.2 / −30.7 / −10.5); invalid (steady state changed) |
| 2 | best vin: +4.8 V 1 / 5 µs ≤ 180 A | pass nominally (172 / 163); invalid |
| 3 | rtl +4.8 V / 1 µs ≥ 195 A; rails ≥ best vin −5% | **miss** (189 / 160 / 165: operating-point shift); rails pass |
| 4 | no harm (divergence, load rows, Vo extremes) | pass within 120 periods; **fails over 600** (the steady check) |

**Decision:**
- None of the policies goes forward.
- **A127 re-registers with structural fixes:**
  - a pure feed-forward with an anchored residual policy, so the action
    is zero in steady state by construction;
  - a 240-period horizon;
  - steady-state identity and long-horizon settling as criteria.

## 2. Limits

- D63 only.
- One design (2.5 MHz).
- The steady-state check was added after the registered evaluation.
