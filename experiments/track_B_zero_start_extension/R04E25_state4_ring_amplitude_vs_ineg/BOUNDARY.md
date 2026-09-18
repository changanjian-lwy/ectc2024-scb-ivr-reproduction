# R04E25 - does state 4's resonant ring amplitude scale with I_NEG, and by how much is it short of ZVS? (BOUNDARY)

## 0. Scope statement (unchanged from R04E21-R04E24, restated)

Same standing limitation: **this does not test, claim, or imply P24
periodic steady-state reachability**, and does NOT attempt a four-phase
handoff. Direct, minimal follow-up to R04E24's own result, still a
phase-1-only diagnostic.

## 1. Parent and why this experiment exists

**R04E24** used `NEG_FRAC=1.6%` (`I_NEG=2.0 A`, chosen with margin below
R04E23's own observed `-2.215 A` natural ceiling) and, for the first
time in this chain, got the machine into state 4
(`COMMUTATE_HIGH_TO_ZVS`). There, `V(vin,xmod:a1)` rings between
`9.66 V` and `14.16 V` (damping toward `~11.92 V`) and never gets
anywhere close to the `<=0 V` ZVS threshold -- closest approach `9.66 V`,
confirmed directly from the `.raw` trace during the state-4 window.

A single back-of-envelope estimate (not yet SPICE-confirmed) suggests
this ring's voltage amplitude may scale roughly linearly with `I_NEG`
(standard for a fixed-impedance LC tank, since stored energy
`0.5*L*I_NEG^2` sets the swing), which would imply closing the observed
`~11.9 V` gap needs `I_NEG` on the order of `~10.6 A` -- about `5x`
above R04E23's own observed natural ceiling for this specific
bootstrapped operating point (`~2.215 A`). **This experiment tests that
scaling directly with real SPICE data, rather than relying on a
single-point extrapolation**, by sweeping `I_NEG` across the full
reachable range and measuring the resulting ring depth at each point.

## 2. What changed relative to R04E24, exactly

- **`NEG_FRAC` swept across four new values** (plus R04E24's own
  already-committed `1.6%` reused by reference), spanning the reachable
  range from near-zero up to just under R04E23's own observed natural
  ceiling (`2.215 A`) at `I_LIMIT=125 A`:

| Cell | `NEG_FRAC` | `I_NEG` | Note |
|---|---:|---:|---|
| (reused) `r04e24_neg1p6pct_t100us` | `1.6%` | `2.0 A` | already committed, cited not re-run |
| `r04e25_neg0p4pct` | `0.4%` | `0.5 A` | near-minimum reachable point |
| `r04e25_neg0p8pct` | `0.8%` | `1.0 A` | |
| `r04e25_neg1p2pct` | `1.2%` | `1.5 A` | |
| `r04e25_neg1p72pct` | `1.72%` | `2.15 A` | just under R04E23's own `2.215 A` natural ceiling, largest safely-reachable point |

  Each new value gives one more `(I_NEG, ring-depth)` pair to fit the
  scaling relationship, bracketing from near-zero up to the practical
  maximum this specific bootstrapped state can reach at all (per R04E23).
- Everything else -- `I_LIMIT=125 A`, `TSTOP=100 us`, phase 1's own
  bootstrapped initial conditions, `CFLY=3 uF`, phases 2-4's own
  hardcoded R04E3 configuration -- copied UNCHANGED from R04E24's own
  already-verified netlist, only `NEG_FRAC` edited per cell.

## 3. What did not change

Everything except `NEG_FRAC` -- copied byte-for-byte from R04E24's own
`r04e24_neg1p6pct_t100us.cir` for each new cell.

## 4. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `NEG_FRAC` in `{.004, .008, .012, .0172}` | New for this experiment: chosen to bracket the reachable `I_NEG` range (near-zero to just under R04E23's own observed `2.215 A` natural ceiling) with roughly even spacing, not arbitrary guesses | `SENSITIVITY_ONLY`, derived from this project's own prior committed results (R04E23's ceiling), not external or paper-sourced |
| The linear-amplitude-vs-current hypothesis being tested | Standard LC-resonant-tank first principles (stored energy `0.5*L*I^2`, voltage amplitude `I*sqrt(L/C)` for a fixed impedance), applied here as an engineering estimate, not a paper-sourced claim | `NUMERICAL_IDEALIZATION` -- explicitly a hypothesis to be tested, not assumed true |
| Everything else | See R04E24 `BOUNDARY.md` for original provenance | unchanged |

No new paper-sourced, cross-paper, or external-device data is
introduced.

## 5. What question this experiment answers

Does the depth of state 4's resonant ring (how close `V(vin,xmod:a1))`
gets to `0 V`) scale linearly (or otherwise predictably) with `I_NEG`
across the full reachable range? If so, by extrapolation, how much
larger would `I_NEG` need to be to actually reach `0 V` and clear ZVS --
and how does that compare to the `~2.215 A` ceiling this specific
bootstrapped state can naturally reach (per R04E23), i.e. is the shortfall
large (confirming an energy-insufficiency conclusion) or small (suggesting
a modest additional push might suffice)?

## 6. Success/failure conditions

- **Ring depth scales linearly (or near-linearly) with `I_NEG`, and
  extrapolation confirms a large (multi-x) shortfall at the natural
  ceiling**: confirms the diagnosed energy-insufficiency conclusion
  cleanly -- closing this stall via `I_NEG`/`I_LIMIT` tuning alone is
  infeasible for this bootstrapped operating point; a circuit-level
  change (e.g. larger `LPHASE`) would be required, out of this
  experiment's own minimal scope.
- **Ring depth scales non-linearly, or the gap closes faster than
  linear extrapolation suggests**: report plainly -- would mean the
  single-point extrapolation was misleading and a real ZVS event might
  be reachable within (or just outside) the natural `I_NEG` ceiling;
  motivates a closer look near the ceiling, not a stop.
- **One of the swept cells actually reaches ZVS (`state_final=5`)**:
  directly and cleanly confirms R04E21's original hypothesis after all
  -- report immediately and prominently, this would reverse R04E24's
  own conclusion.
- Phase 1's own current must stay within `+/-250 A` throughout all five
  cells (R04E24's own single cell already confirmed `125.39 A` max under
  the same `I_LIMIT=125 A`; not expected to differ materially).

## 7. What this experiment cannot prove

Same list as R04E21-R04E24, unchanged: does not test P24 periodicity,
does not test four-phase handoff, does not validate R04E3 as "the" P24
controller, does not modify any other experiment's own committed
results, no P24 reproduction claim of any kind. If this experiment
confirms the energy-insufficiency conclusion, it does NOT identify what
specific circuit-level change (larger `LPHASE`, different state-3
duration, etc.) would fix it -- that would be a separate, new experiment
requiring its own explicit boundary, not performed here. This is also
intended as a stopping point for this minimal-scope sub-investigation if
it confirms the negative result -- further open-ended parameter tuning
beyond this sweep should not proceed without a fresh, explicit boundary
decision.
