# First-principles `Cfly` estimate for P24's own operating point (2026-09-15)

## Why this exists

`CURRENT_ASSUMPTION_CROSSCHECK.md`'s "Flying capacitor" and "Output
capacitor value" rows record that this project's `Cfly=53.8 uF` and
`Cout=4.672 mF` were both traced to EPE2019 Table I, which is that paper's
own **CSC-buck** prototype parts list -- a different, topologically
modified converter from the conventional SC buck P24 actually is, whose
`C1` must block a voltage stress the CSC buck's own redesign specifically
avoids. That finding does not, by itself, supply a better number -- it only
shows the old one is not defensible. This document derives an independent,
first-principles estimate for `Cfly` from P24's own published operating
point, so Track B work has a second, better-grounded candidate to compare
against (or to replace `53.8 uF` with) rather than continuing to lean on a
cross-topology borrow.

**This is a derived sensitivity estimate, not a paper value and not a
replacement conclusion.** It depends on a ripple-percentage target this
project is choosing, not one P24/P25 state numerically -- exactly the kind
of free assumption this project's protocol requires to be labelled as such
(`NUMERICAL_IDEALIZATION`/`SENSITIVITY_ONLY`), not silently promoted.

## Method

Each flying capacitor charges through its own phase's inductor during that
phase's `Ton` and discharges through an adjacent phase's inductor during
the following interval (`PAPER_LOCKED_REPRODUCTION_BASELINE.md`: "each
series capacitor... charges through the inductor of the same phase and
discharges through the inductor current of its adjacent phase, ensuring an
Amp-Sec balance"). Approximating the boundary-mode triangular phase current
(`0` to `Ipk=125 A` over `Ton`) by its average (`Ipk/2`) during the
charging interval gives the charge delivered to the capacitor each period:

```
dQ = (Ipk/2) * Ton
```

With P24's own Eq.-1/Eq.-2/Eq.-3 values (`Vin=48 V`, `Vo=1 V`, `nP=4`,
`nM=4`, `fsw=5 MHz`, `Ipk=125 A`, `Ton=16.667 ns`, all already `LOCKED` in
`SOURCE_COVERAGE_MATRIX.md`):

```
dQ = 62.5 A * 16.667 ns = 1.0417 uC per cycle
```

The steady-state peak-to-peak ripple this charge swing produces on a
capacitance `C` is `dV = dQ/C`, so for a target ripple `dV` expressed as a
percentage of that capacitor's own DC bias voltage (`C1~=36 V`, `C2~=24 V`,
`C3~=12 V`, the same `3Vin/4, Vin/2, Vin/4` targets already used
throughout this project):

```
C = dQ / dV = dQ / (Vdc * ripple_pct)
```

## Result

| Position | `Vdc` | `C` at 1% ripple | `C` at 2% ripple | `C` at 5% ripple |
|---|---:|---:|---:|---:|
| `C1` | 36 V | 2.89 uF | 1.45 uF | 0.58 uF |
| `C2` | 24 V | 4.34 uF | 2.17 uF | 0.87 uF |
| `C3` | 12 V | 8.68 uF | 4.34 uF | 1.74 uF |

`C3` (the lowest-voltage position) needs the most capacitance for a given
ripple percentage, since the same absolute charge swing produces a larger
*relative* ripple on a smaller DC bias. If a single shared `Cfly` value is
used for all three positions (this project's and EPE2019's own convention),
`C3`'s requirement is the binding constraint.

**Across this entire 1%-5% ripple range (a reasonable design-target band,
not a paper-given one), every computed value is well below `53.8 uF`** --
by roughly 6x (`C3` at 5%) to 90x (`C1` at 1%). This is independent
evidence, from P24's own operating point rather than from re-reading
EPE2019, that the previously-used `53.8 uF` was very likely oversized for
this converter, consistent with (though not proof of, on its own) the
already-documented cross-topology provenance problem.

## What this does and does not establish

Establishes: an order-of-magnitude, first-principles candidate range
(`~0.6-8.7 uF` depending on which position and which ripple target)
derived entirely from P24's own locked specification, with no dependence
on EPE2019 or any other cross-source table. Provides a second data point
against which the flagged `53.8 uF` can be judged, independent of the
Table-I provenance argument.

Does not establish: a single correct value (the ripple-percentage target is
this project's own choice, not a paper-given number -- P24/P25 state no
numeric flying-capacitor ripple tolerance anywhere, which is exactly item 3
of the progress report's Section 8 request to Mihai); ESR/ESL; a real,
procurable part (unlike the flagged `53.8 uF`, which at least corresponds
to an actual assembled capacitor bank in a real prototype, just the wrong
one); or ripple contributions from anything other than the single-phase
charge/discharge mechanism modelled here (e.g. four-phase interaction,
transient load steps, or the DC-bias capacitance derating this project has
already discussed for MLCC-class parts, which would push the *needed*
capacitance for a given physical part upward again).

## Cout is not estimated here -- different, currently-unresolvable sizing basis

`Cout`'s sizing in an interleaved multi-phase converter is typically driven
by load-transient response (how much output voltage is allowed to droop
for a given load current step) rather than switching ripple, since
four-phase interleaving already cancels most of the output ripple. This
project has no target transient-response specification (allowed `dV` for a
given `dI/dt`) from P24/P25 or from Mihai, so no comparably-grounded
first-principles `Cout` estimate can be produced the way `Cfly` was here --
this is a separate, currently open gap, not silently assumed equal in
character to the `Cfly` finding above.

## Next permitted action

This range is available as a candidate substitute for `Cfly=53.8 uF` in a
future, explicitly-labelled Track-B experiment (a new, separately-numbered
run, not a silent edit to R00-R04E7's existing results). It must not be
read as confirming or replacing any existing experiment's numeric
conclusions on its own.
