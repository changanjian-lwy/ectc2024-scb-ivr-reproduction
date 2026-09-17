# Zero-start boundary and mathematical-model audit

## Decision

The latest Track-B boundary is sufficiently explicit to build a mathematical
model, but it is not P24's published startup method. It is a labelled
`CROSS_PAPER_EXTENSION` composed of four replaceable modules:

1. P24 single-module, four-phase power-stage connectivity;
2. IPEC-derived passive divider/precharge diodes;
3. Roberts-derived slow input-voltage ramp;
4. fixed 5 MHz, four-phase PWM active from `t=0`.

The correct mathematical object is a hybrid descriptor system, not the P24
steady-state triangular-current formula alone:

`E dz/dt + A_sigma z = r(t)`.

`sigma` contains the commanded high-/low-side switch state and the three
state-dependent precharge-diode states. Diode-state changes require
complementarity/event conditions, so the complete problem is a piecewise
linear DAE.

## Boundary items that are correct

- All flying capacitors, the output capacitor and all inductors begin with
  zero stored energy. No 36/24/12 V state is imposed.
- The output begins at zero and is not held by the Track-A ideal 1 V clamp.
- `nP=4`, 48 V, 1 V, 250 W per module and 5 MHz remain explicit.
- The passive divider can be removed without changing the P24 power-stage
  equations; this permits a clean `{divider present, divider absent}` branch.
- Input ramp, component assumptions and PWM timing are written as parameters,
  not hidden inside an initial condition.

## Boundaries that must not be overclaimed

- This is one 250 W module, not the complete four-module 1 kW assembly.
- The divider and precharge-diode network is a four-phase extrapolation from a
  different paper; P24/P25 do not publish it.
- `Cfly=3 uF`, `Cdiv=300 uF` and `Cout=4.672 mF` are not P24 component values.
- `Ron=1 uOhm`, ideal diodes, zero dead time, no nonlinear `Coss`, no driver
  delay and no package parasitics make this a topology-principle model.
- `RLDAMP=1 uOhm` is effectively an almost lossless inductor series resistance,
  not a meaningful physical damping element. Future files should call it
  `R_LPHASE`, not infer startup damping from it.
- The 4 mOhm resistor is a constant 250 W load only at 1 V. A real processor
  does not necessarily present that load during startup.
- The `+/-250 A` classification used in R04E17/E18 is a project engineering
  screen, not a published device or module limit.
- PWM-from-`t=0` is borrowed from the Roberts demonstration choice. It is not a
  P24/P25 release rule.

## State and mode definition

The compiled MNA vector contains all node voltages, five inductor currents
(`LPAR_IN`, `L1..L4`) and the input-source current. Energy storage comprises:

- four optional divider capacitors;
- three flying capacitors;
- the output capacitor;
- the input parasitic inductor and four phase inductors.

For each fixed switch/diode mode, the matrices are linear and the descriptor
pencil is nonsingular at the audit point. The compiled model has 20 MNA
variables and differential rank 13, exactly matching eight capacitor and five
inductor storage degrees of freedom. Therefore the present boundary is
mathematically formulable from exactly zero stored energy. This structural
result does not yet establish that its trajectory is safe or converges.

## Required next mathematical steps

1. Add diode complementarity checks: on-state current must be nonnegative and
   off-state anode-cathode voltage must be nonpositive.
2. Integrate mode by mode between PWM edges, diode events and input-ramp
   breakpoints while conserving capacitor charge and inductor flux.
3. Derive a switching-period map `x[k+1]=F(x[k], Vin[k])` from the exact model.
4. Average that map only after comparing it against several exact periods.
5. Test reachability of a Track-A periodic state, not merely proximity to
   36/24/12/1 V: currents, capacitor charges and controller mode must also
   match the handoff surface.

## R04E19 pre-run boundary correction

R04E19 proposes changing `Cfly` while holding `Cdiv=300 uF`. This is a useful
system-sensitivity experiment, but it is not a pure test of the Roberts
`1/sqrt(Cfly)` resonance law. The same change moves at least two independent
dimensionless groups:

- normalized ramp duration `Tramp * f_res`;
- passive charge-divider ratio `Cdiv/Cfly`.

For the two 30x-margin cells, `Tramp*f_res` is approximately the same (`10.5`),
but `Cdiv/Cfly` changes from `500` at `0.6 uF` to about `34.48` at `8.7 uF`.
Consequently R04E19 may establish whether the complete divider-present model
is robust across `Cfly`; it cannot attribute a difference uniquely to
resonance-frequency scaling. A later mechanism-isolation branch would need to
control the capacitance ratio or include it explicitly in a multi-variable
fit.

The implementation in `src/scb_ivr/zero_start_descriptor.py` completes the
model-contract and per-mode matrix construction. It deliberately stops before
numerical integration so that diode event rules and the startup load boundary
can be audited before another long simulation.
