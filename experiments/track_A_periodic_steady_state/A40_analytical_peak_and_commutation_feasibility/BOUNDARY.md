# A40 analytical peak-current and commutation-feasibility boundary

Track: A analytical audit. No LTspice run is authorized or performed here.

## 1. Parent experiment

A39, which separated H2 admission-current pinning from the common
`RDS(on)` current-ramp derating. A40 also uses the global model-layer split
introduced in commit `6480590`.

## 2. What changed

One analytical module was added. It contains two independent equation sets:

1. `P24_IDEAL` lossless high-side current rise.
2. `P25_DEVICE_AUGMENTED` constant-drive RL current rise and P25 Mode-5
   capacitor-commutation feasibility derived from Eqs. (13)-(14).

No controller, topology, device library, initial state, threshold, netlist or
archived simulation result was modified.

## 3. Locked inputs and provenance

| Input | Value | Provenance |
|---|---:|---|
| `Vin`, `Vo`, `nP`, `Ton`, `Ipk` | 48 V, 1 V, 4, 16.667 ns, 125 A | P24 Eqs. (1)-(3) |
| phase voltage step | 12 V | P24 four-level ladder, `Vin/nP` |
| drive voltage during rise | 11 V | P24 Eq. (3), `Vin/nP-Vo` |
| main `L` | 1.4667 nH | recalculated P24 Eq. (4), locked project decision |
| conflicting `L` | 2.68 nH | P24 Table I, audit only, not promoted |
| negative-current cases | 1%, 2% of 125 A | P24 Section II-B |
| high-side device capacitance | 385 pF | GS61008T charge-equivalent library; external device data |
| low-side device capacitance | 770 pF | two parallel GS61008T devices; external/P25 population data |
| `RDS(on)` | 7 mOhm | P25 Table III |
| reverse-conduction drop | unresolved; ideal audit uses 0 V | P25 equation symbol exists but value is not published |
| external `CH/CL` snubbers | unresolved; no value selected | P24/P25 omit values |

## 4. Capacitance-participation branches

- `P25_EQ13_HIGH_ONLY`: use the `CH` position explicitly present in P25
  Eq. (13). In the current component abstraction this is
  `CH_DEVICE+CH_SNUBBER`.
- `NODE_SUM_ENVELOPE`: count both high- and low-side capacitances moved by a
  switching-node transition. This is a `GENERAL_PHYSICS_ONLY` conservative
  envelope, not a claim that P25 Eq. (13) contains `CH+CL`.

These interpretations are not merged. The coming SPICE sweep must report
both until the exact topology-level charge participation is verified.

## 5. Questions

1. Is the P24 125-A value an absolute endpoint or the zero-admission lossless
   current rise?
2. Does adding 7 mOhm explain the common ramp derating without explaining
   H2's separate admission-current pinning?
3. Under P25 Eq. (13), how long do P24's 1% and 2% negative-current cases
   require to commutate a declared capacitance, and what capacitance is
   allowed after an external Mode-5 time budget is supplied?
4. Does increasing snubber capacitance help or reduce the available ZVS
   margin under a fixed negative-current target?

## 6. Success condition

The equations reproduce P24's 125-A zero-admission ideal result, reproduce
A39's RL slope factor, and provide explicitly labelled P25 time-law and
general-physics energy envelopes without selecting an unpublished snubber
value or inventing a Mode-5 deadline.

## 7. Failure condition

Do not claim a unique `CH/CL` value, Mode-5 capacitance ceiling, or hardware
ZVS prediction without a declared available time. If the capacitance-
participation or time-budget interpretations differ, preserve them as
uncertainties for the next sweep. Do not use P24 Table I's 2.68 nH to rescue
the main 1.4667-nH branch.

## 8. What this experiment cannot prove

It cannot prove ZVS in the complete four-phase topology, select dead time,
model nonlinear `Coss(V)`, establish a periodic orbit, or validate startup,
loss, thermal or package behavior.
