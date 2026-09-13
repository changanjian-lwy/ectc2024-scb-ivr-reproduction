# Step 22 - R04D3E calibrated ZVS exit acceptance

## Frozen boundary

R04D3E originally accepted the mathematical threshold `7.77%`. After the
margin sweep, it imports the current ideal-model operating default `8%` from
`negative_current_targets.lib`.  It changes no R04D3 topology, initial state,
inductance, capacitance or switch-population value.  The simulation stops just
after the hand-off; subsequent high-side dynamics belong to the next stage.

## Acceptance result

1. `QL1` gate falls at 14.9298 ns with `iL1=-10.0009 A`.
2. Reverse current commutates the node for 1.84378 ns.
3. `Vds(QH1)=0` at 16.7732 ns while `iL1=-2.37994 A`.
4. `QH1` gate rises at 16.7736 ns while `iL1=-2.37694 A`.
5. Event-to-gate numerical delay is 0.402 ps.
6. Maximum gate-overlap monitor is zero.
7. At 16.82 ns, `QL1` gate is 0 V, `QH1` gate is 5 V and high-side Vds is
   -14.58 mV in the ideal switch model.

The ideal physical-event order is accepted.  The high-side turn-on occurs
with negative current and no simultaneous gate command.

## Margin boundary

The calibrated 7.77% value remains the minimum numerical crossing. The ideal
continuation default is 8%, which leaves about 2.38 A negative current at the
high-side gate event. Device tolerance, nonlinear capacitance, propagation
delay and parasitics are absent, so 8% is not claimed as a hardware-qualified
value and does not overwrite the paper-source 1%, 2%, 5% and 10% entries.

## Numerical isolation

An initial 25 ns acceptance run suffered timestep collapse after QH1 turn-on
and produced a 140 MB incomplete raw file.  That generated file was removed.
The accepted test stops at 16.75 ns because its scope is only the exit event;
post-turn-on evolution will be introduced as the next independently bounded
stage.
