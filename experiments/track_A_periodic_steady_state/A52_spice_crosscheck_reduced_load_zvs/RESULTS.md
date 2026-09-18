# A52 - SPICE cross-check of A51's four-phase joint ZVS state (RESULTS)

Boundary: `BOUNDARY.md` in this directory (not modified by this experiment).

## 0. Headline

**All four phases independently achieve natural ZVS in LTspice, at crossing
times agreeing with A51's own Python predictions to between `0.107%` and
`0.242%`** - against a tolerance of `20%` that was pre-declared in
`BOUNDARY.md` Section 4 before the run. This is `BOUNDARY.md` Section 6's
FIRST outcome: the first SPICE-confirmed four-phase joint ZVS periodic
state in this project's history.

| Phase | A51 target `t_cross` (ns) | SPICE `t_cross` (ns) | Error (ns) | Relative | Within 20%? | Natural ZVS in SPICE? |
|---|---:|---:|---:|---:|:---:|:---:|
| 1 | `1.128389` | `1.131116` | `+0.002727` | `+0.242%` | **yes** | **yes** |
| 2 | `1.122660` | `1.124222` | `+0.001562` | `+0.139%` | **yes** | **yes** |
| 3 | `1.122732` | `1.123930` | `+0.001198` | `+0.107%` | **yes** | **yes** |
| 4 | `0.858292` | `0.859292` | `+0.001000` | `+0.116%` | **yes** | **yes** |

Every crossing time is measured from that phase's own dead-time window
start. The tolerance was beaten by a factor of `83x` (phase 1, the worst)
to `187x` (phase 3, the best).

Supporting verdicts, all independently checked below:

- Every phase current stayed within `+/-250 A` (worst `100.3009 A`).
- Zero solver-corruption fingerprints (no non-monotonic or duplicate
  timestamps in `252,547` points; the commanded rail is exactly `48.0 V`
  at every timepoint after `t=0`).
- SPICE's own average output (`0.687945 V`) and delivered power
  (`89.9210 W`) match A51's `0.687944 V` / `89.9207 W` to `1.3e-6 V` and
  `3.5e-4 W`.
- The periodicity itself is reproduced: after one full period SPICE's
  state differs from the seed `z*` by at most `2.52e-2` in the worst
  coordinate, a relative residual of `3.74e-4` (Section 7 discusses what
  this number does and does not mean).

## 1. Window-boundary derivation and its cross-check (`BOUNDARY.md` Section 2)

`BOUNDARY.md` Section 2 requires the window boundaries to be derived in
Python from `solver_copy` directly, **not** by re-deriving the `T/4`-offset
formula by hand. `a52_boundary.py` contains no offset arithmetic at all.
Instead it **bisects the label actually returned by
`solver_copy.zero_start_descriptor.commanded_pwm_mode`** - the same
function A50/A51 integrate against - so each boundary is located to the
last ulp without any formula for it ever being written down.

`derive_windows.py` then produces a second, INDEPENDENT derivation from
A51's own already-committed `a51_period_map.period_intervals`, and
compares both against `BOUNDARY.md` Section 4's quoted instants.

Boundary values, read back off the constructed object rather than retyped
(`derive_windows_log.txt`):

```
period_s                        = 2e-07
duty (= nP*Vout/Vin)            = 0.08333333333333333
on_time_s (Ton)                 = 1.6666666666666664e-08
dead_time_s (d)                 = 2.15e-09
switch_on_resistance_ohm        = 0.007        (UNIFORM, both sides)
flying_capacitances_f           = (3e-06, 3e-06, 3e-06)
switch_capacitance.high_total_f = 3.85e-10     (CH = 385 pF)
switch_capacitance.low_total_f  = 7.7e-10      (CL = 770 pF)
output_capacitance_f            = 0.004672
source_inductance_h / _resistance_ohm = 5e-09 / 0.01
phase_inductance_h / _resistance_ohm  = 1.4666667e-09 / 1e-06
divider_capacitance_f / leakage_ohm   = 0.0003 / 1e9
diode_off_resistance_ohm        = 1e12
switch_off_resistance_ohm       = 1e12
period start t0                 = 2.3001075e-05 s
```

### 1.1 Cross-check against `BOUNDARY.md` Section 4

| Phase | (a) bisection of `commanded_pwm_mode` | (b) A51 `period_intervals` | (c) `BOUNDARY.md` Section 4 | (a) vs (c) |
|---|---|---|---|---|
| 1 | `[2.3198925e-05, 2.3201075e-05)` | `[2.3198925e-05, 2.3201075000000002e-05)` | `[2.319892500e-05, 2.320107500e-05]` | exact (`0` / `0`) |
| 2 | `[2.3048925e-05, 2.3051075000000002e-05)` | identical, bit-for-bit | `[2.304892500e-05, 2.305107500e-05]` | `0` / `3.388e-21 s` |
| 3 | `[2.3098925e-05, 2.3101075e-05)` | identical, bit-for-bit | `[2.309892500e-05, 2.310107500e-05]` | exact (`0` / `0`) |
| 4 | `[2.3148925e-05, 2.3151075e-05)` | identical, bit-for-bit | `[2.314892500e-05, 2.315107500e-05]` | exact (`0` / `0`) |

**All four windows reproduce `BOUNDARY.md` Section 4's quoted values
exactly.** Two residual discrepancies are reported rather than rounded
away, both of which are a single unit in the last place of a `float64` at
`2.3e-5 s` (`1 ULP = 3.388e-21 s`):

- phase 1's window END differs between derivations (a) and (b) by
  `2e-21 s`, because (b) computes `center + d/2` while (a) bisects the
  schedule directly;
- phase 2's window END differs from Section 4's printed 10-significant-
  figure value by `3.388e-21 s`.

Both are `18` orders of magnitude below the `2.15 ns` window and `9`
orders below the finest timestep LTspice was asked for, so agreement is
asserted at 1 ULP and the actual gaps are recorded above.

### 1.2 Offset conversion to netlist time (shown explicitly)

```
common reference  TOFFSET := t0 = 2.3001075e-05 s
netlist time      tau     := t_absolute - TOFFSET
```

`tau = 0` is exactly the instant A51's own period map starts from - the
instant phase 1's turn-on dead-time window ends and phase 1 goes HIGH - so
the seed state `z*` is the state at `tau = 0`. The `.tran` runs
`[0, 250 ns]`, matching A37/A49's own "one period plus overhang"
convention.

Full commanded schedule in netlist time, straight from the bisection:

| Phase | HIGH | DEADTIME turn-off | LOW | DEADTIME turn-on |
|---|---|---|---|---|
| 1 | `[0, 14.5166667)` and `[200, 214.5166667)` | `[14.5166667, 16.6666667)`, `[214.5166667, 216.6666667)` | `[16.6666667, 197.85)`, `[216.6666667, 250]` | `[197.85, 200)` |
| 2 | `[50, 64.5166667)` | `[64.5166667, 66.6666667)` | `[0, 47.85)`, `[66.6666667, 247.85)` | `[47.85, 50)`, `[247.85, 250)` |
| 3 | `[100, 114.5166667)` | `[114.5166667, 116.6666667)` | `[0, 97.85)`, `[116.6666667, 250]` | `[97.85, 100)` |
| 4 | `[150, 164.5166667)` | `[164.5166667, 166.6666667)` | `[0, 147.85)`, `[166.6666667, 250]` | `[147.85, 150)` |

(all in ns). The `Vds` node pair for each phase is taken from
`solver_copy`'s own `HIGH_SIDE_BRANCHES`, so the SPICE probes cannot
disagree with what A51 measured: phase 1 `V(vin)-V(a1)`, phase 2
`V(a1)-V(a2)`, phase 3 `V(a2)-V(a3)`, phase 4 `V(a3)-V(x4)`. The low-side
admission node is `x{p}`, from `a51_period_map._resolve_turn_off`.

### 1.3 `RLOAD` sizing

`BOUNDARY.md` Section 1's state was solved at `module_power_w=190`
nominal, at which `ZeroStartBoundary.load_resistance_ohm` would return
`1/190 = 5.263158e-3 ohm`. The netlist instead sizes the load from the
state's own **actual** delivered power, as required:

```
RLOAD = Vout^2 / P = 0.687944^2 / 89.9207 = 5.263159062774e-03 ohm
```

The two agree to `2.2e-7` relative, which is itself a useful consistency
check that Section 1's quoted `0.687944 V` and `89.9207 W` are mutually
consistent with the solver's own load model.

## 2. Pilot test (`BOUNDARY.md` Section 2's mandatory "pilot-first" step)

### 2.1 What was piloted, and why it was not skipped

The mechanism under test is the only thing that can silently invalidate
this whole experiment: the dead-time window must be exited at **whichever
comes first** of a natural `V <= 0` crossing or the commanded window end.
A fixed-delay approximation of either branch would produce a meaningless
comparison.

The pilot circuit is a single `1 nF` node discharged by a constant current
that switches on exactly when the window opens, so the natural crossing
instant is known in closed form:

```
dV/dt = -I/C   =>   t_cross = window_start + V0*C/I
```

with `V0 = 10 V` and a window of exactly `2.15 ns` (the real
`dead_time_s`). `I = 10 A` puts the crossing `1.000 ns` inside the window
(branch (i) must win); `I = 2 A` leaves `10 - 2*2.15 = 5.7 V` still
standing at the window end (branch (ii) must win).

### 2.2 Mechanism iterations - what failed before what worked

Reported rather than quietly discarded, because each failure is a real
constraint on the final netlist:

1. **`.machine pilot` was rejected outright.** Every directive in the
   block failed to parse ("Expected device instantiation or directive
   here"). The argument to `.machine` is a **TIME**, not a name - A37's
   own netlist writes `.machine 1p`. This was the actual cause, and it
   was initially misdiagnosed as a placement problem.
2. **Wrapping in a `.subckt` did not fix it** (the error merely changed),
   confirming the diagnosis above. Once the argument is a time, `.machine`
   works both at top level and inside a `.subckt`. The final netlist uses
   **top level**, so its node names are the descriptor's own node names
   with no `xmod:` prefix - a direct auditing benefit over A37's form.
3. **The first `.meas` log parser was wrong** and silently reported every
   zero crossing as occurring at `t=0`: a naive "first number after an
   `=`" rule reads the `0` out of `V(vds)=0` in LTspice's
   `t_vds_cross: V(vds)=0  AT 1.9999994985e-09`. This is why `meas_log.py`
   exists as a separate module with its own self-test pinned to the exact
   log shapes (`python3 meas_log.py` -> `meas_log selftest OK`).
4. **A second parser gap** was found during analysis: the
   `AVG(...)=v FROM a TO b` / `MIN(...)`/`MAX(...)` form matched nothing,
   so every range measurement read back as `None`. Also fixed and pinned
   in the self-test.

### 2.3 Mechanism characterisation

Probes (in the scratchpad, summarised here) established three properties
that the main run depends on:

- **Transition timing is independent of the maximum timestep.** A rule
  firing was measured at `1p`, `10p` and `100p` maximum timestep and gave
  a bit-identical instant, so LTspice genuinely backtracks to the
  rule-crossing instant rather than firing at the next grid point.
- **Transition timing is independent of `.machine`'s own argument**
  (`10p`, `1p`, `100f`, `10f`, `1f` all identical).
- **There is a fixed gate-output ramp of about `1.13 ps`.** The machine's
  STATE changes at the correct instant; its OUTPUT node then ramps `0->5 V`
  over `~1.13 ps`, so the switch (`Vt=2.5`) closes about `0.57-1.1 ps`
  later. The same lag appears on a pure `time>=` rule with no event in it
  at all, confirming it is an output-ramp artifact and not an
  event-detection error.

This is why the reported ZVS crossing time is taken from the **direct
physical `Vds` zero crossing**, which carries no gate-ramp latency at all,
with the gate/state transition reported alongside as a secondary number.

### 2.4 Pilot results - both branches confirmed

Eight runs: 2 cases x 2 OR encodings (`(A) | (B)` versus two separate
`.rule` lines with the same source and target states) x 2 maximum
timesteps. Pass bars were fixed before the runs: `2 ps` timing (`86x`
finer than the `171.7 ps` that `20%` of phase 4's target amounts to) and a
`10 ps` branch margin.

| Run | Gate-on instant | vs expected | Direct `Vds` crossing | vs closed form | `Vds` just before window end | Verdict |
|---|---:|---:|---:|---:|---:|:---:|
| `natural_or_1p` | `2.000905422 ns` | `+0.905 ps` | `1.999999499 ns` | `-0.001 ps` | `-0.070000 V` | PASS |
| `natural_or_10p` | `2.001111347 ns` | `+1.111 ps` | `1.999999499 ns` | `-0.001 ps` | `-0.070000 V` | PASS |
| `natural_dual_1p` | `2.000905422 ns` | `+0.905 ps` | `1.999999499 ns` | `-0.001 ps` | `-0.070000 V` | PASS |
| `natural_dual_10p` | `2.001111347 ns` | `+1.111 ps` | `1.999999499 ns` | `-0.001 ps` | `-0.070000 V` | PASS |
| `timeout_or_1p` | `3.150905422 ns` | `+0.905 ps` | none in window | n/a | `+5.699995 V` | PASS |
| `timeout_or_10p` | `3.151111347 ns` | `+1.111 ps` | none in window | n/a | `+5.699995 V` | PASS |
| `timeout_dual_1p` | `3.150905422 ns` | `+0.905 ps` | none in window | n/a | `+5.699995 V` | PASS |
| `timeout_dual_10p` | `3.151111347 ns` | `+1.111 ps` | none in window | n/a | `+5.699995 V` | PASS |

**Both required behaviours are confirmed.**

- (a) **Forced/timeout transition fires at exactly the right commanded
  instant when no natural crossing occurs**: `3.150905 ns` against a
  commanded window end of `3.150000 ns`, with `+5.699995 V` still standing
  on the node against a closed-form `5.700000 V`.
- (b) **Early, event-triggered transition fires at the crossing instant
  when one does occur**: the direct physical crossing lands on
  `1.999999499 ns` against a closed-form `2.000000000 ns` - an error of
  `1 femtosecond`.

Both OR encodings give bit-identical results; the `|` form is used in the
final netlist for legibility. `pilot_results.json` has the full record.

## 3. Initial-condition mapping (`z*` -> netlist)

The netlist uses the descriptor's own node names, so the 20-variable state
vector transfers coordinate-by-coordinate with no reinterpretation.

| # | Variable | Value from `BOUNDARY.md` Section 1 | Where it goes | Note |
|---:|---|---|---|---|
| 1 | `src` | `48.00000000687211` | `V_SRC src 0 48` | **Not** an initial condition: `V_SRC` pins `V(src)` to exactly `48 V`. `z*`'s `6.9e-9 V` excess is the solver's own residual on an algebraically-pinned variable; SPICE enforces the same equation exactly. |
| 2 | `src_r` | `47.96569022236729` | `.ic V(src_r)` | node between `R_SRC` and `L_PAR_IN` |
| 3 | `vin` | `47.969789939303524` | `.ic V(vin)` | the descriptor's POST-inductor node, **not** the `48 V` rail (that is `src`) |
| 4 | `tap3` | `36.0` | `.ic V(tap3)` | divider tap |
| 5 | `tap2` | `24.0` | `.ic V(tap2)` | divider tap |
| 6 | `tap1` | `12.0` | `.ic V(tap1)` | divider tap |
| 7 | `a1` | `48.00677396673983` | `.ic V(a1)` | with `x1` carries `VC1` |
| 8 | `a2` | `24.036209731129393` | `.ic V(a2)` | with `x2` carries `VC2` |
| 9 | `a3` | `11.636445707833776` | `.ic V(a3)` | with `x3` carries `VC3` |
| 10 | `x1` | `11.742411388577601` | `.ic V(x1)` | phase 1 switching node |
| 11 | `x2` | `-0.02167367897568295` | `.ic V(x2)` | phase 2 switching node |
| 12 | `x3` | `-0.21253311225322608` | `.ic V(x3)` | phase 3 switching node |
| 13 | `x4` | `-0.4715756542261936` | `.ic V(x4)` | phase 4 switching node |
| 14 | `out` | `0.6878908393606893` | `.ic V(out)` | across `C_OUT` and `R_LOAD` |
| 15 | `LPAR_IN` | `3.4309784504693295` | `L_PAR_IN ... ic=` | descriptor branch `('src_r','vin')`; LTspice uses the same first-node-to-second-node current convention, so the sign transfers unchanged |
| 16 | `L1` | `-5.202377626634099` | `LIND1 ... ic=` | descriptor branch `('x1','out')` |
| 17 | `L2` | `3.07242026743103` | `LIND2 ... ic=` | descriptor branch `('x2','out')` |
| 18 | `L3` | `30.358686656836504` | `LIND3 ... ic=` | descriptor branch `('x3','out')` |
| 19 | `L4` | `67.36321312878287` | `LIND4 ... ic=` | descriptor branch `('x4','out')` |
| 20 | `I_VSTEP` | `-3.43097845046932` | (none) | the MNA source-branch current, purely algebraic (its column of `E` is exactly zero, per A51's own seed table), so it is not an initial condition anywhere |

Consistency check on the mapping: `a1-x1 = 36.26436257816223`,
`a2-x2 = 24.057883410105076`, `a3-x3 = 11.848978820087002`, reproducing
`BOUNDARY.md` Section 1's quoted flying-capacitor voltages exactly.

## 4. Netlist construction and its deliberate faithfulness choices

Generated by `build_full_netlist.py`; **no timing constant and no
component value in the emitted netlist is hand-typed** - all are read off
the `ZeroStartBoundary` object or off the bisected schedule.

Topology is node-for-node `assemble_descriptor`'s: `V_SRC`/`R_SRC`/
`L_PAR_IN` source path; the four-element `300 uF` divider with `1e9 ohm`
leakages; three `1e12 ohm` precharge "diodes" (A51 calls
`evaluate_period_map` throughout with `diode_state=(False,False,False)`,
which the descriptor renders as `diode_off_resistance_ohm`); `SH1..SH4` on
`vin-a1`, `a1-a2`, `a2-a3`, `a3-x4`; `SL1..SL4` on `x1..x4` to ground;
`CH_TOTAL=385 pF` across every high branch and `CL_TOTAL=770 pF` across
every low branch, always present in both switch states as the descriptor
places them; `C1..C3 = 3 uF`; `LIND1..4 = 1.4666667 nH` with
`Rser = 1 uOhm`; `C_OUT = 4.672 mF`; `R_LOAD` per Section 1.3.

Three choices are stated rather than assumed:

1. **`Ron = 7 mOhm` UNIFORM on every switch, high and low, all four
   phases** - `BOUNDARY.md` Section 2's explicit requirement. A37/A42/A49's
   asymmetric `RHS=7 mOhm`/`RLS=3.5 mOhm` is deliberately NOT used, because
   Section 1's seed was solved under the uniform assumption; using the more
   realistic asymmetric pair here would silently test a different physical
   model.
2. **No reverse-conduction diodes.** A37's netlist instantiates
   `DH*_REVERSE`/`DL*_REVERSE` (`DGAN_IDEAL`) across every switch. A51's
   descriptor model has **no diode anywhere**: it reaches zero-voltage
   turn-on purely through the event-gated switch admission this netlist
   reproduces. Adding an ideal clamp would give the SPICE circuit a
   conduction path the model under test does not have - precisely the
   "silently testing a different model" failure Section 2 warns against.
   This omission is the single largest deliberate difference from A37's
   netlist and is the reason the comparison is meaningful.
3. **`Vin = 48 V` constant, no ramp**, per the task: this is a
   periodicity/ZVS test seeded from an already-converged state, not a
   startup test.

Per `BOUNDARY.md` Section 3, A37/A49's own `.machine` state structure is
NOT reused: it gates low-to-high commutation on a negative-current
threshold (`I(Lk)<=-INEG`), a concept A51 has nowhere. A new, simpler
machine is used instead - one per phase, four independent machines (the
pilot confirmed several `.machine` blocks may coexist), each being the
`HIGH -> DEADTIME -> LOW -> DEADTIME` schedule `commanded_pwm_mode` emits,
UNROLLED over the 250 ns run so that every commanded instant is an exact
`time>=` constant. There is no waveform, no threshold interpolation and no
modular arithmetic anywhere in the schedule. Phase 1's machine, for
example:

```
.rule P1_S0 P1_S1 time>=1.451666666667e-08
.rule P1_S1 P1_S2 (V(x1)<=0) | (time>=1.666666666667e-08)
.rule P1_S2 P1_S3 time>=1.978500000000e-07
.rule P1_S3 P1_S4 (V(vin,a1)<=0) | (time>=2.000000000000e-07)
.rule P1_S4 P1_S5 time>=2.145166666667e-07
.rule P1_S5 P1_S6 (V(x1)<=0) | (time>=2.166666666667e-07)
```

Each dead-time rule is exactly `resolve_deadtime_window`'s own rule:
natural crossing OR commanded end, whichever first.

## 5. Full per-phase SPICE ZVS verdict

Run: `.tran 0 250n 0 1p UIC`, `252,547` points, `44.2 s` elapsed.

### 5.1 Crossing verdicts

| Phase | `Vds` probe | Window (netlist, ns) | `Vds` at entry (V) | `iL` at entry (A) | Crossing (ns after window start) | `Vds` 1 fs before window end (V) | Min signed `Vds` in window (V) | Natural? |
|---|---|---|---:|---:|---:|---:|---:|:---:|
| 1 | `V(vin,a1)` | `[197.85, 200)` | `11.579063` | `-17.137197` | `1.131116` | `-0.036991` | `-0.087006` | **yes** |
| 2 | `V(a1,a2)` | `[47.85, 50)` | `11.821337` | `-17.639929` | `1.124222` | `-0.038364` | `-0.087936` | **yes** |
| 3 | `V(a2,a3)` | `[97.85, 100)` | `11.821525` | `-17.642408` | `1.123930` | `-0.038366` | `-0.087967` | **yes** |
| 4 | `V(a3,x4)` | `[147.85, 150)` | `11.471093` | `-16.491518` | `0.859292` | `-0.026070` | `-0.089458` | **yes** |

Every phase crosses zero well inside its own `2.15 ns` window (margins of
`1.02` to `1.29 ns`), and the node is already clamped NEGATIVE before the
commanded window end, so in every case the natural crossing branch won and
the commanded timeout never fired. No phase hard-switched.

### 5.2 Entry-condition agreement with A51

A test of whether SPICE even arrives at the same state, independent of the
ZVS verdict:

| Phase | `Vds` entry SPICE / A51 (V) | Difference | `iL` entry SPICE / A51 (A) | Difference |
|---|---|---:|---|---:|
| 1 | `11.579063` / `11.579036` | `+2.74e-05` | `-17.137197` / `-17.157444` | `+2.03e-02` |
| 2 | `11.821337` / `11.822603` | `-1.27e-03` | `-17.639929` / `-17.636990` | `-2.94e-03` |
| 3 | `11.821525` / `11.822824` | `-1.30e-03` | `-17.642408` / `-17.636853` | `-5.56e-03` |
| 4 | `11.471093` / `11.472413` | `-1.32e-03` | `-16.491518` / `-16.483221` | `-8.30e-03` |

Phase 1's `iL` difference (`2.03e-2 A`) is the largest, and this is
expected rather than anomalous: phase 1's turn-on window sits at
`197.85 ns`, i.e. at the very END of the period, so it has accumulated a
full period of integration difference between the two models, whereas
phase 2's window is at `47.85 ns`. The monotone growth of the `iL`
difference with window position (`2.9e-3` at `47.85 ns`, `5.6e-3` at
`97.85 ns`, `8.3e-3` at `147.85 ns`, `2.0e-2` at `197.85 ns`) is exactly
the signature of a small, steady per-period integration difference, not of
a structural disagreement.

### 5.3 Three independent readings agree

| Phase | `.raw` scan (ns) | LTspice `.meas` (ns) | Difference |
|---|---:|---:|---:|
| 1 | `1.131115715` | `1.131115715` | `0.0000 ps` |
| 2 | `1.124222471` | `1.124222471` | `0.0000 ps` |
| 3 | `1.123929858` | `1.123929858` | `0.0000 ps` |
| 4 | `0.859291504` | `0.859291504` | `0.0000 ps` |

The `.raw` scan re-finds every crossing by linear interpolation on the
binary trace without using any `.meas` result, and the two agree to the
printed precision on all four phases.

### 5.4 Step-size convergence

Per A50/A51's standing discipline, the whole run was repeated at a `4x`
finer maximum timestep (`0.25 ps`, `491,101` points):

| Phase | `1 ps` (ns) | `0.25 ps` (ns) | Difference | A51 target (ns) | Relative error at `0.25 ps` |
|---|---:|---:|---:|---:|---:|
| 1 | `1.131115715` | `1.130895710` | `-0.2200 ps` | `1.128389` | `+0.222%` |
| 2 | `1.124222471` | `1.123367859` | `-0.8546 ps` | `1.122660` | `+0.063%` |
| 3 | `1.123929858` | `1.123170886` | `-0.7590 ps` | `1.122732` | `+0.039%` |
| 4 | `0.859291504` | `0.858828647` | `-0.4629 ps` | `0.858292` | `+0.063%` |

The crossing times are step-size converged to better than `0.9 ps`
(`<0.1%`), and refining the step moves every phase slightly CLOSER to
A51's prediction, which is the direction a shared-limit agreement should
move in. The headline table in Section 0 reports the coarser (`1 ps`) run,
i.e. the less favourable of the two.

## 6. Safety and solver-fingerprint checks

### 6.1 Phase-current safety

| Phase | max `abs(iL)` from `.raw` (A) | LTspice `.meas MAX` (A) | A51's own maximum (A) |
|---|---:|---:|---:|
| 1 | `100.3009` | `100.3009` | `100.2497` |
| 2 | `99.1349` | `99.1349` | `99.1068` |
| 3 | `99.1344` | `99.1344` | `99.1059` |
| 4 | `97.8309` | `97.8309` | `97.8147` |

Worst `100.3009 A` against the standing `+/-250 A` bound: **within limit**,
with `60%` of headroom. The `.raw` scan and LTspice's own `.meas` agree,
and both agree with A51's maxima to better than `0.06 A`.

### 6.2 Solver-corruption fingerprint

| Check | Result |
|---|---|
| points scanned | `252,547` |
| non-monotonic timestamps | `0` |
| duplicate timestamps | `0` |
| first / last timestamp | `0` / `2.5e-07 s` |
| `V(src)` at `t=0` | `0.0 V` - see note |
| `V(src)` min / max for all `t>0` | `48.0` / `48.0 V`, exactly |
| rail constant at its commanded `48 V` after `t=0` | **yes** |

**The `V(src)=0` at `t=0` is reported rather than suppressed, and is not
corruption.** Under `.tran ... UIC` LTspice emits one pre-source row at
`t=0`; the very next sample (`t = 1e-17 s`) is already exactly `48.0 V`,
and every subsequent sample is exactly `48.0 V`. LTspice's own
`.meas MIN V(src)` therefore reports `0`, which would be misleading if
quoted without this explanation. A dedicated flag
(`v_src_t0_row_is_uic_artifact`) records the discrimination in
`results.json`.

Note on naming: the task's fingerprint criterion is phrased as "`V(vin)`
staying at its commanded `48 V`". In A37's netlist `vin` IS the rail; in
A51's descriptor - which this netlist follows node-for-node - the rail is
`src` and `vin` is the node AFTER the `5 nH` input inductor, so `V(vin)` is
a dynamic node here by construction (`47.9698 V`, drifting `+3.6e-5 V`
over the period). The rail check above is therefore performed on `V(src)`,
which is the node that carries the commanded `48 V`.

## 7. Periodicity of the seeded state

`BOUNDARY.md` Section 6's third outcome asks whether SPICE reproduces the
periodicity itself, not just the ZVS verdicts. Comparing SPICE's state one
full period on (`t = 200 ns`) against the seed `z*`:

| Variable | seed `z*` | SPICE at `t=T` | drift |
|---|---:|---:|---:|
| `src` | `48.000000006872` | `48.000000000000` | `-6.87e-09` |
| `src_r` | `47.965690222367` | `47.965702056885` | `+1.18e-05` |
| `vin` | `47.969789939304` | `47.969825744629` | `+3.58e-05` |
| `tap3` | `36.000000000000` | `36.000026702881` | `+2.67e-05` |
| `tap2` | `24.000000000000` | `24.000019073486` | `+1.91e-05` |
| `tap1` | `12.000000000000` | `12.000009536743` | `+9.54e-06` |
| `a1` | `48.006773966740` | `48.006816789453` | `+4.28e-05` |
| `a2` | `24.036209731129` | `24.036094395712` | `-1.15e-04` |
| `a3` | `11.636445707834` | `11.636267941184` | `-1.78e-04` |
| `x1` | `11.742411388578` | `11.742302550216` | `-1.09e-04` |
| `x2` | `-0.021673678976` | `-0.021788204417` | `-1.15e-04` |
| `x3` | `-0.212533112253` | `-0.212709544334` | `-1.76e-04` |
| `x4` | `-0.471575654226` | `-0.471652755491` | `-7.71e-05` |
| `out` | `0.687890839361` | `0.687893331051` | `+2.49e-06` |
| `LPAR_IN` | `3.430978450469` | `3.429772716614` | `-1.21e-03` |
| `L1` | `-5.202377626634` | `-5.203108755520` | `-7.31e-04` |
| `L2` | `3.072420267431` | `3.088780885793` | `+1.64e-02` |
| `L3` | `30.358686656837` | `30.383891201874` | `+2.52e-02` |
| `L4` | `67.363213128783` | `67.374227233474` | `+1.10e-02` |

Worst-coordinate drift `2.52e-2` (on `L3`), relative residual
`3.74e-4` against the seed's infinity norm.

Every node voltage returns to within `1.8e-4 V`; the three flying-capacitor
voltages are preserved to `1.5e-4 V`. The drift is concentrated in the
phase currents (`L2`, `L3`, `L4`), at `1.1e-2` to `2.5e-2 A` on currents of
`3` to `67 A`.

**What this number is and is not.** A51's own fixed point converged to a
relative residual of `6.6e-9`, so SPICE's `3.7e-4` is five orders of
magnitude looser. This is a comparison between two different one-period
maps, and the honest reading is that it bounds the combined discretisation
difference of BOTH, not SPICE's error alone. A `2.52e-2 A` current drift
over `200 ns` on a `1.4667 nH` inductor corresponds to an average voltage
difference of only `1.85e-4 V` across that inductor - `0.19 mV`. A51's map
integrates with backward Euler at a `62.5 ps` coarse step, which carries
its own first-order error of that scale; SPICE used trapezoidal
integration at `1 ps`. The remaining contributors are the measured
`~1.13 ps` gate ramp on each of the eight commanded transitions per period,
LTspice's `SW` model transitioning smoothly rather than instantaneously,
and `cshunt=1e-15` (which is `8.7e-7` of the `~1155 pF` commutating
capacitance). **This experiment does not attempt to attribute the
`3.7e-4` between the two models, and no claim is made that it is SPICE's
error rather than A51's.** What it does establish is that the seeded state
is genuinely periodic under independent SPICE physics to within a
small fraction of a percent - `BOUNDARY.md` Section 6's third failure mode
(the state drifting materially) did NOT occur.

Independent corroboration from the operating point itself:

| Quantity | SPICE | A51 | Difference |
|---|---:|---:|---:|
| average `V(out)` over one period | `0.687945333889 V` | `0.687944 V` | `+1.3e-06 V` |
| average load power over one period | `89.9210490281 W` | `89.9207 W` | `+3.5e-04 W` |

## 8. Verdict (`BOUNDARY.md` Section 6)

**Outcome 1 occurred.** SPICE independently confirms that all four phases
achieve natural ZVS, at crossing times matching A51's own predictions to
between `0.107%` and `0.242%` against a `20%` pre-declared tolerance, with
every phase current inside `+/-250 A` and no solver-corruption fingerprint.

- Outcome 2 (some but not all phases, or materially different times) did
  NOT occur: all four phases agree, and no phase deviates by even `0.25%`.
- Outcome 3 (periodicity not reproduced) did NOT occur: the worst-
  coordinate drift over one period is `2.52e-2` on a state of infinity norm
  `67.4`, and the average output and delivered power reproduce A51's to
  `1.3e-6 V` and `3.5e-4 W`.

**There is no phase on which SPICE disagrees with the Python prediction.**
The only quantities worth flagging are (a) the `+0.1%` to `+0.25%` positive
bias in every crossing time, which shrinks when the timestep is refined and
is therefore consistent with residual discretisation in one or both models
rather than a physical disagreement, and (b) the `3.7e-4` relative
one-period residual discussed in Section 7.

### What this does NOT establish

Restating `BOUNDARY.md` Section 7, unchanged by the positive result:

- This is **not** a P24 reproduction claim. Section 1's state is
  `SENSITIVITY_ONLY`, a reduced-load (`89.92 W`) operating point, not P24's
  rated `250 W`.
- The more realistic asymmetric `RHS=7 mOhm`/`RLS=3.5 mOhm` was NOT tested
  and is explicitly out of scope; it requires its own fresh Python re-solve
  first to obtain a self-consistent seed.
- Nonlinear `Coss(V)` was not tested; `CH`/`CL` are the fixed `Co(tr)`
  values, which are specified for a `0-to-50 V` transition and applied here
  to a `~11.6 V` transition (an extrapolation inherited unchanged from
  A37/A42/A49/A51).
- Nothing here was solved or searched: the state came from A51 and the
  question asked was only whether independent SPICE physics agrees.

## 9. Files

Produced by this experiment (nothing under `src/scb_ivr/`,
`paper_locked/02_ectc2024_main/`, `results/`, or A37/A42/A48/A50/A51 was
modified; `solver_copy` and A51's modules are imported read-only):

- `a52_boundary.py` - shared boundary, `z*`, Section 4 targets, and the
  `commanded_pwm_mode` bisection (no offset formula anywhere)
- `derive_windows.py`, `derive_windows_log.txt`, `window_derivation.json`
- `build_pilot.py`, `run_pilot.py`, `pilot/` (8 netlists + logs),
  `pilot_results.json`
- `meas_log.py` - `.meas` log parser with a pinned self-test
- `build_full_netlist.py`, `netlist_metadata.json`
- `A52_spice_crosscheck_reduced_load_zvs.cir` / `.log` / `.raw`
- `A52_spice_crosscheck_reduced_load_zvs_step250f.cir` / `.log` / `.raw`
- `analyze_results.py`, `analysis_log.txt`, `results.json`
- `scripts/ltspice_raw_parser.py` - copied verbatim from
  `R04E26_periodic_orbit_ic_swap/scripts/`, per this project's standing
  convention of not re-deriving an already-verified raw parser
- `RESULTS.md` (this file)

The `.raw`, `.log` and `.db` outputs are produced locally but are NOT
committed: `tools/GITHUB_CHECKPOINTS.md` excludes LTspice raw/log/db files
from this repository. Every number quoted above therefore also lives in a
committed artifact - `results.json` (complete machine-readable record,
including both runs' fingerprint, safety, per-phase and periodicity data),
`pilot_results.json`, `window_derivation.json`, `analysis_log.txt` and
`derive_windows_log.txt` - so the full result is reproducible and
re-checkable from the committed `.cir` files plus these scripts without
the binaries.
