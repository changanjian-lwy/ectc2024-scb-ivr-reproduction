# R04E17 result - factorial isolation of "divider removed" vs. "Vin ramped"

## 1. Outcome, stated first

**The clean, third pattern of BOUNDARY.md Section 7 occurred: the
fast-ramp/divider-present cell (`e17_div_f3_t1`, `Tramp=1 us`) shows
genuine runaway-scale current, while the slow-ramp/divider-present cell
(`e17_div_f3_t68p61`, `Tramp=68.61 us`) does NOT.** With R03A's own
divider-plus-diode precharge network reintroduced (at the corrected
`CDIV=300 uF`) into an otherwise-unchanged R04E16 netlist, the `Vin` ramp
now measurably matters: the fast-ramp cell's phase currents reach
`813-1046 A` (`IL1_max=813.14 A`, `IL2_max=884.90 A`, `IL3_max=877.84 A`,
`IL4_max=1046.42 A` -- all four phases exceed the `+/-250 A` safety
bound, and the magnitude is in the same range as R03A's own originally
diagnosed runaway, `563-884 A`), while the slow-ramp cell's phase
currents stay at `140.8-154.7 A`, comfortably inside the bound and close
to R04E16's own divider-ABSENT cells' own currents at the same `Tramp`
values (`150.07 A` and `86.94 A` respectively).

This directly answers the question R04E16 could not (BOUNDARY.md Section
6): with the divider physically present, a fast `Vin` ramp reproduces
R03A's own catastrophic mismatch, and a slow ramp avoids it -- the ramp
mechanism itself, not merely "PWM active from `t=0`" or "no divider",
does real protective work once the divider's precharge is actually in
the circuit. See Section 5 for what this does and does not establish
beyond this specific two-cell comparison.

## 2. Pilot verification (BOUNDARY.md's required pilot-first step)

Before committing to the two full multi-hour runs, a truncated-`TSTOP`
copy of `e17_div_f3_t1` (`TSTOP=Tramp+2 us` instead of `Tramp+300 us`,
everything else byte-identical) was run in isolation. It completed in
`11.5 s` with a full, well-formed `.meas` block and no LTspice topology
error -- confirming the grafted `CIN1-4`/`RLEAK1-4`/`DPC1-3` divider
network attaches cleanly to the existing `a1`/`a2`/`a3` power-stage
nodes with no floating or duplicate nodes, before the two real cells
(Section 3) were run. (This pilot file was not committed; it exists only
as a verification step, per BOUNDARY.md's own pilot-first requirement
for a genuine circuit-topology change.)

## 3. The two new cells, run strictly sequentially

Both cells were run one at a time, on real LTspice
(`tools/ltspice_runner.sh`), never concurrently, per this experiment's
own hard operational constraint (R04E16's own RESULTS.md Section 3b
measured a `~20x` throughput collapse from concurrent runs on this
machine):

1. `e17_div_f3_t1` (`Tramp=1 us`, `TSTOP=301 us`) was started first and
   run to completion before `e17_div_f3_t68p61` was ever launched.
   `.log` confirms `Total elapsed time: 1203.948 seconds` (`~20.1 min`)
   and a full `.meas` block (all 27 measurements present).
2. `e17_div_f3_t68p61` (`Tramp=68.61 us`, `TSTOP=368.61 us`) was only
   started after `e17_div_f3_t1`'s own `.log` had already confirmed
   completion. `.log` confirms `Total elapsed time: 1641.488 seconds`
   (`~27.4 min`) and a full `.meas` block.

No LTspice process for either cell was ever running while the other's
process was still active (directly verified via `ps`/`pgrep` immediately
before each launch).

## 4. Solver-corruption fingerprint check (both new cells)

Per this project's own standing discipline (R04E16 `RESULTS.md` Section
3a) and the task's explicit instruction, both new cells' raw `.raw`
binary traces were directly, byte-level parsed (not merely trusted from
the `.log` summary) and checked for the two-part corruption signature
R04E16 documented: (a) near-duplicate/non-monotonic timestamps
consistent with solver-retry chatter, and (b) the independent,
state-independent `V(vin)` PWL source itself reading a value impossible
for its own commanded ramp.

- **`e17_div_f3_t1.raw`**: `6,728,222` points parsed in full. Zero rows
  with `dt<=0` (no non-monotonic or exactly-duplicate timestamps); the
  smallest positive inter-sample spacing observed is `~4.07e-20 s`,
  consistent with legitimate fine adaptive substepping around switching
  edges at this `TMAX=50 ps` resolution, not chatter. `V(vin)` never
  deviated from its expected commanded PWL value by more than the
  generous `+/-5%`/`-0.5 V` tolerance checked, at any of the `6.7`
  million points -- in particular it never showed anything resembling
  R04E16's own documented `-20885 V`/`5.33e24 V` corruption values.
- **`e17_div_f3_t68p61.raw`**: `8,208,737` points parsed in full. Zero
  rows with `dt<=0`. `V(vin)` anomaly count: `0`.

**Conclusion: the solver-corruption fingerprint is absent from both new
cells.** The `solver=alt cshunt=1e-15 plotwinsize=0` fix (baked into
both netlists unchanged from R04E16, per BOUNDARY.md Section 4) continues
to work correctly for this now-modified netlist (power stage + divider
network combined). The large currents reported for `e17_div_f3_t1`
(Section 5) are directly confirmed as a real transient-current result
from the raw trace, not a numerical artifact.

## 5. Complete 2x2 table

| | Fast ramp (`Tramp=1 us`) | Slow ramp (`Tramp=68.61 us`) |
|---|---|---|
| **Divider ABSENT** | `e16_ctrl_f3_t1` (reused by reference): no runaway, `IL1_max=150.07 A` | `e16_g1_f3_t68p61` (reused by reference): no runaway, `IL1_max=86.94 A` |
| **Divider PRESENT** | `e17_div_f3_t1` (NEW): **RUNAWAY**, `max{|IL1..4|}=1046.42 A` | `e17_div_f3_t68p61` (NEW): no runaway, `max{|IL1..4|}=154.73 A` |

Full per-cell detail (all values directly read from each cell's own
`.log`; the two reused cells' values are copied verbatim from R04E16's
own committed `results.json`, not re-derived):

| Quantity | `e16_ctrl_f3_t1`<br>(absent/fast, reused) | `e16_g1_f3_t68p61`<br>(absent/slow, reused) | `e17_div_f3_t1`<br>(present/fast, NEW) | `e17_div_f3_t68p61`<br>(present/slow, NEW) |
|---|---:|---:|---:|---:|
| `IL1_min` (A) | -21.45 | -4.45 | -860.80 | -22.62 |
| `IL1_max` (A) | 150.07 | 86.94 | 813.14 | 154.73 |
| `IL2_min` (A) | -23.12 | -0.72 | -686.53 | -21.16 |
| `IL2_max` (A) | 94.41 | 70.37 | 884.90 | 147.85 |
| `IL3_min` (A) | -18.42 | -0.76 | -604.43 | -15.65 |
| `IL3_max` (A) | 86.50 | 70.25 | 877.84 | 140.79 |
| `IL4_min` (A) | -32.10 | -2.04 | -469.63 | -15.35 |
| `IL4_max` (A) | 84.02 | 70.48 | 1046.42 | 143.34 |
| `max{|IL1-4|}` (A) | 150.07 | 86.94 | **1046.42** | 154.73 |
| within `+/-250 A` bound | YES | YES | **NO** | YES |
| `Vout_final` (V) | 0.5588 | 0.5588 | 1.0060 | 1.0059 |
| `Vout_pk` (V) | 0.5605 | 0.5591 | 1.8233 | 1.0254 |
| `VC1_final` (V, target 36) | 19.877 | 19.914 | 35.751 | 35.859 |
| `VC2_final` (V, target 24) | 13.157 | 13.220 | 23.814 | 23.798 |
| `VC3_final` (V, target 12) | 6.660 | 6.578 | 11.827 | 11.857 |
| `LADDER_ERR` | 1.3447 | 1.3478 | 0.0291 | 0.0242 |
| `IIN_PK` (A) | 150.07 | 134.55 | 2498.95 | 60.82 |
| Wall clock (real LTspice) | n/a (reused) | n/a (reused) | 1203.95 s (~20.1 min) | 1641.49 s (~27.4 min) |

Two things beyond the runaway/no-runaway split are worth flagging
directly (see Section 6): both divider-PRESENT cells reach `Vout_final`
within `0.6%` of the `1 V` target and `LADDER_ERR` around `0.024-0.029`
-- roughly `46-56x` better than either divider-ABSENT cell's own
`LADDER_ERR~=1.34-1.35` and `Vout_final~=0.559 V`. The divider genuinely
does its intended job (precharging the capacitor ladder toward
`36/24/12 V` well before `TSTOP`) in both ramp conditions; the *cost* of
doing that job at a fast ramp is the runaway current documented above.

## 6. What this pattern means for the "is it the divider or the ramp" question

R04E16 could not distinguish two hypotheses because it changed both
factors (divider removed AND ramp added) at once relative to R03A. This
experiment isolates them and gets a clean, unambiguous answer for this
specific two-cell design: **with the divider physically present, the
`Vin` ramp speed is the decisive factor.** A fast ramp (`Tramp=1 us`,
matching R04E16's own "near-instantaneous" control case) reproduces
R03A's own catastrophic runaway (currents in the same `563-1046 A`
order of magnitude, all four phases individually exceeding the `+/-250
A` bound); a `68.61x`-slower ramp (R04E16's own `30x`-margin value,
unchanged here) avoids it entirely, with phase currents essentially
matching the corresponding divider-ABSENT cell at the same `Tramp`
(`154.7 A` here vs. `86.9 A` for `e16_g1_f3_t68p61` -- same order,
divider-present is somewhat higher but nowhere near runaway scale).

This directly supports Roberts' own dissertation Section 3.5 mechanism
as a genuine causal explanation, not merely a byproduct of removing the
divider: the ramp itself does real protective work **when there is
something (the precharged, mismatched capacitor ladder) for it to
protect against.** R04E16's own control-cell surprise (a fast ramp
avoiding runaway even with the divider absent) is not contradicted by
this result -- it is explained by it: with no divider, there is no
precharge mismatch for a fast ramp to expose in the first place, so
ramp speed had nothing to act on in that experiment. Put together,
R04E16 and R04E17 tell a coherent, non-contradictory story: **the ramp
mechanism protects specifically against the divider's own precharge-vs.
-cold-Vout mismatch; if that mismatch is removed some other way (as
R04E16 did, by deleting the divider entirely), the ramp's protective
role becomes moot, not wrong.**

## 7. What this does and does not establish

**Established by this experiment (for these exact two cells only):**
- With R03A's own divider network reintroduced at `CDIV=300 uF`
  (R04E15's own corrected value at `Cfly=3 uF`), the `Vin` ramp speed
  causally determines whether R03A's runaway mechanism reproduces,
  isolating it cleanly from the "divider removed" factor R04E16 could
  not separate.
- The divider network itself, when it has time to do its job (the
  slow-ramp cell), achieves a substantially better `LADDER_ERR` and
  `Vout_final` than either of R04E16's own divider-ABSENT cells --
  reintroducing the divider is not merely "safe if slow", it is
  actively beneficial for ladder/output accuracy at either ramp speed
  tested.

**NOT established (per BOUNDARY.md Section 8, and directly applicable
here):**
- No claim is made about any `Cfly` value other than `3 uF`, nor any
  `Tramp` value other than the two already used in R04E16 -- whether
  the runaway/no-runaway boundary sits closer to `1 us` or closer to
  `68.61 us`, or scales with `Cfly`, is not tested by this two-point
  design and would need a further, separately-scoped sweep (e.g.
  bisecting `Tramp` between `1` and `68.61 us` at fixed `Cfly=3 uF`).
- `LADDER_ERR` at the moment PWM starts (`t=0` here, since `TSTART=0` in
  both cells) was not used as a mediating variable; "divider
  present/absent" is treated as the binary factor BOUNDARY.md Section 8
  specifies, not a graded one.
- This does not modify, overwrite, or invalidate R04E16's own committed
  results -- its two divider-absent cells are reused here strictly by
  reference (their already-published numbers, copied verbatim), not
  re-run.
- No P24 reproduction claim of any kind is made, the same standing
  Track-B limitation as every other experiment in this lineage.

## 8. Provenance and classification

Every changed/new value in this experiment's two new netlists traces
directly to an already-established source, per BOUNDARY.md Section 5:

| Value | Source | Category |
|---|---|---|
| Divider-network topology (`CIN1-4`/`RLEAK1-4`/`DPC1-3`, model `DPRE`), reused unchanged | `paper_locked/02_ectc2024_main/spice/R03A_passive_precharge_to_fixed_pwm_takeover.cir` | inherited, unchanged |
| `CDIV=300 uF` | R04E15's own well-characterized best-point value at `Cfly=3 uF` | `SENSITIVITY_ONLY`, inherited |
| `Cfly=3 uF`, `LPHASE=1.4666667 nH` | R04E8's own corrected value / Eq.-4 branch | `SENSITIVITY_ONLY`/`P24_EXPLICIT`, inherited |
| `Tramp={1, 68.61} us` | R04E16's own already-tested control and `30x`-margin values | inherited, unchanged |
| `solver=alt cshunt=1e-15 plotwinsize=0` | R04E16's own forensically-diagnosed fix for this netlist family at `TMAX=50 ps` | `NUMERICAL_IDEALIZATION`/`TOOLING_NECESSITY`, inherited |

No new paper-sourced, cross-paper, or external-device data is
introduced; this experiment recombines two already-existing,
already-justified circuit elements at already-established parameter
values. Classification, following this track's own established
language (R04E14/R04E15/R04E16): **`SENSITIVITY_ONLY` /
`NOT_P24_REPRODUCTION`** -- this is a mechanism-isolation finding about
this project's own Track-B constructs (Roberts' soft-start idea and
R03A's divider network), not a claim about P24's own reported behavior.

## 9. Files

- `cases/e17_div_f3_t1.cir`, `cases/e17_div_f3_t1.log`,
  `cases/e17_div_f3_t1.raw` -- the fast-ramp/divider-present cell.
- `cases/e17_div_f3_t68p61.cir`, `cases/e17_div_f3_t68p61.log`,
  `cases/e17_div_f3_t68p61.raw` -- the slow-ramp/divider-present cell.
- `scripts/analyze_r04e17.py` -- parses both new cells' `.log` files and
  merges in R04E16's own two reused cells (from its committed
  `results.json`) to produce the complete 2x2 table.
- `results.csv`/`results.json` -- the complete 4-row 2x2 table (two
  reused rows marked `reused_by_reference: true`, two new rows marked
  `false`).
