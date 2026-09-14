# A40 analytical peak-current and commutation-feasibility results

Grade: `PASS_ANALYTICAL_BOUNDARY / MISSING_MODE5_TIME_BUDGET_AND_CAP_PARTICIPATION`.
No LTspice simulation was run.

## 1. Current-rise audit

With `Vdrive=48/4-1=11 V`, `Ton=16.667 ns` and `L=1.4667 nH`:

| Admission current | P24 ideal endpoint | 7-mOhm RL endpoint |
|---:|---:|---:|
| 0 A | 125.000 A | 120.158 A |
| -1.25 A (P24 1%) | 123.750 A | 119.003 A |
| -2.50 A (P24 2%) | 122.500 A | 117.849 A |

Therefore P24's exact 125-A result is the lossless current rise from zero,
not an unconditional endpoint after a high side is admitted with residual
negative current. P25 says `V_CH2` must return to zero by high-side turn-on,
but it does not publish the exact admission current for the P24 case. A39's
H2 admission at about -1.29 A is consequently a property of the present
numerical event model, not a value printed by P24.

The RL memory factor is
`exp(-R*Ton/L)=0.923536`, matching A39's measured `0.9219-0.9236` sensitivity.
This confirms that 7 mOhm explains the common ramp derating, while A39's
separate H1/H2 endpoint difference remains dominated by admission-current
pinning.

## 2. P25 Mode-5 time law recovered from Eq. (13)

Using P25 Eq. (11) to replace the `t43` term inside Eq. (13) gives

```text
tcomm = 2*Cparticipating*DeltaV/|Ineg|
```

The factor two is retained from the printed Eq. (13). The paper does not give
an independent fixed Mode-5 deadline, so Eq. (13) alone does **not** produce a
unique maximum snubber capacitance. Once an allowed Mode-5 time
`tavailable` is supplied, the corresponding parameterized ceiling is

```text
Cmax_time = |Ineg|*tavailable/(2*DeltaV)
```

The available time must come from the physical event schedule, measured dead
time/controller delay, or a separately declared design constraint. It may not
be borrowed from Mode 4's negative-current build time.

## 3. P24 1%-2% commutation times for the present high-side abstraction

Using `DeltaV=12 V` and `CH_DEVICE=385 pF`, with no external snubber:

| P24 negative target | `Ineg` | P25 Eq. (13) `tcomm` |
|---:|---:|---:|
| 1% | 1.25 A | 7.392 ns |
| 2% | 2.50 A | 3.696 ns |

These are required times, not pass/fail results. Whether either reaches ZVS
depends on the still-unresolved Mode-5 available window and on whether
385 pF is the correct participating capacitance for the 12-V transition.

For equal added high-side snubber capacitance, Eq. (13) predicts a linear
increase in time. At the 2% target each additional 1 nF adds 9.6 ns; at the
1% target it adds 19.2 ns. Thus a larger snubber slows the transition under a
fixed current. It can reduce turn-off `dv/dt` and voltage-current overlap, but
it does not automatically improve the following turn-on ZVS margin.

## 4. Separate general-physics energy envelope

The project's common-physics layer also records the isolated-LC necessary
condition

```text
0.5*L*Ineg^2 >= 0.5*Cparticipating*DeltaV^2
```

This is not P25 Eq. (13), and it is valid only if the selected `L` and `C`
represent the isolated commutating energy pair. Under that explicit
assumption, with `L=1.4667 nH` and `DeltaV=12 V`:

| Capacitance interpretation | C | minimum `Ineg` | Fraction of 125 A |
|---|---:|---:|---:|
| high-side device only | 385 pF | 6.148 A | 4.919% |
| high+low node sum | 1155 pF | 10.649 A | 8.519% |

The earlier full switching model's 7.77% numerical threshold lies between
these two energy envelopes. That is suggestive, but not proof, that more than
the high-side `CH` alone participates while less than the simple full node sum
acts as one isolated capacitor. Cross-phase paths, rail energy exchange,
nonlinear `Coss(V)`, clamp behavior and event timing prevent promoting either
envelope to the final topology equation.

The same isolated-LC assumption would allow only 15.91 pF at 1% and 63.66 pF
at 2%. These numbers deliberately remain `GENERAL_PHYSICS_ONLY`; they must not
be called P25 snubber limits.

## 5. Answer to the audit question

The analytical work does not yet justify saying "1-2% requires approximately
X nF." It establishes the correct direction and the missing inputs:

- P25 Eq. (13): 385 pF needs 7.392 ns at 1% or 3.696 ns at 2%; a maximum
  capacitance requires the unpublished allowed Mode-5 time.
- The isolated-energy envelope predicts a much higher current requirement,
  but its capacitance participation is topology-dependent.
- Adding positive snubber capacitance increases the required charge/time and
  energy. If a future full-topology sweep shows that added snubber makes the
  P24 1-2% branch succeed, the improvement must come from changed voltage
  sharing or event dynamics, not from reduced charge demand.

## 6. Next permitted experiment

Create A41 as two separately reported sensitivity branches:

1. `P25_EQ13_TIME_LAW`: calculate `tcomm(CH)` for P24 1% and 2% without
   asserting pass/fail until `tavailable` is declared.
2. `FULL_TOPOLOGY_SPICE`: sweep `CH_SNUBBER` first with `CL_SNUBBER=0`, then
   sweep symmetric `CH_SNUBBER=CL_SNUBBER` separately.
3. Record actual ZVS crossing time, current at crossing, event-slot margin,
   controller blocking, and inferred participating charge.
4. Keep `L`, `Ton`, topology, initial state, device Coss and negative-current
   target fixed within each branch.
5. Do not select or promote an unpublished snubber value from the sweep.
