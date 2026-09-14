# A44 H2 admission-current upstream-state sensitivity diagnostic boundary

Track: A (periodic steady-state reproduction). Diagnostic only: it measures,
it does not solve. No free variable is fitted to a target; the deliverable
is a sensitivity table and a causal conclusion, not a converged residual.

## 1. Parent experiment

A39 (`A39_h1_h2_peak_sensitivity_diagnostic`) found that H2's admission
current at turn-on is pinned near `-1.29 A` by the `L`-`Coss` resonant
commutation and is nearly insensitive to `IL2_INIT` itself
(`~0.014 A` moved over a `2 A` probe). That test held every *other* state
variable fixed at A37/A38's seed while sweeping only `IL2_INIT`. It never
tested whether the six *other* coupled state variables --
`IL1_INIT`, `IL3_INIT`, `IL4_INIT`, `VC1_INIT`, `VC2_INIT`, `VC3_INIT` --
also leave H2's admission current pinned, or whether one or more of them
actually moves it. The user asked, correctly, whether the "pinning" finding
is genuinely robust or an artifact of only having varied one variable while
the real sensitivity lives elsewhere in the coupled state.

## 2. What changed relative to the parent

A39 varied exactly one variable (`IL2_INIT`) with the rest of the seven-state
vector frozen at A38's values. A44 keeps `IL2_INIT` frozen at A38's own
value and instead perturbs each of the *other six* state variables
one at a time (never jointly), holding all others -- including `IL2_INIT` --
fixed, and measures the same two outputs A39 used: H2's admission current
and H2's admission time. This is a direct, one-variable-at-a-time extension
of A39's method to the remaining coordinates of the same seven-state vector,
not a new method.

## 3. What did not change

Topology, device `Coss`, ideal reverse-conduction clamp, inductor
`1.4667 nH`, each phase's fixed `TON=16.6667 ns`, nominal phase-slot origins,
the `9%` labelled P25 branch, the ideal `1 V` output clamp, and timestep --
all identical to A39/A38/A37/A36/A35/A27. The netlist and baseline seven-state
seed are A38's own solved/seed state (`IL1_INIT=5.2947`,
`IL2_INIT=21.205095337`, `IL3_INIT=56.3206` [A38's solved value],
`IL4_INIT=84.1447433786`, and A37's `VC1_INIT`/`VC2_INIT`/`VC3_INIT`).

## 4. Provenance of the values used

All perturbation values are `SENSITIVITY_ONLY` per the protocol's Section II
-- they exist to observe a direction/magnitude of response and must never be
promoted to a default model parameter or reported as a new "solved" state.

## 5. Question this experiment is meant to answer

Holding `IL2_INIT` fixed at A38's value, does perturbing any one of
`IL1_INIT`, `IL3_INIT`, `IL4_INIT`, `VC1_INIT`, `VC2_INIT`, `VC3_INIT` (each
independently, by a small step appropriate to its unit -- roughly `+-1-2 A`
for currents, `+-0.2-0.5 V` for capacitor voltages) measurably move H2's
admission current away from its `~-1.29 A` pinned value, or its admission
time away from A38's solved `~50 ns`? If so, which variable(s) have the
largest effect, and by how much per unit change (report a sensitivity, same
units as A39's `A/A` figures, e.g. `A` of admission-current change per `A` or
`V` of perturbation)? If none do, that strengthens A39's "pinned by local
resonant commutation, not by upstream state" conclusion into "pinned
regardless of the full seven-state neighborhood tested," not just against
its own initial-current knob.

## 6. Success condition

A complete one-at-a-time sensitivity table across all six variables, each
with: the perturbation applied, the resulting admission-current change, and
the resulting admission-time change, directly read from `.raw` waveforms
(not inferred). "Success" here means a complete, honestly reported table --
it does not require finding a variable that moves the pinned value; a table
showing uniform insensitivity is itself a valid, useful, complete result.

## 7. Failure condition

- If a waveform trace or sweep cannot be obtained for a given variable,
  report that specific gap plainly rather than omitting the row or guessing.
- If one or more variables DO move the admission current substantially,
  do not fold that into a vague "some sensitivity exists" -- name the
  variable(s), the magnitude, and reconsider whether A39's "pinning" framing
  needs a caveat (it would not invalidate A39's own `IL2_INIT`-specific
  finding, but it would mean the full picture is "pinned against its own
  starting current, but movable by some other coupled state").
- Prohibited: do not retune any locked parameter to make the sensitivity
  table look cleaner; do not present a `SENSITIVITY_ONLY` perturbation point
  as a new default value.

## 8. What this experiment cannot prove

- Not a solve of A38's `PHYSICAL_BOUNDARY_FAIL`, and not a new attempt to
  reach 125 A or close the 200 ns period.
- Not a joint/coupled-perturbation study (only one variable moves at a
  time); a variable that shows no effect in isolation could still interact
  jointly with another -- that would require a separate, explicitly
  joint-perturbation experiment, not this one.
- Not a 2024-primary result; still on the 9% `CROSS_PAPER_EXTENSION` branch.
- Not evidence about zero-start, closed-loop regulation, efficiency, loss,
  thermal, EMI, or package behavior.
