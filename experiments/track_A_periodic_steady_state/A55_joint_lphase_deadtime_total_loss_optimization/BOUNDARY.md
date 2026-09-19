# A55 - joint LPHASE + dead-time total-loss optimization at P24's rated load, with EPC2067 (BOUNDARY)

Track: A (periodic steady-state reproduction). Main-line continuation
per explicit user direction 2026-09-19 ("对 你全部都考虑进来 系统级优化
再不行就没辙了" -- yes, take everything into account, do a system-level
optimization; if that still doesn't work, this path is exhausted).

## 0. Scope statement

This does not claim a P24/P25 reproduction. `A53` (GS61008T, `LPHASE`
alone) and `A54` (EPC2067, `LPHASE` alone) both held `dead_time_s` fixed
at `A48`'s own single-phase-optimized `2.15 ns`, inherited unchanged
from `A51`. This experiment adds `dead_time_s` as a SECOND free variable,
jointly optimized alongside `LPHASE`, using EPC2067 (`A54`'s own
better-performing device) at P24's rated `250 W`, and changes the
objective from "find where ZVS first turns on" to **"find the (`LPHASE`,
`dead_time_s`) pair that minimizes TOTAL loss (conduction + switching),
whether or not every phase individually achieves full natural ZVS"** --
a strictly more general and more correct optimization target than either
prior experiment used.

## 1. Why dead-time is a genuinely new, previously-untested lever here

`A48` found the single-phase `7.77%`-branch optimal dead time (`2.1516
ns`) is tied to that SPECIFIC resonant tank's own quarter-period
(`quarter-period ~ pi/2 * sqrt(L*C)`). `A53`/`A54` both changed `L`
and/or `C` substantially (`A54`'s own critical point: `L` down `57%`,
`C` up `~9x` relative to `A48`'s own tank) without ever re-deriving what
dead time THAT tank's own resonance actually needs. Estimated
quarter-period scaling: `sqrt((0.627/1.467)*(9300/1155)) ~= sqrt(0.427*8.05)
~= 1.85x` longer than `A48`'s own tank -- i.e. the `2.15 ns` dead time
inherited into `A54` may be too SHORT for its own new resonance, forcing
premature hard-switching timeouts before a natural crossing that a
longer window would have allowed. **This is a concrete, quantified
reason to expect dead-time re-optimization can reduce how far `LPHASE`
needs to be cut** -- not a speculative addition.

## 2. What is explicitly included in, and excluded from, "system-level"

Per explicit investigation before writing this boundary (not assumed):

**Included** (real data, already in this project):
- Conduction loss: `I_rms^2 * Ron`, EPC2067's own `1.55 mOhm`
  (`A54`'s own convention, unchanged).
- Capacitive switching loss: `0.5*C*V^2*f_sw`, computed PER PHASE based
  on whether that specific phase achieves natural ZVS or not at the
  candidate `(LPHASE, dead_time_s)` -- generalizing `A53`/`A54`'s own
  all-or-nothing measurement into a proper per-phase, continuous
  objective term (Section 3).
- `LPHASE` and `dead_time_s`, jointly optimized (Section 3).

**Explicitly excluded, with reasons checked, not assumed**:
- **Gate-drive loss**: no `Qg` (gate charge) data exists anywhere in
  this repository's own component libraries for ANY cataloged device
  (checked directly: `grep`-confirmed absent from every `.lib` file in
  `paper_locked/04_component_models/`). Cannot be estimated without
  inventing a number, which this project's own discipline forbids.
  **However, gate-drive loss depends only on gate charge, supply voltage
  and switching frequency -- NOT on drain-side ZVS/hard-switch
  behavior** -- so it is the SAME additive constant at every candidate
  point in this experiment's own search space, and therefore cannot
  change WHICH point is optimal or whether the net comparison against
  the nominal baseline is positive or negative. Its omission does not
  compromise this experiment's own conclusion, only the absolute
  (not relative) efficiency number.
- **Reverse-conduction ("third-quadrant") loss during dead time**:
  `GaN_reverse_conduction_ideal.lib` (already in this repository)
  confirms this is currently modeled as lossless. Unlike gate-drive
  loss, this term is NOT constant across candidates: a hard-switched
  phase spends its full dead-time window in reverse conduction, while a
  natural-ZVS phase spends less time in it (ending early at the
  crossing). **Its omission means this experiment's own switching-loss-
  eliminated numbers are more likely an UNDERCOUNT than an overcount** --
  i.e. achieving ZVS is probably being credited with LESS benefit here
  than it actually has, not more. Cannot be quantified without a real
  GaN third-quadrant voltage-drop value, which is not in this project's
  component libraries -- flagged as a genuine, concrete addition to a
  future `MINIMUM_INFORMATION_REQUEST.md`-style ask, not fabricated here.
- **Magnetic core loss**: requires real inductor/core material data
  (Steinmetz-type parameters) that does not exist anywhere in this
  project. Not estimated. A caveat, not a silent gap -- stated plainly
  in every result this experiment produces.
- **Population sweep** (`NHS`/`NLS` beyond EPC2067's own paper-specified
  `2`/`3` row): a legitimate further design axis, but explicitly OUT OF
  SCOPE here to keep this experiment tractable -- if the two-dimensional
  `(LPHASE, dead_time_s)` optimization already settles the question
  either way, a further population axis is not needed to answer it; if
  it does not settle the question, this is named as the natural next
  step, not silently left for later without saying so.

## 3. Method

1. Reuse `A51`'s own `a51_period_map.py` and `A54`'s own EPC2067 device
   parameters (`Ron=1.55 mOhm` uniform, `CH=3720 pF`, `CL=5580 pF`)
   read-only; do not modify `A51`/`A53`/`A54`'s own files.
2. **Define a proper scalar objective**: `total_loss(LPHASE, dead_time_s)
   = conduction_loss + sum over phases of (0 if that phase achieves
   natural ZVS else 0.5*C_phase*Vds_residual^2*f_sw)` -- evaluated at the
   Newton-converged fixed point for that `(LPHASE, dead_time_s)` pair
   (using continuation from a nearby already-solved point for numerical
   safety, per `A53`/`A54`'s own established practice).
3. **Search jointly** over `LPHASE` in `[A54's own critical 0.627 nH,
   nominal 1.4667 nH]` and `dead_time_s` in `[2.15 ns, 10 ns]` (the
   upper bound matching this project's own prior exploration range in
   `A48`/`A51`'s own robustness sweeps) for the minimum of
   `total_loss`. The exact search algorithm (coarse grid plus local
   refinement, coordinate descent, or another reasonable method) is an
   engineering choice, not a boundary constraint -- but report the
   search's own coverage/history plainly, and do not stop at a point
   that has not been checked against nearby alternatives (i.e. do not
   report a single lucky evaluation as "the optimum" without at least a
   local neighborhood check).
4. **At the found optimum**, run the full per-phase step-size-converged
   ZVS verification (`A50`/`A51`/`A53`/`A54`'s own established
   discipline) and report every phase's own verdict individually.
5. **Report the final total-loss comparison against the nominal-`L`/
   nominal-dead-time EPC2067 baseline** (already established in `A54`:
   conduction `26.94 W`, switching `17.98 W`, total `44.92 W`) and
   against `A54`'s own already-found `LPHASE`-only critical/margin
   points -- three-way comparison: nominal, `A54`'s `LPHASE`-only
   optimum, this experiment's joint `(LPHASE, dead_time_s)` optimum.

## 4. Provenance of every value

| Value | Source | Category |
|---|---|---|
| EPC2067 device parameters | `A54`'s own already-verified values | `EXTERNAL_DEVICE_DATA`, unchanged |
| `dead_time_s` search range `[2.15, 10] ns` | Lower bound: `A48`'s own single-phase optimum (no longer assumed correct for this tank, Section 1). Upper bound: this project's own prior exploration range (`A51`'s robustness sweeps already tested `10 ns`) | `SENSITIVITY_ONLY` |
| `LPHASE` search range `[0.627, 1.4667] nH` | Lower bound: `A54`'s own found critical point (further reduction cannot help, since switching loss is already ~0 there). Upper bound: P24's own nominal value | Bounds inherited from `A53`/`A54`'s own already-published results |
| `module_power_w=250 W` | P24's own rated load | `P24_EXPLICIT` |
| Everything else | See `A50`/`A51`/`A53`/`A54` `BOUNDARY.md` for original provenance | unchanged |

## 5. Success/failure conditions

- **A joint optimum is found with total loss BELOW the nominal
  baseline's `44.92 W`** (i.e. achieving full or partial ZVS this way
  is a genuine net win once dead-time is also optimized, unlike `A53`/
  `A54`'s own `LPHASE`-only results): a positive, actionable finding --
  report the specific `(LPHASE, dead_time_s)` pair and by how much it
  beats nominal, and note this would be the first net-positive ZVS
  balance found in this whole `A53-A55` chain.
- **The joint optimum is still above nominal, but meaningfully better
  than `A54`'s own `LPHASE`-only critical point**: report the
  improvement plainly -- still not a full "yes," but a genuinely
  informative narrowing of the gap, consistent with `A54`'s own already-
  observed pattern (each added degree of freedom has made the deficit
  smaller, not larger).
- **The joint optimum is no better than `A54`'s own `LPHASE`-only
  result** (dead-time re-optimization turns out not to matter as much as
  Section 1's estimate suggested): report this plainly -- per the user's
  own framing, if THIS system-level attempt still does not find a net
  win, that is treated as this specific investigative path (parameter
  retuning within the existing topology/device catalog) being exhausted,
  not as a reason to keep expanding the search further without a fresh,
  separately-justified boundary decision.
- Every phase current must stay within `+/-250 A` throughout the ENTIRE
  search (not just the reported optimum) -- `A54`'s own search already
  came within `7%` of this bound at its own most aggressive point;
  report explicitly if this search approaches or exceeds that margin
  anywhere.

## 6. What this experiment cannot prove

- Does not include gate-drive, reverse-conduction, or core loss (Section
  2) -- explicitly flagged, not fabricated.
- Does not sweep device population (`NHS`/`NLS`) beyond EPC2067's own
  paper-specified row -- named as the natural next axis if this
  experiment's own two-dimensional result does not settle the question.
- A positive result would still not constitute a P24/P25 reproduction
  claim, nor a hardware-validated efficiency number -- it would be a
  theoretical best-case bound given this project's own partial loss
  model and the two devices already cataloged.
- Does not modify `src/scb_ivr/`, or A37/A42/A45/A48/A50/A51/A52/A53/
  A54's own committed files.
- Does not include a SPICE cross-check of the found optimum -- the same
  standing follow-up `A53`/`A54` already deferred, now applying to
  whichever `(LPHASE, dead_time_s)` point this experiment recommends.
