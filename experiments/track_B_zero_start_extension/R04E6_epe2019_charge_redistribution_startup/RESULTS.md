# R04E6 result -- EPE2019 charge-redistribution ladder bootstrap

## Outcome, stated first

All 16 cells (`TH` in {200 ns, 1 us, 5 us, 20 us} x `NCYC` in {1, 3, 5, 10})
completed and were measured. **The mechanism, run as a blind repeated
cycle, does not converge toward the `36/24/12 V` target -- it moves away
from it as more cycles are applied.** A single, fully-settled cycle
(`TH>=5 us`, `NCYC=1`) reaches roughly `VC1~24 V`, `VC2~VC3~12 V` --
closer to zero than the start, but a different ratio (approximately
`2:1:1`) from the `3:2:1` target, with an aggregate ladder error of about
`0.84` (the same metric R02B uses: `|VC1-36|/36+|VC2-24|/24+|VC3-12|/12`).
Every additional cycle beyond the first makes this worse, not better, at
every tested hold time: by `NCYC=10` all three capacitors have converged
toward each other at roughly `45-46 V` each -- nearly equal voltages, the
opposite of the required `3:2:1` asymmetry. Grade: `NOT_CONVERGING` for
9/16 cells (`NCYC>=3`), `SENSITIVITY_ONLY` for the remaining 7 (`NCYC=1`,
no multi-cycle trend to grade).

## A numerical artifact caught and corrected before being reported

Every one of the 16 cells' `.meas`-extracted `ICS1_MAX` came back as
exactly `1231993.625 A` -- bit-identical across all 16 cells, which is
physically impossible for 16 cells with different hold times and cycle
counts if this were a real, parameter-dependent current. Checked directly
against the netlist: `ICS1_MAX` is measured `MAX I(XMOD:CS1) FROM 0 TO
<end>`, i.e. it includes the first simulation instant, whereas the
separately-defined `ICS1_INRUSH_CYC1` explicitly starts at `1 ns` and
returns a much smaller, cell-dependent value (e.g. `4574 A` for the
`TH=200 ns`/`NCYC=1` cell). Because state (a)'s `H1`+`L1` charging loop for
`C1` is identical in every cell regardless of `TH`/`NCYC` (those parameters
only affect what happens *after* the first sub-nanosecond), the solver's
very first, sub-1-ns timestep produces the same numerically extreme
transient spike in every cell -- a startup-transient artifact of the ideal
switch model at `t=0`, not a converged or physically meaningful current.
**`ICS1_MAX`/`max_abs_current_a` as originally computed is discarded and
must not be read as a real current.** The properly time-windowed
measurements (`*_inrush_cyc1`, `*_stateb_cyc1`, `*_statec_cyc1`, all of
which exclude the first 1 ns) are used below instead.

## Physically meaningful peak currents (t>1 ns only)

Taking the `TH=200 ns`/`NCYC=1` cell as representative of the fast end and
`TH=20 us`/`NCYC=1` as the slow end:

| Quantity | `TH=200 ns` | `TH=20 us` |
|---|---:|---:|
| `C1` charge current (state a) | 4574 A | 4574 A (same -- state (a)'s peak is set by the L-C step response, not by `TH`, since `TH` only decides how long the state is *held*, not its initial slope) |
| `C1`/`C2` current during state (b) | +234/-704 A | +112/-3428 A |
| `C2`/`C3` current during state (c) | +50/-117 A | +56/-1712 A |

These are the actual inrush-scale currents this mechanism produces, and
they are large relative to P24's `125 A` per-phase boundary-mode target --
tens to thousands of amps flowing directly capacitor-to-capacitor with only
switch `Ron` (a few `mOhm`) as series impedance. BOUNDARY.md's Section 4
already states the source paper gives no numeric inrush limit for this
mechanism, so no pass/fail threshold is applied here either; this is
reported as a plain finding, not a graded failure.

## Ladder evolution vs. cycle count, all four hold times

`LADDER_ERR = |VC1-36|/36 + |VC2-24|/24 + |VC3-12|/12` (0 = perfect,
lower is better; starting from zero energy this metric starts at `3.0`).

| `TH` | `NCYC=1` | `NCYC=3` | `NCYC=5` | `NCYC=10` |
|---|---:|---:|---:|---:|
| 200 ns | 2.524 | 2.524 | 2.524 | 2.524 |
| 1 us | 0.969 | 1.585 | 2.690 | 3.943 |
| 5 us | 0.851 | 1.497 | 2.680 | 3.937 |
| 20 us | 0.836 | 1.508 | 2.696 | 3.944 |

(`TH=200 ns` barely moves with more cycles because the hold time is too
short relative to the `L`-`C` time constants for any state to meaningfully
charge or redistribute anything in one pass -- confirmed by its `VC1/VC2/
VC3` values being nearly unchanged across `NCYC=1` through `10`, unlike the
other three rows.)

**Direction, stated explicitly and unambiguously**: for every hold time
long enough to matter (`TH>=1 us`), `LADDER_ERR` increases monotonically
with `NCYC` -- more repetitions of the exact 3-state cycle move the ladder
further from `36/24/12 V`, not closer. The best result in the entire grid
is a *single* cycle at a long hold time (`TH=20 us`, `NCYC=1`,
`LADDER_ERR=0.836`), not any repeated-cycle cell.

## Why this happens -- a causal account, not just a correlation

BOUNDARY.md Section 6 established (from the correctly-derived and
figure-verified truth table -- see that section for the disagreement this
corrected) that state (a) charges `C1` alone from `Vin` via `H1`+`L1`, then
state (b) redistributes between `C1` and `C2` via `H2`+`L1`+`L2`, and state
(c) redistributes between `C2` and `C3` via `H3`+`L2`+`L3`. States (b) and
(c) are plain charge-sharing loops between two capacitors with no
mechanism that biases the split toward the `2:1`/`2:1` ratios the `3:2:1`
target actually requires -- each redistribution pass tends to move the two
capacitors' voltages toward each other (weighted by their capacitance,
equal here), not toward a specific asymmetric target. Repeating the full
(a)-(b)-(c) cycle therefore repeatedly re-injects charge at `C1` (state a)
and then keeps re-equalizing the whole chain (states b, c) -- the net
effect over many cycles is a slow drift toward all three capacitors
converging to a common voltage, which is exactly the `NCYC=10` result
(`~45-46 V` on all three, nearly equal). This is a structural property of
running this specific 3-state sequence blindly and repeatedly, not a
tuning problem that a different `TH` or `NCYC` grid would fix.

This also clarifies the source paper's own wording: "bounce back-and-forth
... until the voltages ... become high enough" (p.4, describing the
related CSC-buck mechanism) implies a *monitored*, voltage-feedback-gated
stopping condition -- decide state-by-state, in real time, when to stop --
not a fixed, blind repeat count decided in advance. This experiment tested
the latter (open-loop, fixed `NCYC`) because that is what BOUNDARY.md
declared as the free sensitivity axis, and the result shows why the paper's
own phrasing needs the feedback it implies: without it, more cycles make
the ladder worse, exactly as found here.

## Comparison against every prior zero-start attempt

| Experiment | Mechanism | Best `LADDER_ERR`-equivalent result reached |
|---|---|---|
| R02A (unmodified transfer) | passive divider, IPEC-2018 values | `-78.84%/-95.60%/-98.80%` vs. target (worse than this experiment's worst cell) |
| R02B (tuned divider) | passive divider, swept `CDIV`/`TRAMP` | best cell `34.046/21.793/10.631 V`, `LADDER_ERR=0.260` (per STEP_06's own table; still not a pass, but closer than R04E6's best) |
| R04E6 (this experiment) | EPE2019 3-state switched-capacitor redistribution, zero external divider | best cell `23.97/11.98/11.98 V`, `LADDER_ERR=0.836` |

**R04E6 does not outperform R02B.** R02B's passive-divider approach (a
much larger, separate divider capacitance bank feeding the flying
capacitors through diodes) gets substantially closer to `36/24/12 V` than
this switched-capacitor technique does, at least in this specific 3-state,
fixed-order, un-monitored form. This is a genuinely new mechanism (no
overlap with R00-R04E5's approaches) and it does establish the ladder can
be moved partway from zero without invoking the inductor/`Vout` timing
problem that blocked R03A-R04E5 entirely -- but it does not reach the
target ladder on its own, and blind repetition actively hurts it.

## What this resolves and what it does not

Resolves: confirms EPE2019's Fig. 5 mechanism, applied literally and
blindly (fixed hold time, fixed cycle count, no voltage monitoring) to
P24's own topology and `Cfly=53.8 uF`, does not autonomously reach
`36/24/12 V`; identifies the specific reason (unbiased pairwise
redistribution drifts toward equalization, not the target ratio); and
establishes that a single well-settled cycle is a better starting point
than any tested repeated-cycle sequence.

Does not resolve: whether a *monitored* version of this same mechanism
(stop each state based on measured voltage, not a fixed timer -- closer to
what the source paper's own text implies) would reach the target; whether
a different state ordering or an added fourth redistribution state
(matching what EPE2019 describes for their CSC-buck variant's "empty one
FC and redistribute" option) would help; any `Vout` bootstrap or handoff
into the existing event-gated steady-state controller (explicitly out of
scope here, matching BOUNDARY.md); or hardware-realistic switch stress
during these inrush events (no rating check was performed).

## Next permitted action

Do not repeat this exact blind, fixed-`NCYC` sweep expecting a different
outcome -- the direction is established and monotonic. A monitored,
voltage-threshold-gated version of the same three states (exit each state
when a measured capacitor voltage crosses a computed target, not after a
fixed time) is the next reasonable variant of this specific mechanism, and
is a materially different, separately-scoped experiment, not a rerun of
this one with different grid points.
