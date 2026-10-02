# A109 - a valley trim for the slotted phases (RESULTS): falsified, not adopted

Track A, with four-module checks. One factor: `slot_trim` = 1
(`st_smax` 64).

**Boundary:** `BOUNDARY.md`, committed with the code (a85ac64) before
any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json`;
- `a109_summary.json` (`a109_analyze.py`).

**Physical model:**
- Verilog RTL;
- A88's plant (kernel2);
- A105's I2 with `slot_lo`;
- 5%, 25 C;
- one module and four modules.

## 0. Verdict

1. **The hypothesis is falsified.** A slotted phase's slot time does not
   control its steady valley.
   - **The offsets ran to the ±1024 LSB bound in steady state.** s1_n0:
     phases 2/3/4 at −326 / −1024 / +1001 LSB.
   - **The valleys hardly moved:** phase 3 −6.93 → −6.85 A, phase 4
     −5.85 → −5.75 A.
   - **What the wound-up integrator did:**
     - the turn-off sd rose from 0.13 to 1.59 A (the step dithering at
       up to 64 LSB);
     - in four modules it broke the interleave: gaps 0.14-55.9 ns, with
       1834 and 1590 late fires in two slaves.
2. **No line step improved:**
   - falling 50 µs: phase 4's valley +11.4 A (A108 +12.1);
   - 10 µs: +29.9 A (A108 +29.2);
   - 1 µs: +54.8 A (+55.7).
   - Load steps and Vo were unaffected (within 5%). No overlap anywhere.
3. **`slot_trim` is not adopted.**
   - The default stays 0. The gates showed the code changes no earlier
     result.
   - The feature is a candidate for removal at the next clean-up (less
     burden). It stays only so these runs remain reproducible.

## 1. Why: what sets a slotted phase's valley (and an erratum to A108)

**A108's records**, at phase 4's worst valley in the falling steps:

| run | phase-4 rail vs Vin/4 | phase-4 current (valley + nearest peak)/2 | peak | valley |
|---|---|---|---|---|
| before the step | 11.96 vs 12.00 V | 65.0 A | 135.8 A | −5.8 A |
| m48_50us at 444.9 µs | **11.18 vs 10.92 V** (+0.26) | **73.5 A** (+13%) | 134.9 A | +12.1 A |
| m48_10us at 410.6 µs | **11.32 vs 10.80 V** (+0.52) | **82.2 A** (+26%) | 135.1 A | +29.2 A |

- **While the ladder re-divides, the phases with the higher rails carry
  more current.** That is how the series capacitors move: D60's
  restoring current.
- **At a common period and Ton**, the extra current lifts the whole
  waveform. The peak stays near 135 A, and the valley rises above zero.
- **A constant slot offset only shifts the waveform in time.** It does
  not change the current the phase must carry, so an integrator on the
  valley has no authority and winds up.
- **Erratum to A108 RESULTS 0.3.**
  - "falling inputs ... turn the high-rail phases off early" is wrong.
    The high-rail phases carry the ladder's restoring current, which
    raises their valleys.
  - The scaling with the ramp rate stands, as measured.
- **Open:** why the extra current (8.5 A at 0.096 V/µs) exceeds what
  tracking the ramp alone needs. Cs dV/dt is ~0.2 A for the ladder's
  share, a 3 A difference in valley terms. This needs a derivation (the
  SCB's per-phase current split during ladder motion) before any further
  remedy.

## 2. Registered criteria (BOUNDARY Section 3)

| # | criterion | result |
|---|---|---|
| 1 | slotted valleys within ±0.3 A of −6.25 A (s1_n0, m4_n0) | **miss**: phase 3 −6.85 A, module 1 phase 3 −7.22 A |
| 1 | master phase 1 unchanged (±0.05 A) | pass |
| 2 | high-side turn-on within ±0.15 V; low side ≤ 0 | s1_n0 **miss** (phase 2 9.09 against 8.91 V); low side pass |
| 3 | offsets within ±64 LSB; gaps T/16 ± 2 ns | **miss**: at ±1024; gaps 0.14-55.9 ns |
| 4 | Vo, overlap, peak | pass |
| 5 | j30 sd ×(1 ± 0.3); steps ±10% | sd **miss** (1.41 against 0.49 A, phase 2); steps pass (+11.89 / −14.85 mV) |
| 6 | falling 50 / 10 µs: valleys ≤ −2 A | **miss** (+11.4 / +29.9 A) |
| 7 | falling 1 µs: slotted ≤ +25 A | **miss** (+54.8 A) |
| 8 | rising: phase 1 unchanged; slotted ≥ −15 A | phase 1 1 µs +49.9 against +56.7 A (**miss**, changed by the others' shifts); slotted −27.8 A **miss** |
| 9 | m4_ls_p10: slave 1 valleys ±0.3 A of −6.25, current −10.0 ± 1% | **miss**: valleys −3.5 to −4.6 A (offsets at +1024), current −8.46% |
| 10 | m4_l_m48_10us: all valleys negative | **miss** (+28.9 to +30.8 A, as C03) |

## 3. What remains true, and what this changes

**Remains true:**
- A108's measured tolerances:
  - peak ≤ 200 A from 2.4 V/µs;
  - valleys negative only for slow rising inputs;
  - not for falling inputs down to 0.096 V/µs.

**What this changes:**
- **The positive valleys in falling inputs are tied to the ladder's own
  re-division** at a common period. A turn-off timing correction cannot
  remove them. The options left:
  - **Accept them:** a short loss of zero-voltage turn-on on the
    high-rail phases while the ladder moves (the bus slew decides how
    long). The 200 A limit holds.
  - **Let each phase leave the common period during the transient**
    (per-phase boundary turn-off). This keeps every valley at −i_neg, as
    D60's model assumes, but the interleave slides until the rails
    agree.
  - **Shape the input slew or add active balancing** of the series
    capacitors.
- **D61's scheme B** (a sharing trim per slave) cannot be built on a
  slot trim either. A slave's current follows its rails and inductance,
  not its slot time. This is consistent with C01 and C03.
