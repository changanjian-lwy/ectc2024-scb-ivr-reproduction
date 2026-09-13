# Step 14 - R04D0 shared-ladder first-interval test

## Why this precedes a charge-balance test

A complete periodic charge-balance measurement requires every charge and
discharge interval to be defined. P24 explicitly describes the first-phase
interval but does not publish the complete four-phase gate vector or numeric
Coss/dead-time transition. Therefore the shared network is introduced first
only for the P24-explicit `QH1 + QS2` state.

## Change relative to R04C

The independent stiff `Vin/nP` sources are replaced by the P24 Fig. 3 shared
48-V flying-capacitor ladder. Only `QH1` and the adjacent phase low-side `QS2`
are commanded ON for the P24 Eq. (3) on-time.

Everything else remains bounded:

- `nP=4`, `nM=1`, `Vin=48 V`, `Vo=1 V`, `fsw=5 MHz`;
- `Ton=16.6667 ns` and selected Eq. (4) `L=1.46667 nH`;
- stiff 1-V output and ideal switches;
- no post-on-time commutation, periodic reset, startup, ZVS or loss model.

## Capacitor initialization

`36/24/12 V` are applied only as capacitor initial conditions representing the
candidate periodic operating state. The experiment does not test self-balance.
`Cfly=53.8 uF` is an explicitly labelled cross-source numerical enabler from
EPE2019 because P24/P25 omit the capacitance; it is not fitted and cannot be
reported as the P24 design value.

## Acceptance / failure interpretation

The main check is causal: the shared ladder should place approximately 12 V at
the phase-1 switching node, so L1 should see approximately 11 V and approach
the R04A 125-A peak during `Ton`. The sign of `iL2` and charge moved through C1
and C2 are recorded to verify the adjacent-phase path.

If this fails, retain the failure as a topology/orientation/state-definition
problem. Do not repair it by changing Cfly, initial capacitor voltages,
inductance or on-time.

## Result

### R04D0-A - retained numerical failure

The first execution stopped immediately with `Singular matrix: node a1`.
Before the first commanded edge, the ideal switches isolate parts of the
capacitor ladder and leave no DC reference for the numerical solver. This is a
numerical initialization failure, not evidence for or against the P24 power
stage.

### R04D0-B - permitted next attempt

The only change is a `1 Tohm` reference from each potentially floating internal
node to the module reference. At 48 V its worst-case leakage is 48 pA, so it is
treated as a numerical reference rather than a physical balancing network.
No paper parameter or switching state is changed.

Result: the `1 Tohm` references remained below the useful conductance range of
the numerical solver and the same singular-node failure was retained.

### R04D0-C - permitted numerical-reference adjustment

Only the reference resistance is reduced from `1 Tohm` to `1 Gohm`. Its
worst-case 48-nA leakage transfers less than `1e-15 C` during this experiment,
which is negligible relative to the stated cross-source 53.8-uF capacitor.
If this still fails, the resistance must not be reduced again merely to force
convergence; the next investigation must be the initial switch-state topology.

Pending execution.

Result: the same singular-node failure remained. This rules out insufficient
reference conductance as the useful explanation.

### R04D0-D - start directly in the published state

The earlier attempts included a 1-ns all-OFF interval before `QH1+QS2`. P24
does not define that interval, and without the omitted Coss/diode network the
ideal capacitor ladder has no physically defined clamp during it.

R04D0-D therefore begins with `QH1` and `QS2` already ON, retains only the
two-phase subnetwork participating in this explicitly described interval, and
ends at `Ton`. This is a local state-equation test. It must not be presented as
the complete four-phase Fig. 3 network or as a startup solution.

Status: **PASSED_LOCAL_P24_INTERVAL_1**.

| Quantity | Result | Interpretation |
|---|---:|---|
| `iL1` maximum | 124.933 A | agrees with the R04A/P24 Eq. (4) 125-A branch |
| `iL2(Ton)` | -11.351 A | `QS2` clamps phase 2 low, so L2 sees about `-Vo` |
| `VC1` | 36.0000 -> 36.01931 V | C1 is charged during the phase-1 interval |
| charge through C1 | 1.03898 uC | matches `C1*(VC1_end-VC1_start)` on the identical measurement window |
| charge through C2 | -0.000000965 pC | effectively zero in this local state |

The expected ideal values independently support the result:

- `Delta iL1 = (Vin-VC1-Vo)*Ton/L = 125 A`;
- `Delta iL2 = -Vo*Ton/L = -11.364 A`;
- full-interval triangular L1 charge is approximately
  `0.5*125 A*Ton = 1.0417 uC`; the reported 1.03898-uC value excludes 20 ps
  from both endpoints so that its window exactly matches the voltage samples.

This verifies only the charging half of P24's capacitor-balance statement:
the same-phase inductor charges C1. The later adjacent-phase discharge of C1
has not yet been executed, so no charge-balance or self-balancing claim is
permitted.

## Next permitted experiment

Rotate into the next P24-supported adjacent-phase state and measure the charge
removed from C1. Keep the transition between the two states symbolic or
instantaneous and explicitly exclude it from any ZVS claim until Coss and dead
time are available. Only after charge-in and charge-out are both defined may a
full-period average capacitor current be evaluated.
