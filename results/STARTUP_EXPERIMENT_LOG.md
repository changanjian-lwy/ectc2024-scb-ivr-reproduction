# SCB startup experiment log

All tests use the ECTC 2024 four-phase, four-module, 48 V to 1 V, 1 kW
topology.  Flying capacitance is 27.34375 uF from APEC 2025 Eq. (23), with
an allowed capacitor ripple of 0.12 V.  No capacitor voltage IC statements
are used.

## E0 - Fixed-PWM baseline

**Reference:** sourced-parameter baseline.

**Inputs:** 5 MHz fixed interleaved PWM; PWM enabled at 5 us; input rises
from 0 to 48 V in 40 us; no precharge or balancing controller; 2.68 nH per
phase.

**Result:** completed, failed the operating-point target.

| Metric | E0 result |
|---|---:|
| Vout | 0.35414 V |
| C1 / C2 / C3 | 12.9705 / 8.6258 / 4.3470 V |
| L1 max / min | 22.768 / -3.245 A |
| Startup input-current peak | 200.927 A |

**Conclusion:** fixed normal PWM does not establish the intended capacitor
ladder from zero under this startup condition.  The current surge is also
unacceptable.

**Next adjustment indicated:** add an explicit startup function before
changing steady-state duty ratio or inductance.

## E1 - Current-limited functional precharge

**Compared with:** E0.

**Independent changes:** add a 10 A maximum controlled precharge branch to
each flying capacitor; track targets 0.75Vin, 0.50Vin and 0.25Vin; delay the
5 MHz PWM enable from 5 us to 140 us.  All power-stage values, input ramp,
load, normal PWM duty and interleaving remain unchanged.

The precharge branch is a functional abstraction of the two auxiliary FETs
in Reusch et al.  It does not yet model their floating gate drives or draw
the precharge energy through a fully physical auxiliary path.

**Result:** completed; strongly improved, but did not fully reach the target.

| Metric | E0 | E1 | Change |
|---|---:|---:|---:|
| Vout | 0.35414 V | 0.69708 V | +96.8% |
| C1 | 12.9705 V | 31.1818 V | +18.2113 V |
| C2 | 8.6258 V | 21.6515 V | +13.0257 V |
| C3 | 4.3470 V | 11.2143 V | +6.8673 V |
| Startup input-current peak | 200.927 A | 49.696 A | -75.3% |
| L1 max / min | 22.768 / -3.245 A | 40.824 / -11.389 A | larger ripple and reverse current |

**Conclusion:** sequencing precharge before the normal PWM is effective and
greatly reduces the source-current surge.  The 140 us precharge interval is
too short for the largest capacitor target, and the post-enable operating
point is still below 1 V.  The negative current also shows that dead time and
the transition from precharge to boundary operation require control.

**Next adjustment indicated:** keep the 10 A limit and extend precharge enable
to approximately 220-300 us; record capacitor voltages immediately before
PWM enable; then ramp duty/frequency instead of applying full 5 MHz operation
as a step.  Only increase IPRE after checking auxiliary-device SOA.

## E2 - Slow-ramp, low-frequency natural-balancing screen

**Compared with:** E0.

**Independent changes:** input ramp 40 us to 10 ms; switching frequency
5 MHz to 100 kHz; phase inductance 2.68 nH to 134 nH as the dependent Table-1
frequency scaling; dead time 2 ns to 20 ns.  No precharge is added.

**Result:** numerical/computational failure, deliberately retained as an
experiment result.  The complete 16-phase switching model generated more
than 1 GB of raw data and was still running after about six minutes, so it
was stopped before final measurements were available.

**Conclusion:** a millisecond-scale natural-balancing search should not be
performed directly in the full nanosecond-resolution transistor-level model.
This run neither proves nor disproves natural self-precharge.  It proves that
the selected simulation level is unsuitable for finding the startup
frequency and ramp time.

**Next adjustment indicated:** construct an averaged or state-space startup
model first; sweep the input-ramp time, startup frequency and modulation law;
extract the slow balancing eigenmode; then replay only the selected short
transition in the full LTspice model.  Also determine what "zero modulation"
means for this DC-DC SCB, because the inverter paper's gating law cannot be
copied directly.

## Current decision

E1 is the actionable implementation route.  E2 remains a research route but
requires a reduced-order model before another full switching run.  Neither
result should yet be interpreted as an efficiency or hardware-SOA result.
