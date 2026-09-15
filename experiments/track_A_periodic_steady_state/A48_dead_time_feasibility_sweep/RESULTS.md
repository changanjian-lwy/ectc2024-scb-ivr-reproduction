# A48 result -- dead-time feasibility sweep

## Outcome, stated first

Two separate, unambiguous findings:

1. **The 1% and 2% (`P24_EXPLICIT`) release rows never reach zero-voltage
   turn-on at any tested dead time (0.5-20 ns).** At every `T_DEAD`, the
   residual `V(vin,a1)` at forced turn-on is large (8.2-13.9 V) -- roughly
   the same order of magnitude as the row's own already-known bounded
   oscillation, never close to zero. This is exactly what A42 predicts and
   is not a new finding on its own: A42 already showed these two rows never
   reach a natural `Vds=0` crossing at all inside the observation window: a
   longer or shorter dead time only changes *when* the driver forces QH1 on
   and therefore *which* point of the same bounded, never-zero oscillation
   gets hard-switched into -- it cannot manufacture a zero crossing that the
   release current never produced.
2. **For the 7.77% row (A42's own bracketed natural-ZVS threshold), the
   fixed-delay mechanism reproduces A42's natural-ZVS result only inside a
   narrow window of `T_DEAD` centered on the natural commutation duration --
   not for "any `T_DEAD` above the natural duration" as a first-pass
   hypothesis might suggest.** Below the window, forced turn-on happens
   before the natural crossing (residual voltage falls toward zero as
   `T_DEAD` approaches the window from below). Above the window, the LC tank
   is still ringing (QH1 is still off, nothing holds `Vds` at zero), so the
   residual voltage does **not** stay at zero and does **not** vary smoothly
   -- it rises again and then swings over a wide, non-monotonic range (up to
   20.9 V, i.e. *worse* than many of the too-early cases) as `T_DEAD`
   increases further. The window is centered almost exactly on A42's own
   independently-measured commutation duration (2.1516 ns): the fine grid
   finds `Vds_at_forced_on=0.0000 V` at `T_DEAD=2.15 ns`.

## Simulation completion

All 48 generated cases (27 coarse + 11 refinement + 10 fine, all on the
7.77% row) completed normally after one fix (below). No case was left
incomplete or discarded.

### A numerical obstacle encountered and how it was resolved

Several coarse cases (all cases that force a hard turn-on into several
volts of residual `Vds`, e.g. `01pct`/`T_DEAD=10ns`) initially hung
indefinitely (observed: >20 minutes of CPU time with no result, confirmed
non-convergent, not merely slow) under A42/R04D3A's inherited
`chgtol=1e-16`. That tolerance was tuned for a soft, near-zero-differential
ZVS closure; a hard closure across several volts demands a charge-transfer
resolution per timestep that `chgtol=1e-16` cannot satisfy during a
multi-thousand-amp instantaneous spike, and the adaptive-timestep solver
never converges. Root-caused by isolated testing (not guesswork): truncating
the `.tran` window did not help (the stiffness is at the discontinuity
itself, not the subsequent settling time); relaxing `chgtol` to LTspice's
own default, `1e-14` (100x looser, still tight), immediately resolved every
case (each completes in under 1.5 s). This relaxation was verified not to
change the physics of interest: A42's own original 1% netlist, rerun
standalone with only `chgtol` changed (no other edit), reproduces A42's
published 9.2566 V minimum post-release `Vds` to 4 significant figures
(9.2567-9.2570 V across two isolated checks, one with A48's reverse diode
added and A42's original controller otherwise untouched). See
`build_a48_dead_time_feasibility_sweep.py` and BOUNDARY.md for the full
account.

## Parameters actually used

Identical to A42 except the swept `T_DEAD` and the controller/diode changes
stated in BOUNDARY.md: `Vin=48V`, `Vo=1V`, `nP=4`, `NM=1`, `L=1.4667nH`,
`CH=385pF`, `CL=770pF`, `RHS`/`RLS` from `GS61008T_RDS_TYP_25C`, three
`NEG_FRAC` rows (0.01, 0.02, 0.0777) inherited unchanged from A42.

## Coarse grid: all three rows, T_DEAD = 0.5-20 ns

`Vds_at_forced_on` (V) and `I(L1)` at forced turn-on (A):

| T_DEAD (ns) | 1% Vds | 1% I | 2% Vds | 2% I | 7.77% Vds | 7.77% I | 7.77% before natural? |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0.5 | 11.376 | -1.490 | 10.843 | -2.647 | 7.774 | -9.324 | yes |
| 1 | 10.717 | -1.513 | 9.736 | -2.408 | 4.071 | -7.576 | yes |
| 2 | 9.607 | -0.925 | 8.200 | -0.963 | 0.081 | -1.184 | yes |
| 3 | 9.269 | 0.182 | 8.227 | 1.022 | 2.216 | 5.869 | **no** |
| 5 | 11.127 | 1.523 | 12.036 | 2.475 | 17.284 | 7.967 | no |
| 7 | 12.700 | -0.078 | 13.803 | -0.852 | 20.162 | -5.318 | no |
| 10 | 9.765 | -1.080 | 8.380 | -1.287 | 0.390 | -2.484 | no |
| 15 | 12.692 | 0.130 | 13.900 | -0.502 | 20.872 | -4.149 | no |
| 20 | 9.579 | 0.878 | 9.114 | 2.050 | 6.432 | 8.814 | no |

The 1%/2% columns show no trend toward zero anywhere in this range --
values stay in the same broad 8-14 V band regardless of `T_DEAD`, confirming
finding (1) above. The 7.77% column falls toward zero as `T_DEAD` rises
from 0.5 to 2 ns, then behaves non-monotonically for `T_DEAD>=3 ns` (2.2,
17.3, 20.2, 0.4, 20.9, 6.4 V in sequence) -- this is the LC tank continuing
to ring with QH1 still off; there is no reason to expect the fixed-delay
value to land near a favorable point of that ongoing ring for an arbitrary
`T_DEAD`, and mostly it does not.

## Refinement grid: 7.77% row, T_DEAD = 2.0-3.0 ns (0.1 ns steps)

| T_DEAD (ns) | forced before natural? | Vds_at_forced_on (V) | I at forced (A) |
|---:|:---:|---:|---:|
| 2.0 | yes | 0.0811 | -1.184 |
| 2.1 | yes | 0.0109 | -0.438 |
| 2.2 | no | 0.0056 | 0.310 |
| 2.3 | no | 0.0648 | 1.057 |
| 2.4 | no | 0.1884 | 1.797 |
| 2.5 | no | 0.3757 | 2.527 |
| 2.6 | no | 0.6256 | 3.242 |
| 2.7 | no | 0.9365 | 3.937 |
| 2.8 | no | 1.3067 | 4.610 |
| 2.9 | no | 1.7340 | 5.255 |
| 3.0 | no | 2.2157 | 5.869 |

## Fine grid: 7.77% row, T_DEAD = 2.10-2.24 ns (0.01-0.02 ns steps)

| T_DEAD (ns) | forced before natural? | Vds_at_forced_on (V) | I at forced (A) |
|---:|:---:|---:|---:|
| 2.10 | yes | 0.0109 | -0.438 |
| 2.12 | yes | 0.0046 | -0.288 |
| 2.14 | yes | 0.0009 | -0.139 |
| 2.15 | yes | **0.0000** | -0.064 |
| 2.16 | no | 0.0000 | 0.011 |
| 2.17 | no | 0.0004 | 0.086 |
| 2.18 | no | 0.0015 | 0.161 |
| 2.20 | no | 0.0056 | 0.310 |
| 2.22 | no | 0.0122 | 0.460 |
| 2.24 | no | 0.0215 | 0.610 |

Exact-zero residual voltage is found at `T_DEAD=2.15 ns`, matching A42's own
independently-measured commutation duration (`P24_COMMUTATION_DURATION` =
2.1516 ns for this row) to within simulation resolution -- two independent
measurement methods (A42's ideal-detector crossing time, and A48's swept
fixed-delay bracket) agree on the same physical instant.

## Residual-voltage-vs-dead-time direction, stated explicitly

- **Below the near-zero window** (`T_DEAD` from 0.5 ns up to ~2.15 ns for
  the 7.77% row): residual `Vds` at forced turn-on **falls** as `T_DEAD`
  increases -- monotonically, from 7.77 V at 0.5 ns down to 0.0 V at
  2.15 ns. This is the expected, well-behaved direction: catching the
  natural ZVS transition later (but still before it completes) means less
  voltage is left to hard-switch into.
- **Above the near-zero window** (`T_DEAD` greater than ~2.16 ns for this
  row): residual `Vds` **rises again** immediately (0.0 V at 2.16 ns to
  2.2 V by 3.0 ns in the fine/refinement data), and for still larger
  `T_DEAD` (5-20 ns) it **does not continue rising smoothly nor return
  toward zero** -- it swings non-monotonically across a wide range (2.2 V,
  17.3 V, 20.2 V, 0.4 V, 20.9 V, 6.4 V) because the underlying LC network
  keeps ringing once past the natural crossing with QH1 still off. A longer
  dead time is therefore **not** a safe, monotonically-improving choice once
  past the natural crossing; it is only safe inside the narrow window found
  above.
- **For the 1%/2% rows**, there is no falling trend at all: residual `Vds`
  stays in the 8-14 V band across the whole 0.5-20 ns range with no
  systematic direction, consistent with these rows never having a zero
  crossing to approach in the first place.

## Practical dead-time bracket

For the 7.77% row, using a practical near-zero criterion of
`|Vds_at_forced_on| < 50 mV`: interpolating the fine/refinement data, the
window is approximately **2.04 ns to 2.28 ns**, centered on the exact-zero
point at 2.15 ns (A42's own measured commutation duration). Outside that
roughly +/-0.13 ns window, residual voltage grows quickly on the low side
and unpredictably (via continued ringing) on the high side.

For the 1% and 2% rows: **no dead time in the tested 0.5-20 ns range reaches
anywhere close to zero residual voltage**; there is no bracket to report
because there is no natural crossing to catch. This matches A42's own
finding exactly and is expected, not a new result.

## Acceptance condition

Met for the primary goal (a feasibility map of forced-turn-on residual
voltage vs. dead time, for the fixed release rows reused from A42). Not met
in the sense that no single "T_DEAD above X is always safe" bracket exists
for the 7.77% row -- the honest result is a narrow window, not a one-sided
threshold, and that nuance is itself the useful output for comparing against
Mihai's eventual real dead-time number.

## Grades

- **1% row (`P24_EXPLICIT`)**: `EXPECTED_FAILURE`. No `T_DEAD` in the tested
  range produces near-zero residual voltage; consistent with A42's own
  established result that this row never reaches natural ZVS. This was
  expected before running and is confirmed, not discovered.
- **2% row (`P24_EXPLICIT`)**: `EXPECTED_FAILURE`, same reasoning as 1%.
- **7.77% row (`A42_NATURAL_ZVS_REFERENCE`), narrow-window sub-result**:
  `LOCAL_PASS`. A specific `T_DEAD` bracket (~2.04-2.28 ns) reproduces
  near-zero residual voltage and cross-validates A42's independently
  measured commutation duration, but this is one local interval on one
  phase, not any larger claim.
- **7.77% row, "any T_DEAD above natural duration is safe" hypothesis**:
  `REJECTED`. The coarse grid directly falsifies this: `T_DEAD=5,7,15 ns`
  (all above the 2.1516 ns natural duration) give 17-21 V residual voltage,
  far from zero. This specific hypothesis, stated in this experiment's own
  planning text, must not be carried forward as if confirmed.
- **Overall experiment**: `SENSITIVITY_ONLY`. `T_DEAD` remains a swept
  sensitivity value; the real dead time is still `BLOCKED_BY_MISSING_DATA`
  (Mihai, Report Section 8, unanswered).

## First failure boundary

For 1%/2%: the failure boundary is identical to A42's -- insufficient
release-current margin, not a timing problem, and no timing value can move
it.

For 7.77%: the "failure" (nonzero residual voltage) boundary is timing
precision itself -- roughly +/-0.13 ns around the natural commutation
instant for this specific device/current combination. This is a much
tighter timing tolerance than the 0.5-20 ns coarse span originally deemed
"physically reasonable," which is itself a useful, reportable finding: a
fixed-delay driver would need dead-time accuracy at the sub-nanosecond level
to reliably catch this particular ZVS transition, not just "roughly the
right order of magnitude."

## What must never be changed because of this failure

- Do not conclude that any dead time above ~2.15 ns is acceptable for the
  7.77% row; the data directly contradicts that. Only report the bracket
  actually found.
- Do not use this experiment's device/capacitance assumption (GS61008T) or
  its narrow-window finding to infer anything about the EPC2067 branch
  (A45) without rerunning the same sweep there explicitly (not done in this
  experiment -- see BOUNDARY.md).
- Do not treat the exact-zero point (2.15 ns) as a recommended real-world
  dead-time setting; it is a zero-margin knife-edge in this idealized model
  (no jitter, no temperature variation, no unit-to-unit spread). A real
  driver would need margin inside the ~2.04-2.28 ns window, and knowing
  which side to bias toward requires the real Mihai dead-time/propagation
  number this experiment does not have.

## Module to adjust next

Comparing this bracket (2.04-2.28 ns for the GS61008T/7.77% case) against
Mihai's real dead-time/driver-propagation-delay number, once given, is the
direct next step (Report Section 8's second data request). A second,
separately-labelled EPC2067 branch (A45's device assumption) is the natural
next sweep if pursued, since A45 found a very different natural-ZVS
threshold (22.04-22.05%) and almost certainly a different commutation
duration and therefore a different narrow window.
