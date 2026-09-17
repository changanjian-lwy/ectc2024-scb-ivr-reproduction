# R04E18 - locating the runaway/safe `Tramp` boundary with the divider present (BOUNDARY)

## 1. Parent and why this experiment exists

**R04E17** (`experiments/track_B_zero_start_extension/
R04E17_divider_ramp_factorial_isolation/`) established, with R03A's own
passive-divider network reintroduced (at the corrected `CDIV=300 uF`/
`Cfly=3 uF`), that a fast `Vin` ramp (`Tramp=1 us`) reproduces R03A's own
catastrophic current runaway (`813-1046 A`) while a `68.61x`-slower ramp
(`Tramp=68.61 us`, Roberts' own `30x`-margin value) avoids it entirely
(`141-155 A`). **Only these two `Tramp` points were tested; the actual
transition between "runs away" and "safe" is completely unmapped** --
R04E17's own Section 7 explicitly flags this as not established ("whether
the runaway/no-runaway boundary sits closer to `1 us` or closer to
`68.61 us`... is not tested by this two-point design and would need a
further, separately-scoped sweep").

Per explicit user direction 2026-09-17 (approving the first, lowest-cost
item of `CONSOLIDATED_FINDINGS_2026-09-16.md`'s updated priority list),
this experiment maps that boundary.

## 2. What changed relative to R04E17, exactly

**No mechanism, topology, or fixed-parameter change of any kind.** This
experiment reuses R04E17's own byte-level-faithful netlist (R04E16's
fixed-timing four-phase power stage + R03A's divider network reintroduced
at `CDIV=300 uF`, `Cfly=3 uF`, `TSTART=0`, `LPHASE=1.4666667 nH`,
`solver=alt cshunt=1e-15 plotwinsize=0`, `TMAX=50 ps`) completely
unchanged. The ONLY thing swept is `Tramp` itself, at three NEW
intermediate points between R04E17's own already-tested `1 us`
(runaway) and `68.61 us` (safe) endpoints.

## 3. Swept grid

Three new cells, `Tramp` in `{5, 22.87, 40} us`, `TSTOP=Tramp+300 us`
each (matching R04E16/R04E17's own convention):

- `Tramp=5 us`: a round, near-the-fast-end point, roughly `5x` slower
  than R04E17's own runaway cell.
- `Tramp=22.87 us`: NOT an arbitrary new number -- this is R04E16's own
  already-derived `10x`-margin value at `Cfly=3 uF`
  (`ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md` Section 2), already used
  and reported (divider-ABSENT case only, R04E16's own `e16_g2_f3_t22p87`
  cell) but never tested with the divider PRESENT. Reusing it here keeps
  this experiment's own new grid tied to an already-justified value
  rather than an arbitrarily chosen one.
- `Tramp=40 us`: a round, near-the-safe-end point, between R04E16's own
  `10x` (`22.87 us`) and `30x` (`68.61 us`) margin values, filling that
  gap.

Together with R04E17's own two already-completed endpoints, this gives a
5-point picture of the transition (`1, 5, 22.87, 40, 68.61 us`) without
committing to a full continuous bisection search, which would require
many more sequential multi-hour LTspice runs than is practical in one
pass. If this 5-point picture leaves the transition still coarsely
localized, a further-refined follow-up remains available.

## 4. What did not change

Everything else, copied byte-for-byte from R04E17's own two netlists:
four-phase power-stage connectivity, `TSTART=0` fixed-timing gate
B-sources, `LPHASE=1.4666667 nH`, `CFLY=3 uF`, `COUT=4.672 mF`,
`RLOAD=Vout^2/Pout`, ideal `SWI` switch model, `RLDAMP=1u`,
true-zero-energy IC (`UIC`), `TMAX=50 ps`, `solver=alt cshunt=1e-15
plotwinsize=0`, R03A's own divider-network topology (`CIN1-4`/
`RLEAK1-4`/`DPC1-3`, `CDIV=300 uF`, `IPEC2018 LPAR=5n`/`RPAR=10m`,
`RLEAK=1G`, ideal diode model).

## 5. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `Tramp=5 us` | New for this experiment: a round point near the fast/runaway end | `SENSITIVITY_ONLY` |
| `Tramp=22.87 us` | R04E16's own already-derived `10x`-margin value at `Cfly=3 uF` (`ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`), reused here at a new (divider-present) condition | `CROSS_PAPER_EXTENSION`, inherited |
| `Tramp=40 us` | New for this experiment: a round point filling the gap between R04E16's own `10x`/`30x` margin values | `SENSITIVITY_ONLY` |
| Everything else | See R04E17 `BOUNDARY.md` Section 5 for original provenance | unchanged |

No new paper-sourced, cross-paper, or external-device data is
introduced. This experiment only adds grid resolution to an already-
established, already-justified `(divider-present, Cfly=3uF)` parameter
line.

## 6. What question this experiment is meant to answer

Where, within the `1-68.61 us` `Tramp` range, does the transition from
"reproduces R03A's runaway" to "avoids it" actually occur, with the
divider present? Is it a sharp threshold (most of the range on one side
or the other) or a gradual one (intermediate `Tramp` values show
intermediate, partial current elevation)?

## 7. Success/failure conditions

Every outcome is informative, per Ground Rule 7 and R04E17's own
precedent:

- If all three new cells show runaway-scale current (`IL_max`
  approaching or exceeding R03A's own `563-884 A` range, or the `+/-250 A`
  safety bound): the threshold sits above `40 us`, closer to R04E17's own
  `68.61 us` safe point than previously assumed.
- If all three avoid runaway (stay comfortably under `+/-250 A`,
  comparable to R04E17's own `154.73 A` safe cell): the threshold sits
  below `5 us`, meaning even a modest ramp is sufficient and R04E17's own
  `1 us` runaway point is closer to a sharp cliff edge than a gradual
  region.
- If the three show a mix (e.g. `5 us` and `22.87 us` still show runaway,
  `40 us` does not, or any other split): this directly localizes the
  transition to a specific sub-interval, the primary goal of this
  experiment.
- A genuinely GRADUAL transition (partial current elevation at
  intermediate points, neither clearly "runaway" nor clearly "safe") is
  itself a reportable finding, not an ambiguous non-result -- report the
  actual `IL_max` trend across all 5 points (including R04E17's own two)
  plainly.

## 8. What this experiment cannot prove

- It does not achieve a precise, continuous threshold value -- only a
  5-point picture. A further bisection within whichever sub-interval
  this experiment localizes the transition to would be needed for a
  precise value, if one is wanted.
- It does not test any `Cfly` value other than `3 uF` -- whether the
  threshold's absolute value (in `us`) scales with `Cfly` the way the
  underlying resonance-frequency model would predict is not addressed
  here.
- It does not address `Vout`/handoff bootstrap beyond what R04E16/R04E17
  already report.
- It does not modify, overwrite, or invalidate R04E16's or R04E17's own
  committed results.
- A P24 reproduction claim of any kind remains out of scope, the same
  standing Track-B limitation as every other experiment in this lineage.
