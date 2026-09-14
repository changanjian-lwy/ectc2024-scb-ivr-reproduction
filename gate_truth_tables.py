"""Source-labelled four-phase gate truth tables with explicit unknown states."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Gate(str, Enum):
    ON = "ON"
    OFF = "OFF"
    EVENT = "EVENT_CONTROLLED"
    UNKNOWN = "NOT_REPORTED"


@dataclass(frozen=True)
class GateRow:
    branch: str
    active_phase: int
    state: str
    high: tuple[Gate, ...]
    low: tuple[Gate, ...]
    end_event: str

    @property
    def compile_ready(self) -> bool:
        return Gate.UNKNOWN not in self.high + self.low


def _off_highs_with_active(phases: int, active: int, value: Gate) -> tuple[Gate, ...]:
    return tuple(value if k == active else Gate.OFF for k in range(1, phases + 1))


def p24_minimal_rows(active: int, phases: int = 4) -> tuple[GateRow, ...]:
    """Transcribe P24 statements; silence remains NOT_REPORTED."""

    if not 1 <= active <= phases:
        raise ValueError("active phase outside configured phase count")
    adjacent = active % phases + 1
    energy_lows = tuple(
        Gate.OFF if k == active else Gate.ON if k == adjacent else Gate.UNKNOWN
        for k in range(1, phases + 1)
    )
    interval2_lows = tuple(
        Gate.EVENT if k == active else Gate.UNKNOWN for k in range(1, phases + 1)
    )
    interval3_lows = tuple(
        Gate.EVENT if k == active else Gate.UNKNOWN for k in range(1, phases + 1)
    )
    return (
        GateRow("P24_MINIMAL", active, "I1_ENERGY", _off_highs_with_active(phases, active, Gate.ON), energy_lows, "HIGH_SIDE_ON_TIME_END"),
        GateRow("P24_MINIMAL", active, "I2_COSS_TO_LOW_ZVS_AND_CURRENT_ZERO", (Gate.OFF,) * phases, interval2_lows, "INDUCTOR_CURRENT_ZERO"),
        GateRow("P24_MINIMAL", active, "I3_NEGATIVE_AND_HIGH_ZVS", tuple(Gate.EVENT if k == active else Gate.OFF for k in range(1, phases + 1)), interval3_lows, "HIGH_SIDE_VDS_ZERO"),
    )


def p25_extended_rows(active: int, phases: int = 4) -> tuple[GateRow, ...]:
    """Rotate P25's all-inactive-low rule into a labelled four-phase branch."""

    if not 1 <= active <= phases:
        raise ValueError("active phase outside configured phase count")
    next_phase = active % phases + 1
    inactive_lows = tuple(Gate.OFF if k == active else Gate.ON for k in range(1, phases + 1))
    all_lows = (Gate.ON,) * phases
    next_low_off = tuple(Gate.OFF if k == next_phase else Gate.ON for k in range(1, phases + 1))
    next_high = _off_highs_with_active(phases, next_phase, Gate.ON)
    return (
        GateRow("P25_NP4_EXTENSION", active, "M1_ACTIVE_HIGH", _off_highs_with_active(phases, active, Gate.ON), inactive_lows, "ACTIVE_HIGH_OFF"),
        GateRow("P25_NP4_EXTENSION", active, "M2_ACTIVE_LEG_COMMUTATION", (Gate.OFF,) * phases, inactive_lows, "ACTIVE_LOW_VDS_ZERO"),
        GateRow("P25_NP4_EXTENSION", active, "M3_ALL_LOW_FREEWHEEL", (Gate.OFF,) * phases, all_lows, "NEXT_PHASE_CURRENT_ZERO"),
        GateRow("P25_NP4_EXTENSION", active, "M4_NEXT_NEGATIVE_BUILD", (Gate.OFF,) * phases, all_lows, "NEXT_PHASE_NEGATIVE_TARGET"),
        GateRow("P25_NP4_EXTENSION", active, "M5_NEXT_HIGH_COMMUTATION", (Gate.OFF,) * phases, next_low_off, "NEXT_HIGH_VDS_ZERO"),
        GateRow("P25_NP4_EXTENSION", active, "M6_NEXT_HIGH", next_high, next_low_off, "NEXT_PHASE_CURRENT_PEAK"),
    )


def assert_no_commanded_shoot_through(rows: tuple[GateRow, ...]) -> None:
    for row in rows:
        for phase, (high, low) in enumerate(zip(row.high, row.low), start=1):
            if high == Gate.ON and low == Gate.ON:
                raise RuntimeError(f"{row.branch} {row.state}: phase {phase} shoot-through")


def require_compile_ready(rows: tuple[GateRow, ...]) -> None:
    unresolved = [row.state for row in rows if not row.compile_ready]
    if unresolved:
        raise RuntimeError(f"truth table contains NOT_REPORTED gates: {unresolved}")
