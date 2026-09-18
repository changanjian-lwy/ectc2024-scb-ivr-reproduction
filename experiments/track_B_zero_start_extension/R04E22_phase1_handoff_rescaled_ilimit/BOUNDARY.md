# R04E22 - rescaling I_LIMIT/I_NEG to P24's own real current scale (BOUNDARY)

## 0. Scope statement (unchanged from R04E21, restated)

Same standing limitation as R04E21: **this does not test, claim, or
imply P24 periodic steady-state reachability**, and it does NOT attempt
a four-phase handoff -- phases 2-4 stay at R04E3's own hardcoded,
single-phase-isolation configuration. This is a direct, narrowly-scoped
follow-up to R04E21's own negative result, testing one specific,
diagnosed hypothesis.

## 1. Parent and why this experiment exists

**R04E21** fed R04E17's own real bootstrapped state (`VC1=35.86 V`,
`IL1=75.97 A`) into R04E3's own event-gated controller and found the
SAME stall R04E3/R04E5 already documented from zero energy: permanent
parking at state `COMMUTATE_HIGH_TO_ZVS`, `T_HIGH_SIDE_ZVS` never fires.
The bootstrapped current/voltage magnitude alone did NOT avoid the
stall.

**Diagnosed cause, to be tested here, not assumed**: R04E3's own
`I_LIMIT=10 A` and `NEG_FRAC=.02` (giving `I_NEG=I_LIMIT*NEG_FRAC=0.2 A`)
are leftover values sized for TRUE ZERO-ENERGY startup's own tiny first-
pulse scale (R04E9's own dissertation-independent finding: phase 1's
first pulse from zero energy is `~0.93-1 ns`, reaching only a few
amps). R04E21 fed in a bootstrapped state at `~76 A` -- vastly larger
than `I_LIMIT=10 A` -- but the STATE MACHINE's own `I_NEG=0.2 A` negative-
current TARGET (state 3's exit condition, `I(L1)<=-I_NEG`) is unchanged,
so state 3 exits again almost immediately once the current crosses only
`-0.2 A`, storing only a tiny amount of magnetic energy
(`E=0.5*L*I_NEG^2`) for the state-4 resonant ZVS ring -- regardless of
how large the bootstrapped starting current was. **This experiment tests
whether rescaling `I_LIMIT`/`I_NEG` to P24's own real, already-locked
current scale (not an arbitrary new guess) lets the ZVS event actually
occur.**

## 2. What changed relative to R04E21, exactly

- **`I_LIMIT` corrected from R04E3's own `10 A` to P24's own LOCKED
  Table-1 peak current, `125 A`** (`SOURCE_COVERAGE_MATRIX.md`, already
  `LOCKED`, the same value `CFLY_FIRST_PRINCIPLES_ESTIMATE.md` and every
  other P24-operating-point derivation in this project uses). This
  changes state `ENERGY`'s own exit condition to `I(L1)>=125 A` --
  since the bootstrapped starting current (`~76 A`) is now BELOW this
  corrected `I_LIMIT`, state 0 will genuinely dwell (charging phase 1's
  current further via the high-side conducting) rather than exiting
  near-instantly as it did in R04E21, before proceeding through the
  rest of the chain. This is a MORE physically meaningful reading of
  what "`I_LIMIT`" should represent (P24's own designed peak current)
  than R04E3's own arbitrary small zero-start-era default.
- **`NEG_FRAC` swept across two values, both already-established,
  already-labelled candidates from this project's own Track-A lineage
  -- NOT new guesses**:
  - `NEG_FRAC=.02` (`2%`): "Main P24 branch" convention
    (`CURRENT_ASSUMPTION_CROSSCHECK.md`'s own "Negative current" row).
  - `NEG_FRAC=.0777` (`7.77%`): A42's own found LOCAL, single-phase
    natural-ZVS threshold (same row; A43's own precedent for citing the
    upper end of the `7.76-7.77%` range as a single test value).
  With `I_LIMIT=125 A`, these give `I_NEG=2.5 A` and `I_NEG=9.7125 A`
  respectively -- both far larger than R04E21's own `0.2 A`, testing the
  diagnosed energy-scale hypothesis directly.
- Everything else (phase 1's own bootstrapped initial conditions
  `VC1_IC=35.85894624845418 V`, `IL1_IC=75.96527862548828 A`, `CFLY=3 uF`,
  all other parameters, phases 2-4's own hardcoded R04E3 configuration)
  copied UNCHANGED from R04E21's own already-verified netlist.

## 3. What did not change

- R04E17's own bootstrapped source state and how it was extracted --
  unchanged, reused verbatim from R04E21 (not re-extracted).
- `CFLY=3 uF` (the R04E21 correction from R04E3's own `53.8 uF`) --
  unchanged.
- The 5-state `.machine` structure itself, its `.rule` transition
  CONDITIONS (only the `I_LIMIT`/`I_NEG` VALUES plugged into those
  conditions change, not the conditions' own form) -- unchanged.
- Phases 2-4's own hardcoded gate drives and zero-energy initial
  conditions -- unchanged, same explicit scope limit as R04E21 Section 4.
- `LPHASE`, `COUT=4.672 mF`, GS61008T device data, `TRAIL=10p`,
  `solver=alt cshunt=1e-15`, `TSTOP=20 us` -- unchanged from R04E21/R04E3.

## 4. Swept grid

Two cells, `I_LIMIT=125 A` fixed, `NEG_FRAC` in `{.02, .0777}`:

| Cell | `NEG_FRAC` | `I_NEG` | Source of this value |
|---|---:|---:|---|
| `r04e22_neg2pct` | `2%` | `2.5 A` | P24's own "main branch" convention |
| `r04e22_neg7p77pct` | `7.77%` | `9.7125 A` | A42's own found local natural-ZVS threshold |

## 5. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `I_LIMIT=125 A` | P24's own `LOCKED` Table-1 peak current (`SOURCE_COVERAGE_MATRIX.md`) | `P24_EXPLICIT` |
| `NEG_FRAC=.02` | `CURRENT_ASSUMPTION_CROSSCHECK.md`'s own "main P24 branch" convention, already used throughout Track A (A24-A48) and R04E3 itself | `P24_EXPLICIT`-adjacent (P24's own text states `1-2%`; this project's own standing choice is `2%`) |
| `NEG_FRAC=.0777` | A42's own found LOCAL single-phase natural-ZVS threshold, `7.76-7.77%` (A43's own precedent for testing the upper bound as one value) | `SENSITIVITY_ONLY`, inherited from A42/A43, explicitly NOT the full-four-phase-machine threshold (`9%`) per the standing warning in `CURRENT_ASSUMPTION_CROSSCHECK.md` |
| Everything else | See R04E21 `BOUNDARY.md` for original provenance | unchanged |

No new paper-sourced, cross-paper, or external-device data is
introduced -- both `I_LIMIT` and both `NEG_FRAC` values are reused,
already-labelled quantities from elsewhere in this project, redeployed
here for a new purpose (as R04E21's own diagnosed correction), not newly
invented.

## 6. What question this experiment answers

Does correcting `I_LIMIT`/`I_NEG` to P24's own real current scale (rather
than R04E3's own leftover zero-start-era small values) let the high-side
ZVS event (`V(vin,a1)<=0`, state 4->5) actually occur, when phase 1
starts from the SAME R04E21 bootstrapped state that failed under the
old, undersized `I_NEG=0.2 A`? Does the answer depend on WHICH
already-established `NEG_FRAC` value is used (`2%` vs `7.77%`)?

## 7. Success/failure conditions

- **Stall avoided at one or both `NEG_FRAC` values**: state 5 reached.
  Directly confirms the diagnosed energy-scale hypothesis -- the ORIGINAL
  `I_NEG=0.2 A` was insufficient, not the bootstrap itself.
- **Stall persists at both values**: the diagnosed hypothesis is wrong,
  or incomplete -- the blocking mechanism is something else (e.g. the
  specific voltage/current TRAJECTORY at the handoff instant, not just
  the target magnitudes used downstream). A genuinely informative
  negative result, reported plainly, not forced.
- **Different outcome at the two `NEG_FRAC` values** (e.g. `7.77%` works,
  `2%` doesn't, or vice versa): directly informative about how much
  negative-current margin this specific handoff needs -- report the
  split plainly.
- Phase 1's own current must stay within `+/-250 A` throughout (R04E21's
  own bootstrapped state, `IL1_IC=75.97 A`, already sits well under this;
  the larger `I_LIMIT=125 A` charging target increases the risk somewhat
  and must be checked explicitly, not assumed safe).

## 8. What this experiment cannot prove

Same list as R04E21 Section 8, unchanged: does not test P24 periodicity,
does not test four-phase handoff, does not validate R04E3 as "the" P24
controller, a positive result would not establish what happens past
state 5 (R04E3's own deliberate stopping point), does not modify any
other experiment's own committed results, no P24 reproduction claim of
any kind.
