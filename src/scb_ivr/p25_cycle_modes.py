"""D15: P25's three-phase 15 main modes, physical event index mapping.

Fig2/3, SecII: first six described modes then repeated operation in remaining
phases. Later rows are explicit cyclic extrapolation of those rules, not new
device/timing data. No topology/state-array rotation. Prime reverse intervals
remain electrical submodes, NOT extra gate commands or fixed durations.
"""
from dataclasses import dataclass
from .p25_native_events import GateState, MODES

SLOTS=("high_on","down_comm","all_low","negative","up_comm")


@dataclass(frozen=True)
class CycleMode:
    name: str
    phase: int
    next_phase: int
    slot: str
    gates: GateState
    exit_event: str
    source_scope: str


def cycle_mode(name: str) -> CycleMode:
    if name not in tuple(f"M{i}" for i in range(1,16)):
        raise ValueError("P25 main modes M1-M15 only; no four-phase or prime-gate mode")
    index=int(name[1:])-1
    phase=index//5+1; q=phase%3+1; slot=SLOTS[index%5]
    high=[False]*3; low=[True]*3
    if slot=="high_on": high[phase-1],low[phase-1]=True,False
    elif slot=="down_comm": low[phase-1]=False
    elif slot=="up_comm": low[q-1]=False
    event={"high_on":f"SH{phase}_on_duration_elapsed",
           "down_comm":f"SL{phase}_zero_voltage_admission",
           "all_low":f"iL{q}_downward_zero",
           "negative":f"iL{q}_latched_negative_target",
           "up_comm":f"SH{q}_zero_voltage_admission"}[slot]
    scope="P25 first-six source-checked mapping" if index<6 else "P25 repeated-phase rule; project explicit cyclic mapping"
    result=CycleMode(name,phase,q,slot,GateState(tuple(high),tuple(low)),event,scope)
    original={m.name:m.gates for m in MODES if "OPTIONAL" not in m.name}
    if name in original and result.gates!=original[name]:
        raise ValueError("cycle mapping contradicts locked first-six source table")
    return result


def current_signs(name: str) -> tuple[int, int, int]:
    """Closed paper-mode signs; zero means unrestricted, not zero current.

    Extends D02 first-handoff signs using the D15 repeated-phase mapping.
    These are domain checks, not proof that a trajectory reaches that mode.
    """
    mode = cycle_mode(name)
    signs = [1, 1, 1]
    if mode.slot == "high_on":
        signs[mode.phase-1] = 0
    elif mode.slot in {"negative", "up_comm"}:
        signs[mode.next_phase-1] = -1
    return tuple(signs)


def commutation_target(name: str) -> str:
    """Return the physical target switch without rotating any node state."""
    mode = cycle_mode(name)
    if mode.slot == "down_comm":
        return f"SL{mode.phase}"
    if mode.slot == "up_comm":
        return f"SH{mode.next_phase}"
    raise ValueError("commutation requires M2/M5/M7/M10/M12/M15")
