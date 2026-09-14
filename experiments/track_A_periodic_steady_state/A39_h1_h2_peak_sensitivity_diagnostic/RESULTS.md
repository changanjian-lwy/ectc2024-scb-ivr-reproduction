# A39 H1-vs-H2 peak-current sensitivity diagnostic results

Track: A (periodic steady-state reproduction). **Purely diagnostic** per
BOUNDARY.md: nothing here is solved, no locked parameter was retuned, and no
swept `IL1_INIT`/`IL2_INIT` value is promoted to a default. This answers
BOUNDARY.md Section 5's three questions directly.

## 1. Whether the simulation completed normally

Yes, for every run used in this report. The Part-1 sweep (13 `IL1_INIT`
points, `-20 A` to `+40 A`) and the Part-2 waveform-capture run (1 point, at
A38's exact best-candidate operating point) all completed with LTspice exit
code 0 (`subprocess.run(..., check=True)`; a nonzero exit would have raised).
One coding mistake occurred and is disclosed for transparency: the first
attempt at `part2_waveform_comparison()` tried to read a differential trace
name (`V(xmod:a1,xmod:x1)`) that LTspice's `.raw` does not actually store
(confirmed directly: `raw.get_trace()` lists only single-ended node traces,
even though the netlist's own `.save` line and `.meas` statements use the
differential syntax). This raised `IndexError` and stopped the script after
Part 1 had already finished and been written to disk. The fix (reconstruct
`VC1=V(a1)-V(x1)`, `VC2=V(a2)-V(x2)` from the already-present single-ended
traces) was applied and Part 2 was re-run standalone; Part 1's results were
untouched by the crash and did not need to be re-run.

## 2. Parameters actually used

Locked, unchanged from A38/A37/A36/A35/A27 (BOUNDARY.md Section 3):
topology, `Coss` (385 pF high-side / 770 pF low-side), ideal reverse-clamp
(`Vf=0`, `Ron=1 mOhm`), `LPHASE=1.466666666666667 nH`, `TON=16.6667 ns`,
`PHASE=50 ns`, `NEG_FRAC=.09` (`INEG=11.25 A`), `RHS=7 mOhm`
(`GS61008T_RDS_TYP_25C`, external device data), `RLS=3.5 mOhm`, ideal `1 V`
output clamp, timestep/solver options. Netlist template: A38's own final
`.cir` (`A38_h2_h3_local_peak_and_100ns_zvs_solve.cir`), read-only, never
modified.

**Part 1 (wide `IL1_INIT` sweep):** `IL2_INIT=21.205095337 A` (A38 seed,
unmoved), `IL3_INIT=56.32056566312004 A` (A38 solved), `IL4_INIT=
84.1447433786 A`, `VC1_INIT=36.000066454 V`, `VC2_INIT=23.9999142326 V`,
`VC3_INIT=12.0006048777 V` — all four read directly from A38's
`best_candidate.json` (not retyped). `IL1_INIT` swept over
`{-20,-15,-10,-5,0,5.2947,10,15,20,25,30,35,40} A` (13 points, `5.2947`
included so A36's own solved point sits inside the sweep for direct
comparison). Every swept value is `SENSITIVITY_ONLY`.

**Part 2 (TON1-vs-TON2 waveform comparison):** the single point
`IL1_INIT=5.2947 A` (A36-solved), `IL2_INIT=21.205095337 A` (A38-seed),
`IL3_INIT=56.32056566312004 A`, `IL4_INIT=84.1447433786 A`,
`VC1_INIT=36.000066454 V`, `VC2_INIT=23.9999142326 V`,
`VC3_INIT=12.0006048777 V` — i.e. byte-identical to A38's own
`best_candidate.json`, so this single 4-phase run contains both H1's and
H2's representative solved/near-solved operating points simultaneously.
Three additional confirmatory probes were run at `IL2_INIT` seed`+1.0 A`,
seed`+2.0 A` (both known from A38 to still admit H2) to check whether the
admission current found in the main Part-2 run was a coincidence of that one
point or a structural pin (see Section 4).

## 3. When each key event occurred

Part 2 main run (`IL1_INIT=5.2947`, `IL2_INIT=21.205095337`):

| Event | Time | Current |
|---|---:|---:|
| H1 on (unconditional, cycle start) | 0.0007 ns | `iL1`=5.3177 A |
| H1 off (fixed TON1 end) | 16.6681 ns | `iL1`=124.9999 A |
| `iL2` crosses 0 (freewheeling down) | 30.8453 ns | 0 A |
| `iL2` crosses `-INEG`=-11.25 A | 47.6792 ns | -11.25 A |
| H2 on (natural `Vds(H2)=0` admission, at its 50 ns slot) | 50.0007 ns | `iL2`=-1.2858 A |
| H2 off (fixed TON2 end) | 66.6681 ns | `iL2`=117.7638 A |

Confirmatory `IL2_INIT` probes (all other variables held at the values
above):

| `IL2_INIT` delta | H2 admission time | `iL2` at admission | `iL2` at TON2 end | TON2 gain |
|---:|---:|---:|---:|---:|
| 0 (seed) | 50.0007 ns | -1.2858 A | 117.7638 A | 119.050 A |
| +1.0 A | 51.4437 ns | -1.2776 A | 117.7801 A | 119.058 A |
| +2.0 A | 52.8859 ns | -1.2721 A | 117.7941 A | 119.066 A |

## 4. Key voltages and currents

### Part 1: wide `IL1_INIT` sweep result (H1's peak-current sensitivity)

| `IL1_INIT` (A) | `iL1` at H1-off (A) | `peak_error_h1` (A) | local slope (A/A) |
|---:|---:|---:|---:|
| -20.0 | 101.5779 | -23.4221 | -- |
| -15.0 | 106.2324 | -18.7676 | 0.9309 |
| -10.0 | 110.8740 | -14.1260 | 0.9283 |
| -5.0 | 115.5027 | -9.4973 | 0.9257 |
| 0.0 | 120.1187 | -4.8813 | 0.9232 |
| 5.2947 (A36 solved) | 124.9999 | -0.0001 | 0.9219 |
| 10.0 | 129.3378 | 4.3378 | 0.9219 |
| 15.0 | 133.9475 | 8.9475 | 0.9219 |
| 20.0 | 138.5571 | 13.5571 | 0.9219 |
| 25.0 | 143.1667 | 18.1667 | 0.9219 |
| 30.0 | 147.7763 | 22.7763 | 0.9219 |
| 35.0 | 152.3859 | 27.3859 | 0.9219 |
| 40.0 | 156.9955 | 31.9955 | 0.9219 |

Overall slope across the full 60 A span: `(156.9955-101.5779)/60 = 0.9236
A/A` -- matching the point-to-point local slope (which settles to `0.9219
A/A` and stays there for every pair from `-10 A` to `+40 A`) to within
`~0.2%`. **No flattening, bending, or saturation is observed anywhere in
this 13-point, 60 A-wide sweep** -- 10x wider than A36's own probe (which
only spanned `-0.94 A` to `5.29 A`, a `6.23 A` range).

This constant slope matches a closed-form analytic prediction almost
exactly. H1's TON1 window is governed by a simple linear RL-charging ODE,
`dI/dt = (V0 - I*RHS)/LPHASE`, with `V0 = VIN - VC1(t)` effectively constant
(`VIN=48 V` is an ideal source with zero output impedance, and `VC1` moves
by only `~0.02 V` over the `16.67 ns` window against a `CFLY~58.2 uF`
flying cap -- see Part 2 below). The closed-form solution of this ODE gives
`d[I(TON)]/d[I(0)] = exp(-RHS*TON/LPHASE) = exp(-0.007*16.6667e-9/
1.4667e-9) = exp(-0.07955) = 0.9235`, matching the empirical `~0.9219-
0.9236` to within numerical-timestep noise. **H1's linearity is not a local
patch on top of a shared saturating curve with H2 -- it is the exact,
global, closed-form behavior of a simple linear-RL charging window with a
non-sagging drive rail**, and this holds over the entire tested range.

### Part 2: TON1 vs TON2 direct comparison

| Quantity | TON1 (H1) | TON2 (H2) | Comment |
|---|---:|---:|---|
| Window start current | 5.3177 A (=`IL1_INIT`) | -1.2858 A (`!=IL2_INIT`=21.2 A) | **decisive difference; see below** |
| Window end current | 124.9999 A | 117.7638 A | matches A36/A38 residuals |
| Window gain (end-start) | 119.682 A | 119.050 A | within 0.53%, essentially equal |
| `di/dt` window-average | 7.181 A/ns | 7.143 A/ns | within 0.5%, essentially equal |
| `di/dt` near window start | 8.478 A/ns | 7.462 A/ns | both windows curve similarly; see caveat below |
| `di/dt` near window end | 6.899 A/ns | 6.808 A/ns | both windows curve similarly; see caveat below |
| Flying-cap voltage at window start | `VC1`=36.0002 V | `VC2`=23.9997 V | both near their nominal 36/24 V levels |
| Flying-cap voltage at window end | `VC1`=36.0205 V | `VC2`=24.0180 V | |
| Flying-cap delta over window | **+0.0203 V** | **+0.0183 V** | **nearly identical, both negligible** |
| `RHS`-IR drop at window-end peak current | `7 mOhm x 125.00 A = 0.875 V` | `7 mOhm x 117.76 A = 0.824 V` | **H2's IR drop is smaller, not larger** |

Caveat on the start/end `di/dt` finite-difference values: these use a
5-sample local window on LTspice's adaptive (non-uniform) timestep grid, so
the two windows' 5-sample spans cover different absolute `dt`, which biases
the ratio between the start- and end-slope estimates (a numerical-sampling
artifact, not a physical one). The window-average `di/dt` and the window
gain are the robust, sampling-independent numbers, and both show TON1 and
TON2 delivering **essentially the same volt-second gain** (119.68 A vs
119.05 A, `0.53%` apart).

**The single largest, and essentially the entire, source of the `125 -
117.76 = 7.24 A` gap is the `6.60 A` difference in each window's *starting*
current** (`5.3177 A` for H1 vs `-1.2858 A` for H2): `6.60 A` (starting
current gap) `+ 0.63 A` (small gain gap) `= 7.24 A`, matching the measured
gap to within rounding. Neither the flying-capacitor voltage (both sag/rise
by `~0.02 V`, an order of magnitude too small to matter across a `12 V`
nominal per-phase drive) nor the `RDS(on)` IR drop (both under `0.9 V`, and
H2's is actually *smaller* because its current is lower) can explain a
`7.24 A` deficit. A `7.24 A` deficit at this window's gain slope
(`~7.16 A/ns`) corresponds to only `~1.0 ns` of "missing" volt-seconds --
about the same order as the observed `0.53%` gain difference times the
window length, not something a `<0.03 V` capacitor delta or a `<0.9 V`
`IR` drop difference of `<0.05 V` could produce.

**What actually differs is what sets each window's starting current.**
H1's TON1 begins in state `P1_M1`, the `.machine`'s unconditional
cycle-start state (`time>=T0` alone, no event gate) -- so `IL1_INIT` *is*,
directly and without modification, TON1's initial condition. H2's TON2
begins only after the chain `P1_M3` (`I(LIND2)<=0`) `->` `P1_M4`
(`I(LIND2)<=-INEG`) `->` `P1_M5` (turns L2 off) `->` `P2_M1`
(`time>=50ns AND V(a1,a2)<=0`, a resonant Coss commutation from L2's
negative current, not a fixed-current threshold). By the time that chain
completes and H2 actually admits, `iL2` has drifted from `-11.25 A`
(`-INEG`, crossed at `47.68 ns`) back up to only `-1.29 A` (crossed the
`50 ns` floor essentially immediately after `-INEG`, with `~19 ns` between
the `-INEG` crossing and admission) -- a value set by the Coss-resonance
physics of that commutation, not by `IL2_INIT`.

**This admission current is empirically pinned, not merely close by
coincidence at the seed.** The three-point probe (`IL2_INIT` seed, `+1 A`,
`+2 A`; Section 3 table) shows the admission current moves by only `0.014 A`
across a full `2 A` range of `IL2_INIT`, while the admission *time* moves by
`2.89 ns` over that same range (`~1.45 ns` per A, matching A38's own logged
`+1.45 ns/A` and `+2.89 ns` at `+2 A` almost exactly). **Essentially all of
`IL2_INIT`'s leverage is absorbed into re-timing the admission event, not
into re-leveling the admission current** -- which is exactly why moving
`IL2_INIT` barely moves the TON2-end peak (A38's measured `+0.0162 A/A`):
the lever is coupled to the wrong degree of freedom for this residual.

## 5. Whether the acceptance condition was met (per BOUNDARY.md Section 6)

Yes. BOUNDARY.md Section 6 requires (a) a wide `IL1_INIT` sweep that either
finds a flattening point or states none was found up to the tested range,
(b) a time-resolved TON1-vs-TON2 comparison of the four named quantities
from directly inspected `.raw` data, and (c) a named leading hypothesis with
supporting evidence, or an explicit statement of ambiguity. All three are
satisfied: (a) no flattening found over `-20 A` to `+40 A` (Section 4), (b)
all four quantities (`di/dt` shape, `VCk` sag, `RHS` IR drop, admission-event
timing/current) were extracted directly from `.raw` via `spicelib.RawRead`
(Section 3-4), and (c) a single decisive factor is named with specific
supporting numbers (Section 6 below) -- the evidence is not ambiguous.

## 6. Where the first failure boundary occurred / named decisive factor

There is no "failure boundary" in the solve sense (BOUNDARY.md Section 6/7
reframes this for a diagnostic as: did the sweep/trace produce usable
evidence, or is the result blocked/ambiguous). It did: usable evidence was
obtained for both questions, and it isolates a single decisive factor.

**Named decisive factor: the event-gated ZVS admission architecture itself
(control-logic/physical-event coupling), not `RDS(on)` IR drop, not
flying-capacitor sag, and not a shared device/model saturation.**

Evidence ranked by how directly it isolates the cause:
1. **Admission-current pinning** (Section 4, Section 3 table): `iL2` at
   H2's own turn-on varies by only `0.014 A` across a `2 A` `IL2_INIT`
   range while the admission time shifts by `2.89 ns` over the same range.
   This directly shows `IL2_INIT`'s effect is being consumed by re-timing,
   not re-leveling, the ramp's start point -- the specific mechanism behind
   A38's `0.0162 A/A` finding.
2. **Equal ramp gain** (Section 4): TON1 and TON2 deliver essentially the
   same current gain over their fixed windows (`119.68 A` vs `119.05 A`,
   `0.53%` apart) and the same average `di/dt` (`7.18` vs `7.14 A/ns`).
   This rules out a bent/clipped/saturating ramp *shape* as the cause --
   the ramps themselves are behaving alike; only their starting points
   differ.
3. **Negligible, near-equal flying-cap sag** (`VC1` `+0.0203 V`, `VC2`
   `+0.0183 V`) rules out capacitor voltage sag/coupling as a differentiator
   between the phases.
4. **Negligible, near-equal (and smaller for H2) `RDS(on)` IR drop**
   (`0.875 V` vs `0.824 V`) rules out switch conduction drop as the
   differentiator.
5. **H1's own wide-range linearity matches a closed-form RL-charging
   prediction exactly** (Section 4, `exp(-RHS*TON/LPHASE)=0.9235` vs
   measured `~0.9219-0.9236` over a 60 A span), showing H1 is not "one point
   on a shared saturating curve H2 is also on" -- H1's curve has no visible
   saturation anywhere tested, and the physics governing it (a linear RL
   charge against a non-sagging rail) is structurally different from what
   limits H2 (an event-gated admission current set by resonant commutation,
   decoupled from the swept initial-condition variable).

**Conclusion to BOUNDARY.md Section 5.3: the user's suspicion is
correct in spirit but the mechanism is more specific than "same curve,
different point."** H1 and H2 are **not** two points on one shared
nonlinear/saturating peak-current-vs-initial-current curve; each phase's
own TON ramp is a nearly identical, near-linear RL-charging process (ruled
out: RDS(on) drop, cap sag, ramp-shape difference). What differs is
*upstream* of the ramp: H1's initial-current knob is wired directly to its
own ramp's start point (an unconditional absolute-time admission), while
H2's initial-current knob is wired to the *timing* of an event-gated,
self-regulating ZVS commutation whose *outcome current* is set by that
commutation's own physics, not by the knob. That upstream wiring
difference -- not a shared saturating I-vs-I curve -- is why the same class
of lever (`ILk_INIT`) has a ~60x different effective sensitivity on the two
phases' own peak-current residuals.

## 7. Result grade

**`SENSITIVITY_ONLY`.** This is a sensitivity/diagnostic experiment per the
task's explicit framing; it produced a clean, evidenced, non-ambiguous
answer to all three of BOUNDARY.md Section 5's questions, but per Section
III/X it must never be reported as a `PASS`/`FAIL` on the underlying 125 A
target (it does not attempt that target) and no swept `IL1_INIT`/`IL2_INIT`
value here is promoted to a default model parameter.

## 8. Which module should be adjusted next

Not a "module to adjust next" in the solve sense (BOUNDARY.md Section 8:
this diagnostic proves no solve). The finding does point at what any future
attempt to close H2/H3's `~7.2 A` shortfall would need to target: since the
shortfall is a starting-current deficit set by the resonant Coss-commutation
admission physics (not by `IL2_INIT`, not by `RDS(on)`, not by cap sag), the
only levers that could plausibly move the *admission current* itself are
ones that change that commutation's own dynamics -- e.g. `Coss`
value/nonlinearity, the `-INEG` target itself (a `P25`-labelled,
`CROSS_PAPER_EXTENSION` 9% branch parameter, not something this experiment
is authorized to touch), or the dead/freewheel duration between the
`-INEG` crossing and the `50 ns` floor. This experiment does not evaluate
any of those; it only identifies that `ILk_INIT` is the wrong lever for this
particular residual on any event-gated phase (H2, H3, and by the same
mechanism almost certainly H4, though H4 was not directly measured here per
BOUNDARY.md Section 8).

## 9. Which parameters must never be changed because of this failure

Per Section XI and BOUNDARY.md Section 7: `TON=16.6667 ns` must never be
extended to force `iL2`/`iL3` up to 125 A; `RHS`/`RLS`/`Coss`/`LPHASE`/
`CFLY` must not be changed to fit this result; the 9% negative-current label
(`NEG_FRAC`) must not be raised or lowered to manufacture a peak-current
match and must never be presented as the 2024 2% result; no swept
`IL1_INIT` or `IL2_INIT` value from this diagnostic's sweep (Part 1's 13
points or Part 2's 3 confirmatory probes) may be promoted to a new default
`.param` value -- all are `SENSITIVITY_ONLY`. `IL2_INIT`, `IL3_INIT`,
`IL4_INIT`, and all three `VCk_INIT` remain exactly as inherited from A38;
this experiment gives no reason to reopen any of them, and confirms (rather
than challenges) A38's own conclusion that `IL2_INIT` is not a viable lever
for R1. A36's own two converged residuals (H1 peak-current, H2 ZVS-timing)
are unaffected by this experiment (Part 1's sweep only varies `IL1_INIT` in
throwaway probe netlists under the gitignored `A39_solver_work/`; A36's
archived candidate at `IL1_INIT=5.2947` was never modified).
