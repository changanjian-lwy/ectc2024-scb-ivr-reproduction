"""Compile the labelled P25-to-four-phase truth table to one LTspice machine."""

from __future__ import annotations


def _state(phase: int, mode: int) -> str:
    return f"P{phase}_M{mode}"


def emit_p25_np4_machine(*, phases: int = 4, hybrid_timing: bool = False) -> str:
    if phases != 4:
        raise ValueError("current Fig. 3 emitter is locked to phases=4")

    lines = [
        "* Generated P25_NP4_EXTENSION controller: one rotating event machine.",
        "* No absolute T/4 threshold substitutes for a physical event.",
        ".machine 1p",
    ]
    number = 0
    for phase in range(1, phases + 1):
        for mode in range(1, 6):
            lines.append(f".state {_state(phase, mode)} {number}")
            number += 1

    high_vds = {1: "V(vin,a1)", 2: "V(a1,a2)", 3: "V(a2,a3)", 4: "V(a3,x4)"}
    for phase in range(1, phases + 1):
        nxt = phase % phases + 1
        lines.extend(
            (
                (
                    f".rule {_state(phase,1)} {_state(phase,2)} V(gh{phase}_ton)>=2.5"
                    if hybrid_timing
                    else f".rule {_state(phase,1)} {_state(phase,2)} I(L{phase})>=IPEAK"
                ),
                f".rule {_state(phase,2)} {_state(phase,3)} V(x{phase})<=0",
                f".rule {_state(phase,3)} {_state(phase,4)} I(L{nxt})<=0",
                f".rule {_state(phase,4)} {_state(phase,5)} I(L{nxt})<=-INEG",
                (
                    f".rule {_state(phase,5)} {_state(nxt,1)} "
                    f"(time>=T0+{phase}*PHASE)*({high_vds[nxt]}<=0)"
                    if hybrid_timing
                    else f".rule {_state(phase,5)} {_state(nxt,1)} {high_vds[nxt]}<=0"
                ),
            )
        )

    for gate_phase in range(1, phases + 1):
        lines.append(f".output (gh{gate_phase}) VG*(state=={_state(gate_phase,1)})")
    for gate_phase in range(1, phases + 1):
        on_states = []
        for active in range(1, phases + 1):
            nxt = active % phases + 1
            for mode in range(1, 6):
                is_on = (
                    (mode in (1, 2) and gate_phase != active)
                    or mode in (3, 4)
                    or (mode == 5 and gate_phase != nxt)
                )
                if is_on:
                    on_states.append(f"(state=={_state(active,mode)})")
        lines.append(f".output (gl{gate_phase}) VG*({' + '.join(on_states)})")
    lines.append(".output (sequence_state) state")
    lines.append(".endmachine")
    if hybrid_timing:
        lines.extend(
            f"B_GH{k}_TON gh{k}_ton g V=delay(V(gh{k}),TON)"
            for k in range(1, phases + 1)
        )
    lines.extend(
        [f"RGH{k}_MACHINE gh{k} g 1k" for k in range(1, phases + 1)]
        + [f"RGL{k}_MACHINE gl{k} g 1k" for k in range(1, phases + 1)]
        + ([f"R_GH{k}_TON gh{k}_ton g 1k" for k in range(1, phases + 1)] if hybrid_timing else [])
        + ["R_SEQUENCE_STATE sequence_state g 1k"]
    )
    return "\n".join(lines)
