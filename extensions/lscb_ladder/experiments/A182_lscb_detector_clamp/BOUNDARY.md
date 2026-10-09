# A182 - A180's switched clamp opened by a real detector (BOUNDARY)
Method: math. Open-loop LTspice power stage of one P24 module, the same plant as A180. A182 adds a detector-made window
(lscb_ladder p["win"], detect(), p["save_ls"]).
Context: extension lscb_ladder. The user approved it on 2026-10-09 evening. It answers the second external review,
point 6 (FINAL_SPEC Section 6), and A180's limit 2. Written and committed before any run. Nothing was run beforehand.
The steady deviation was estimated from A180's rail-1 ripple (0.45 V p-p) and its 0.13 V offset.
Decision it changes: whether a switched clamp with a realistic trigger still helps. This decides how the EEK5101 video
words the claim, and whether the lscb_ladder line closes positive with a detector spec or negative.
Cheaper check done first: none; this is the cheap model. Budget: 33 LTspice runs of about 20 s each.

## 1. What and why
- A180 opened the clamp window exactly at the input step, an ideal trigger.
  - A real detector fires only after the clamp voltage V(d(4-k)) - Vcs_k crosses a threshold vth.
  - Its comparator and floating driver then add a delay td.
  - By the time the switch closes, the ladder and the flying capacitor already differ by some ΔV. The switch then
    shares charge hard: a current spike limited only by resistance here, and a loss of about ½ C ΔV².
- **Method, two passes per row.**
  - Pass 1: the active variant with its window never open, so only its 3.0 V diode acts. The run records, for each
    vth, the first time at or after the step that max_k |deviation_k| ≥ vth, and the largest |deviation| before the
    step.
  - Pass 2: the window [t_det + td, t_det + td + 20 µs]. The switch closes on each overlap of an SL_k on-interval
    with the window, including mid-interval.
  - Until the switch first closes, pass 2 is the same circuit as pass 1. So this is exactly a one-shot detector
    with that threshold and delay.
  - The "ideal" rows open the same overlap window at the step: A180's trigger with A182's gating.
- **Grid.**
  - C_DC 20 µF: vth 0.75 / 1.5 V × td 0.1 / 0.3 / 1.0 µs.
  - C_DC 60 µF: vth 0.75 V, td 0.3 µs.
  - Rows: up1 (+4.8 V / 1 µs), up5 (+4.8 V / 5 µs), dn1 (-4.8 V / 1 µs).
  - Pass 1: 6 runs. Ideal: 6 runs. Detector: 21 runs.
- **Not tested.**
  - Clamp loop inductance: the spike is resistance-limited, so the peak magnitude is an upper bound. The ½ C ΔV²
    energy does not depend on R.
  - Retriggering, false triggers from load steps, and the detector's own offset and noise.
  - The closed loop.

## 2. Criteria
Base and ideal values come from A180's runs (same plant). If criterion 1 fails at 0.75 V, criteria 2-4 use 1.5 V
(registered fallback).
1. No false trigger: in every pass-1 run, the pre-step max |deviation| < vth, for both thresholds.
2. Rising step, vth 0.75 V, td 0.3 µs, C_DC 20 µF, up1: rail1_exc ≤ 2.32 V (½ of base 4.64) and max phase peak
   ≤ 222.6 A (base 242.6 - 20). These are A180 criterion 3's bounds.
3. Falling step, same setting, dn1: |rail1_exc| ≤ |A182 ideal_c20_dn1| + 0.30 V and max phase peak ≤ 178.2 A
   (base 198.2 - 20).
4. Hard sharing, same setting, up1: max clamp peak ≤ 1.5 × A182 ideal_c20_up1's max clamp peak.

## 3. Predictions (not criteria)
- **Pre-step |deviation| max:** 0.25-0.45 V, so neither threshold fires falsely.
- **t_det - t_step on up1:** 0.08-0.30 µs at 0.75 V and 0.25-0.50 µs at 1.5 V. On dn1, similar. On up5, about 4×
  later.
- **A182 ideal versus A180 act:** A182's ideal can close mid-interval. On up1 its rail1_exc is 1.8-2.2 V at 20 µF and
  its peak within ±10 A of 161 A.
- **up1 at C_DC 20 µF:**

  | vth | td (µs) | rail1_exc (V) | peak (A) |
  |---|---|---|---|
  | 0.75 | 0.1 | 2.0-2.8 | 160-195 |
  | 0.75 | 0.3 | 2.3-3.4 | 170-215 |
  | 0.75 | 1.0 | 3.6-4.6 | 205-240 |
  | 1.5 | each | +0.2-0.6 V over the same td at 0.75 V | |

  So criterion 2 is likely marginal.
- **Clamp peak:** 1.5-3 × ideal at td 0.3 (hard sharing of ΔV ≈ 1.5-3 V through ~6 mΩ), so criterion 4 is likely to
  FAIL. The ½ C ΔV² energy per event is 5-25 µJ. The 3.0 V diode bounds ΔV near 3 V, which caps the spike.
- **Rail1_exc grows with td:** at each vth and on up1. Phase luck (the next LS interval is 0-0.45 µs away) may swap
  0.1 / 0.3.
- **up5:** smaller penalty. Rail1_exc at 0.75 V / 0.3 µs is 2.0-2.6 V (ideal A180 2.03).
- **60 µF at 0.75 V / 0.3 µs, up1:** 1.8-2.8 V.

## 4. Decision rule
- **1-4 pass:** the video keeps "a switched clamp helps", with the condition "detector ≤ 0.3 µs at 0.75 V". The line
  closes positive, with that detector spec. Step 2 (closed loop) stays unrun (user, 2026-10-09).
- **2 or 3 fails:** the video says the benefit needs a trigger faster than 0.3 µs. The largest td that still meets
  2-3 from the grid is reported as the requirement, or "none tested" if no td does. The line closes as a conditional
  negative.
- **4 fails:** whatever 2-3 say, the claim gets the caveat "late closure shares charge hard: a clamp current spike of
  X A (resistance-limited) and Y µJ per event; it needs a current-limited clamp". That stays an open item, not run.
- **1 fails at both thresholds:** the detector as defined does not work; report the steady deviation and stop.
