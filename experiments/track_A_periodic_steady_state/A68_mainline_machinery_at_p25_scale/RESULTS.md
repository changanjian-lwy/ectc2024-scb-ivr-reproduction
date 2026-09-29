# A68 - the main line's P25-native event machinery at P25 scale (RESULTS)

Track A, `DIAGNOSTIC`. The main line's code was run **read only**: no
main-line file was changed. It is the other session's working tree, partly
uncommitted; the bytes run hash to `94db011926eb3f8d` over 33 files
(`a68_context.source_hashes()`). This tests the hypothesis in A67 Section 4.

Records:
- `results.json` (`a68_periodic.py`);
- the three single runs from `python3 a68_context.py fixture|p25|p25_override`.

## 0. Verdict

**The hypothesis holds. The main line's repeated failure (D23-D38: another
phase's current reaches zero before SH2 reaches ZVS) is a property of its
synthetic fixture's scale, not of the P25 mechanism or the event model.**
The same machinery was given only P25-scale values, with alpha kept at the
fixture's 5%. It then passes SH2 ZVS on the first try (M5, 4.6 ns), which no
fixture seed ever did.

Two further findings, both for the main line to decide on:

1. **A numerical-contract conflict at M7, a path never exercised before.**
   - The M5 ZVS root is located to the declared 10 nV tolerance. It lands
     at -6 nV (-5 nV with 100 uF series capacitors).
   - The ON switch SH2 preserves that residual through M6, because the
     contract does not project it away.
   - D11's entry rule then blocks M7, because it requires an *exactly*
     zero reverse gap.

   Along the flow, SH2's gap is positive 1 ps later and rises at 18 V/ns
   (the SL2 target is reached in 0.12 ns), so nothing physical reverses.
   M2 never meets this: SH1's gap is exactly 0.0, since SH1 sits on the
   fixed input.
2. **Under per-phase current control, periodic closure is not reached
   (ill-conditioned).** A diagnostic override releases only reverse gaps
   with -tol <= value < 0 and an outward rate. With it, the full M1-M15
   cycle closes onto the next SH1 section, with ZVS on all three high
   sides, at an emergent **1.943 us (0.515 MHz)**; P25's hardware runs at
   0.5 MHz.
   - Truncated-SVD Newton brings the current residual after one cycle to
     2.6e-5 A (from 2 A). The voltage residual stalls at 0.9 mV.
   - `J - I` has two near-null directions, both in the (iL2, iL3) plane:
     the phase spacing is nearly neutral.
   - The largest section-map eigenvalue is ~1.14. A plain iteration leaves
     the 15-mode order after 14 cycles.

   *Correction (2026-09-29, after D41):*
   - The first version said "no isolated period-1 orbit". That is too
     strong.
   - The Jacobians above used a 2e-6 finite-difference step. The section
     map carries ~1e-8 event-location noise, so that step gives ~5e-3
     derivative error.
   - Recomputed with a 1e-3 step, the two small singular values are
     3.0e-4 and 2.5e-4. Both still lie in (iL2, iL3), so the phase spacing
     is still nearly neutral.
   - That makes any orbit very ill-conditioned, and Newton did not
     converge. It does not prove that none exists.
   - With the mathematical model's D41 single-sensor (phase-shift) control,
     P25 Sec. III, Newton converges to a returned section (residual
     ~1e-8). See `symbolic_derivations/02_P25_native/D41_*`.

## 1. Runs

| case | values | result |
|---|---|---|
| fixture (control) | main line's D12/D29 fixture: 1 F, 2/3/4 H, Ton 0.02 s, alpha 5%, peak ref 20 A | blocked at **M5** (as the main line reports) |
| P25 scale, main-line rules | 30 nH; 0.69 / 1.38 nF per high / low bank; Ton 500 ns; peak ref 50 A; alpha 5%; load 67.5 A; Cs 100 uF; Co 100 uF | M1-M6 pass, including **M5 SH2 ZVS**; blocked at **M7** (exact-zero entry rule) |
| P25 scale, 10 uF Cs, override | same but Cs 10 uF | M1-M10 pass, including **M10 SH3 ZVS**; blocked at M11 because the ~1.25 V series-capacitor droop cut phase 1's peak (41.9 A), so its current reached zero during phase 3's on-time |
| P25 scale, override | as row 2 | **M1-M15 complete**, next SH1 section at 1994.7 ns from the rough seed |

P25-scale value choices:
- **Inductance.** 30 nH is the value implied by P25's reported 50 A peak
  with its 22 nH part.
- **Switch capacitance.** GS61008T charge-equivalent over 0-4 V (A67):
  1 high side, 2 low sides.
- **Series capacitors.** P25 assumes zero series-capacitor ripple and
  publishes no value; 100 uF is a `PROJECT_DECISION`.
- **Seed.** A steady-state estimate: 8 V / 4 V on the series capacitors,
  phases spaced T/3.

Everything else is the fixture's own model choice: ideal zero-drop reverse,
zero winding resistance, zero snubber.

## 2. Periodic-closure diagnostics (`a68_periodic.py`, override on)

| step | max voltage residual | max current residual | period |
|---|---:|---:|---:|
| rough seed | 1.0e-2 V | 2.0 A | 1994.7 ns |
| TSVD-Newton 1 | 9.2e-4 V | 1.9e-2 A | 1943.3 ns |
| TSVD-Newton 5 (no further descent) | 9.2e-4 V | 2.6e-5 A | 1943.2 ns |

- **Singular values of `J - I`:** 37.5, 21.2, 1.01, 0.41, 1.2e-3, 7.0e-4.
- **The two dropped directions:**
  (iL2, iL3) ~ (0.88, 0.48) and (-0.48, 0.88).
- **Meaning.** Perturbing phase 2's and 3's currents at the section just
  carries over to the next section: each phase turns on when *its own*
  current reaches the negative target, so nothing restores the spacing.
  The 0.9 mV voltage residual sits in the same near-null subspace.
- **Eigenvalues of the section map:** 1.138; 0.945 +/- 0.160i; 0.830;
  0.587; ~0 (the section constraint).
- **Override.** 408 uses in total, all at the M7/M12/M15 entries (SH2, SH3,
  SL1). Max |gap| 9.99 nV, inside the 10 nV tolerance, and all with an
  outward rate.

Note for the main line (a lead, not a finding): the project's P25 baseline
records that P25 senses **one representative inductor current per module**,
not one per phase (`paper_locked` baseline, "Current sensing"). The native
model triggers each phase on its own current, which leaves the spacing
neutral.

## 3. What this means for the main line

- Do not tune the synthetic fixture further. Its failures are scale
  effects: flip time 122-150 times the on-time (A67).
- At P25 scale, the remaining obstacles are specific and contractual:
  1. how D11 should treat tolerance-level ON-switch residuals at the next
     entry (exact zero vs. `|gap| <= tol` with an outward rate);
  2. a closure formulation for a model with a neutral phase-spacing
     direction. Options include pinning the phase spacing as P25's
     one-sensor control would, adding the damping the hardware has, or a
     shooting formulation over the neutral family.
- These are the main line's decisions. A68 only reports what its code does
  at P25 scale.

## 4. Limits

- The override is diagnostic. It is not the main line's accepted rule, and
  results that use it are labelled so.
- Event detection is sampled (4000 intervals per search horizon, as in the
  main line's own conditional scans). It is not certified root coverage.
- The P25 values are orders of magnitude (P25 used only for causal
  understanding). The model is ideal and lossless, with constant
  capacitances and a constant-current load port.

## 5. Reproduction

```
python3 a68_context.py fixture        # control: blocked at M5
python3 a68_context.py p25            # main-line rules: blocked at M7
python3 a68_context.py p25_override   # full M1-M15 cycle
python3 a68_periodic.py               # Newton / eigenvalues / plain iteration -> results.json
```
