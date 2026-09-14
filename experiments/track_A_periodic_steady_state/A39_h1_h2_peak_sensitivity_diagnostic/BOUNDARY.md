# A39 H1-vs-H2 peak-current sensitivity diagnostic boundary

Track: A (periodic steady-state reproduction). This is a **diagnostic**
experiment: it measures, it does not solve. No free variable is fitted to a
target here; the deliverable is a causal explanation, not a converged
residual.

## 1. Parent experiment

A38 (`A38_h2_h3_local_peak_and_100ns_zvs_solve`), graded
`PHYSICAL_BOUNDARY_FAIL` on `R1`: probing `IL2_INIT` in `{-2,-1,-0.5,+0.5,
+1,+2} A` around A37's seed showed the H2 peak-current residual
(`iL2(TON2 end)-125 A`, stuck near `-7.2 A`) moves only ~0.016 A per A of
`IL2_INIT`, and any decrease breaks H2's own admission window entirely. By
contrast, A36's own solve moved `IL1_INIT` by `6.23 A` (from A35's `-0.9357 A`
to `5.2947 A`) and closed a `-5.74 A` peak-current gap for H1 -- an implied
sensitivity of about `0.92 A/A`, roughly 60x larger than H2's. The user asked,
correctly, whether H1's apparently clean linear solve might simply have
landed in a locally linear region while sharing the same underlying
saturation H2 shows elsewhere -- i.e. whether "H1 is solved" and "H2 is
structurally stuck" are actually the same phenomenon observed at two
different points on one nonlinear curve, not two different phenomena.

## 2. What changed relative to the parent

A38 (and A36 before it) treated `IL1_INIT`/`IL2_INIT` purely as solver
knobs and stopped once a target residual converged or was shown locally
insensitive. A39 does not solve anything. It (a) re-sweeps `IL1_INIT` over a
much wider range than A36 ever explored, specifically to see whether H1's
peak-vs-`IL1_INIT` curve also flattens/saturates somewhere, and (b) traces
the internal waveforms during `TON1` and `TON2` (inductor current slope,
flying-capacitor voltage, switch voltage drop, and any other device firing
inside the window) to identify which physical quantity actually differs
between the two phases and causes H2's near-zero sensitivity.

## 3. What did not change

Topology, device `Coss`, ideal reverse-conduction clamp, inductor
`1.4667 nH`, each phase's fixed `TON=16.6667 ns`, nominal phase-slot origins,
the `9%` labelled P25 branch, the ideal `1 V` output clamp, and timestep --
all identical to A38/A37/A36/A35/A27. `IL3_INIT` (A38's solved value,
`56.3206 A`), `IL4_INIT`, and all three `VCk_INIT` are held at A38's values
throughout unless a specific probe explicitly says otherwise (see Section 6).

## 4. Provenance of the values used

All swept `IL1_INIT`/`IL2_INIT` values in this experiment are
`SENSITIVITY_ONLY` per the protocol's Section II -- they exist to observe a
direction/shape of response and must never be promoted to a default model
parameter or reported as a new "solved" state. Any device-level quantity
this diagnostic reads out (an `RDS(on)` drop, a `Coss`-charging current, a
flying-capacitor voltage trajectory) is read directly from the already-
`EXTERNAL_DEVICE_DATA`/`NUMERICAL_IDEALIZATION`-classified model already in
the netlist; this experiment does not introduce any new device value.

## 5. Question this experiment is meant to answer

1. Does H1's peak-current-vs-`IL1_INIT` relationship stay linear (slope near
   the `~0.92 A/A` A36 implied) over a wide sweep, or does it also flatten
   toward zero sensitivity somewhere -- i.e., is H1 "solved" or merely
   "not yet pushed far enough to hit the same wall H2 already hit"?
2. What specific quantity differs between `TON1` (H1's fixed conduction
   window) and `TON2` (H2's) that could explain H2's near-zero sensitivity?
   At minimum, directly compare, across the two windows: the inductor
   current's instantaneous `di/dt` shape (linear ramp vs. bending/clipping),
   the driving flying-capacitor voltage (`VC1` during `TON1` vs `VC2` during
   `TON2`) for whether it stays flat or sags/rises measurably, the switch's
   own voltage drop (`Ron` IR drop) at the higher currents involved, and
   whether any other device or comparator event fires inside `TON2` that has
   no analogue inside `TON1` (e.g. something tied to phase 1's negative-
   current cutoff or ZVS admission that is temporally close to phase 2's
   window).
3. Based on (1) and (2), name the single most likely decisive factor (or
   state plainly that the evidence does not yet isolate one factor from the
   others, if that is the honest conclusion).

## 6. Success condition

This diagnostic "succeeds" if it produces a specific, evidenced answer to
Section 5's three questions -- not a converged residual. Concretely:

- A recorded `IL1_INIT` sweep wide enough to either observe flattening
  (report the `IL1_INIT` value where sensitivity visibly drops) or to state,
  with the tested range explicit, that no flattening was observed up to that
  range.
- A recorded, time-resolved comparison of at least the four quantities named
  in Section 5.2 for `TON1` vs `TON2`, from directly inspected `.raw` data
  (not re-derived from endpoint residuals alone).
- A named leading hypothesis for the decisive factor, with the specific
  evidence that supports it over the alternatives, or an explicit statement
  that the evidence remains ambiguous between two or more candidates.

## 7. Failure condition

- If the sweep or waveform trace cannot be obtained (e.g. a tooling problem),
  report that plainly rather than substituting a guess.
- If the evidence genuinely cannot distinguish between candidate causes,
  grade this `BLOCKED_BY_MISSING_DATA` or state the ambiguity explicitly --
  do not pick a "most plausible-sounding" cause without waveform evidence
  behind it. A wrong causal claim here is worse than an honest "still
  ambiguous," because later experiments would build on it.
- Prohibited: do not retune any locked parameter (Section 3) to make the
  sensitivity curve look cleaner; do not present a `SENSITIVITY_ONLY` sweep
  point as a new default value; do not silently narrow the `IL1_INIT` sweep
  range to avoid finding an inconvenient flattening point.

## 8a. Addendum: ideal-target vs. non-ideal-device tension (confirmed 2026-09-14)

A separate, real modeling tension exists alongside this diagnostic's own
finding, and the two must not be conflated. The `125 A` target itself comes
from 2024's lossless Eq. (2); once `RDS(on)=7 mOhm` (2025 device data) is
included, `L di/dt = V - RDS(on)*i` means a fixed starting current no longer
reaches the ideal lossless endpoint over one `TON`. This is quantitatively
confirmed here: `exp(-RDS(on)*TON/L) = exp(-0.007*16.6667e-9/1.4667e-9)
= 0.9235`, matching this diagnostic's measured H1 sensitivity
(`0.9219-0.9236 A/A`) almost exactly. `ILk_INIT` being a free, solved
variable (Section VIII, `NUMERICAL_IDEALIZATION`) rather than a value fixed
at the ideal formula's implied starting point (typically near `0 A`) is
precisely what absorbs this gap and lets the model still land on the
2024-defined `125 A` target despite using 2025's non-ideal `RDS(on)`. This is
a legitimate, already-used reconciliation, not a hidden error -- but it had
not previously been written down as the reason `ILk_INIT` needs to be
strictly positive rather than zero or paper-derived.

This tension is **not** the cause of A38's H2 peak-current shortfall. Section
6/7's own measurements show the `RDS(on)`-driven ramp shape is nearly
identical between H1 and H2 (gain and average `di/dt` within `0.6%` of each
other) -- the derating this addendum describes applies almost equally to
both phases and does not explain why one phase's shortfall can be tuned away
and the other's cannot. The actual cause is recorded in this experiment's own
`RESULTS.md` ("decisive factor" section): H2's *starting* current at
admission is pinned by the `L`-`Coss` resonant commutation, not chosen by
`IL2_INIT`, which is a categorically different mechanism from the
RDS(on)-derating described here.

## 8. What this experiment cannot prove

- Not a solve of A38's `PHYSICAL_BOUNDARY_FAIL`, and not a claim that the
  125 A target is or is not reachable for H2/H3 -- only a causal diagnosis of
  why the initial-current lever does not reach it.
- Not a claim about H3/H4 specifically (only H1 vs H2 are directly compared;
  if the same diagnostic quantities are easy to also read for H3, note them,
  but do not extrapolate a firm H3 conclusion from an H1/H2 comparison alone).
- Not a 2024-primary result; still on the 9% `CROSS_PAPER_EXTENSION` branch.
- Not evidence about zero-start, closed-loop regulation, efficiency, loss,
  thermal, EMI, or package behavior.
