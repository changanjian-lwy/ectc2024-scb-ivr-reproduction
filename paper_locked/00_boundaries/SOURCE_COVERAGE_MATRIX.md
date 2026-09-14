# Source coverage matrix and no-omission gate

## Status meanings

- `LOCKED`: visually checked against the PDF and allowed in the main model.
- `TRANSCRIBE`: relevant but not yet transcribed/visually checked.
- `TEST`: implemented, but numerical validation is incomplete.
- `MISSING`: the paper does not provide the value or implementation.
- `CONFLICT`: two printed statements or calculations disagree.
- `N/A`: background material not used by the present circuit model.

No model may advance from one phase/module level to the next while a required
row remains `TRANSCRIBE`. `MISSING` rows must remain named variables and
`CONFLICT` rows must become separate experiments.

## 2024 ECTC coverage

| Source item | Model role | Status |
|---|---|---|
| Fig. 1 | system/PDN context only | N/A for PF-S25/PF-S24 circuit core |
| Fig. 2 | CCM vs boundary sequence and negative-current ZVS mechanism | LOCKED |
| Fig. 3 | multi-phase/multi-module SCB connectivity | LOCKED |
| Fig. 4 | theoretical phase/interleaving waveforms | LOCKED |
| Eq. (1) | `D=nP*Vo/Vin` | LOCKED |
| Eq. (2) | `ILpk=2Io/(nP*nM)` | LOCKED |
| Table I | 48 V/1 V phase/module/frequency design targets | LOCKED; L column CONFLICT |
| Eq. (3) | `Ton=nP*Vo/(fsw*Vin)` | LOCKED; visually checked on PDF p. 5 |
| Eq. (4) | critical inductance | LOCKED; conflicts with Table I |
| Eqs. (5)-(6) | embedded-inductor parallel count and unit inductance | LOCKED; visually checked on PDF p. 6 |
| Sec. II-B interval 1 | high-side energy-transfer path | LOCKED |
| Sec. II-B interval 2 | high-side turn-off and low-side Coss commutation | LOCKED |
| Sec. II-B interval 3 | 1-2% negative current and high-side Coss discharge | LOCKED |
| Fig. 5 | conceptual 3-D package integration | TRANSCRIBE before package layer |
| Fig. 6 | estimated package dimensions | TRANSCRIBE before package layer |
| Table 3 | embedded-inductor and EPC GaN switch/parallel-count selection per `nP`/`nM` (e.g. `nP=4`,`nM=4`: 2x EPC2067 HS, 3x EPC2067 LS) | LOCKED (2026-09-14); scope caveat below |
| named high-/low-side device and driver for the Sec. II-B ZVS circuit itself | required device model | MISSING (Table 3's EPC2067 selection is Sec. IV's embedded/3-D-package concept; not yet confirmed to be the same device intended for Sec. II-B's commutation mechanism) |
| flying/output capacitor values and parasitics | required hardware model | MISSING |
| exact ZCD/dead-time/startup implementation | required controller/startup model | MISSING |

## Cross-source startup literature

| Source item | Model role | Status |
|---|---|---|
| APEC 2016 Sec. IV-B, Fig. 3, Eq. (5) | active current-source precharge principle and delay equation | LOCKED; exact four-phase circuit MISSING |
| IPEC 2018 Figs. 2, 4, 8(e), Secs. III-IV | passive split-input-capacitor precharge and stated N-level extension | LOCKED as replaceable startup candidate |
| IPEC 2018 Table II | `Lpar=5 nH`, `Rpar=10 mOhm`, `Cin1=Cin2=10 uF` for its 24-V 3L prototype | LOCKED; cross-source sensitivity only |
| IPEC 2018 four-phase SCB wiring | exact P24-compatible diode/divider implementation | MISSING; R02A is labelled extrapolation |
| TPEL 2018 modified SC HCR topology | alternative topology eliminating startup voltage stress | N/A for unchanged P24 Fig. 3 power stage |
| ECCE 2015 automatic current sharing | later charge-balance/current-sharing validation | LOCKED for principle; not a startup module |
| OJPEL 2024 Eq. (1), Sec. II | `D<1/N`, adjacent-main-switch non-overlap, phase-sequence rules | LOCKED for steady-state modulation |
| OJPEL 2024 star sequencing | duty extension for high phase count | N/A to the present `N=4`, `D=1/12` module |
| OJPEL 2024 Appendix | large-signal state propagation under forced CCM/CVM | LOCKED but not valid as a DCM startup-release law |

## 2025 APEC coverage

| Source item | Model role | Status |
|---|---|---|
| Fig. 1 | 3-phase/2-module connection, grounded low sides, CH/CL placement | LOCKED |
| Fig. 2 | 15-mode waveform order and module phase shift | LOCKED |
| Fig. 3 modes 1-9 shown | current paths and commutation topology | LOCKED for modes 1-6; remaining shown modes TRANSCRIBE |
| Eqs. (1)-(4) | Mode-1 current slopes | LOCKED |
| Eqs. (5)-(6) | Mode-2 commutation voltage/time | TRANSCRIBE into executable checks |
| Eqs. (7)-(10) | Mode-3 current slopes and zero-cross time | TRANSCRIBE into executable checks |
| Eqs. (11)-(12) | Mode-4 negative-current interval | TRANSCRIBE into executable checks |
| Eqs. (13)-(14) | Mode-5 commutation voltage/time | TRANSCRIBE into executable checks |
| Eqs. (15)-(16) | Mode-6 next-phase current rise | TRANSCRIBE into executable checks |
| Eq. (17) | `Vo/Vin=D/nP` | LOCKED |
| Eqs. (18)-(19) | duty/maximum-phase constraint | LOCKED |
| Eq. (20) | 5%-negative-current boundary inductance | LOCKED |
| Eqs. (21)-(22) | component/output-capacitor ripple stress | TRANSCRIBE |
| Eq. (23) | minimum series capacitance | LOCKED |
| Table I | component voltage/current stress | TRANSCRIBE |
| Table II | 12 V/1 V, 200 W, 3x3, nominal 0.5 MHz | LOCKED; printed `D=0.26%` CONFLICT with Eq. (17) |
| Table III | devices and passive families | LOCKED; capacitor suffixes MISSING |
| Table IV | CCM/boundary comparison and control family | LOCKED |
| Fig. 4 | measured gate/VDS switching sequence | LOCKED qualitatively; numeric dead time MISSING |
| Fig. 5 | measured 50 A phase peak and about 15 A module ripple | LOCKED |
| exact CH/CL values | Mode-2/5 commutation | MISSING |
| exact dead time, ZCD circuit, filtering/blanking and control logic | event controller | MISSING |

## Netlist reverse-traceability gate

Every active `PF-*` netlist parameter must carry one of these tags in a nearby
comment:

- `P24-FIG/EQ/TABLE/TEXT`
- `P25-FIG/EQ/TABLE/TEXT`
- `DATASHEET:<part>`
- `DERIVED:<equation>`
- `UNRESOLVED-SENSITIVITY`
- `NUMERICAL-ONLY`

A result is not eligible for the word "reproduced" unless:

1. all required source rows for that result are `LOCKED`;
2. all netlist parameters pass the reverse-source check;
3. all boundary assertions pass;
4. no unresolved sensitivity value is presented as a paper value; and
5. the full required waveform sequence passes, not only the output average.
