# Operating-sequence source matrix

## Compiler rule

The target is P24. P24 explicit statements always control. P25 is consulted
only where P24 is silent. A conflict creates no automatic winner and blocks
publication-locked SPICE generation.

Framework transition interfaces use stable physical-event identifiers rather
than a paper's local `t1/t2/t3` symbols. Paper labels are aliases attached to
those events. A new source inserts aliases or a branch; it must not rewrite the
topology, formula, device, controller or experiment modules. In particular,
P24 `t2` maps to phase-1 inductor-current zero, whereas P25 `t2` maps to the
phase-1 low-side zero-Vds / ideal turn-on boundary.

The next mapping is also deliberately non-identical:

| Physical event | P24 label | P25 label | Meaning |
|---|---:|---:|---|
| Phase-1 high-side turns off | `t1` | `t1` | Shared physical start of capacitance commutation |
| Phase-1 low-side Vds reaches zero and low-side turns on | unnumbered event inside P24 interval 2 | `t2` | P25 Mode 3 begins here; P24 interval 2 has not ended |
| Phase-1 inductor current reaches zero | `t2` | no `t3` alias | P24 interval 3 begins; this is not P25 `t3` |
| Phase-2 inductor current reaches zero | not used as the displayed phase-1 interval-3 boundary | `t3` | P25 Mode 3 ends; controller zero-crossing event for the next phase |
| Phase-1 high-side reaches zero Vds and turns on | `t3` | belongs to a later same-phase cycle, not P25 Mode-3 `t3` | P24 interval 3 ends |

Consequently, P25 Mode 3 `[t2,t3]` cannot be pasted over P24 interval 3
`[t2,t3]`.  The matching framework interfaces are physical events, not the
printed time symbols.

## Current resolution

| Topic | P24 | P25 | Classification | Action |
|---|---|---|---|---|
| Phase-1 energy interval | `QH1` and `QS2` conduct; `iL1` rises | Adds the other non-active low-side freewheel state in its three-phase example | `P25_FILLS_P24_SILENCE` | Preserve P24 commands; label any fourth-phase completion as extension |
| `QH1` turn-off | Positive `iL1` charges high-side Coss and discharges low-side Coss | Adds `CH1/CL1`, Mode 2/2' and timing equations | `P25_FILLS_P24_SILENCE` | P24 mechanism controls; numeric timing still needs capacitance/dead time |
| Third-stage boundary | Follows same-phase `iL1` through zero/negative current and returns `QH1` to ZVS | Mode 3 ends on next-phase `iL2=0`; Modes 4-6 prepare/start `SH2` | `CONFLICT_REQUIRES_DECISION` | Do not merge automatically |
| Negative-current target | 1%-2% of phase peak | 5%-10% in Mode 4; up to 5% in Eq. (20) | `CONFLICT_REQUIRES_DECISION` | Keep separate source branches |
| Numeric Coss/dead time | Not reported | Equations/mechanism reported, values not reported | `UNKNOWN_BLOCKING` | Device/external assumption may support exploration only |
| Module/phase interleaving | P24 says phases and modules are interleaved but does not print one universal combined timing formula | P25 states module origin shift `360/nM`; its demonstrated `nP=3,nM=2` case has no collisions | `REQUIRES_CONFIGURATION_AUDIT` | Keep both `nP` and `nM` explicit; test the resulting event set before generating gates |
| Mode-4/5 command-to-switch boundary | no corresponding explicit split | Mode 4 ends with the SL2 turn-off command at `t4`; Mode 5 says SL2 physically turns off at `t5`, but no delay is reported | `UNKNOWN_BLOCKING` for hardware; ideal baseline allowed | Keep command and physical-off as separate events; ideal branch may state `t5=t4` |
| Mode-6 printed time span | no Mode-6 label | heading repeats `[t5,t6]` although Mode 5 ends with SH2 ON at `t6` and Mode 6 begins with that event | `P25_INTERNAL_LABEL_CONFLICT` | Start from physical SH2-ON event and leave the peak-current end label unnumbered |
| Maximum phase count | not stated | Eqs. (18)-(19): to prevent high-side overlap and preserve series-capacitor/inductor charge balance, `D<=1/nP`, hence `nP<=floor(1/D)`; the text states this "limitation, not addressed in [1] [the 2024 paper]" | `P25_FILLS_P24_SILENCE` | Cross-check every `(nP, Vin, Vo)` combination against `nP<=floor(Vin/(nP*Vo))`, i.e. `nP<=floor(sqrt(Vin/Vo))` after substituting P24 Eq.(1), before it is used in a primary experiment. The active `nP=4`, `Vin=48 V`, `Vo=1 V` mainline satisfies this (`D=0.0833<=1/4=0.25`). The 2024 paper's own Table I additionally analyzes `nP=8` and `nP=16` at 48/1 V, both of which fail this 2025-derived bound (`nP<=6` for 48/1 V); this is a paper-internal tension, not a project error, and blocks treating any `nP=8`/`nP=16` Table I row as a compilable primary case without a separate named decision. |

The module-origin shift is stored as `nP*T/(nP*nM)=T/nM`, with `nP` retained
as a mandatory model input even though it cancels algebraically. For a
single-phase module the caller must pass `nP=1`; for a four-phase module it
must pass `nP=4`. The ideal spacing between all individual events is
`T/(nP*nM)`. These are different quantities and must not be represented by one
ambiguous parameter. Naively combining phase offsets `kT/nP` with module
offsets `mT/nM` produces only `lcm(nP,nM)` unique event times. Thus the P25
demonstration `3 x 2` produces six distinct events, while `4 x 4` would produce
four coincident groups unless an additional scheduling convention is supplied.

## Code layout

- `p24_operating_sequence.py`: exactly three P24 intervals.
- `p25_operating_supplement.py`: exactly six P25 modes.
- `sequence_resolution.py`: comparison, adopted supplements and blockers.
- `ectc2024_mode_spec.py`: topology plus quarantined legacy candidate; it no
  longer exports the candidate as a P24-first executable command table.
- `physical_events.py`: stable observable events plus paper-label aliases.
- `interval3_branches.py`: separate P24 same-phase and P25 next-phase Mode-3 branches.

`publication_sequence_ready()` currently returns `False`, and
`assert_publication_sequence_ready()` raises an error listing the unresolved
topics. This prevents a generator from silently compiling the mixed sequence.
