"""D04: state-based guards for P25 first handoff; no timer substitutions.

Endpoint brackets are not located roots. Voltage admission is not an energy
or gate-driver certificate. Unknown reverse thresholds stay unknown.
"""
from dataclasses import dataclass
from math import isfinite

import numpy as np

from .p25_native_events import Event, GateState, MODES, NativeBoundary, PeakReference, negative_target_a
from .p25_nodal_contract import incidence, SWITCHES


@dataclass(frozen=True)
class Snapshot:
    boundary: NativeBoundary
    run_id: str
    clock_id: str
    cycle: int
    time_s: float
    vin_v: float
    voltage_v: tuple[float, ...]  # a1,a2,x1,x2,x3,out
    current_a: tuple[float, ...]  # all three phase currents at this instant
    gates: GateState

    def __post_init__(self):
        if not isinstance(self.boundary, NativeBoundary) or not isinstance(self.gates, GateState):
            raise ValueError("typed native boundary and gate state required")
        if not self.run_id.strip() or not self.clock_id.strip() or type(self.cycle) is not int or self.cycle < 0:
            raise ValueError("run/clock/cycle identifiers required")
        if len(self.voltage_v) != 6 or len(self.current_a) != 3:
            raise ValueError("complete simultaneous three-phase state required")
        if not all(isfinite(x) for x in (self.time_s, self.vin_v, *self.voltage_v, *self.current_a)):
            raise ValueError("finite snapshot required")

    def switch_voltage(self, switch: str) -> float:
        if switch not in SWITCHES:
            raise ValueError("unknown P25 switch")
        return float((incidence().T @ np.r_[self.vin_v, self.voltage_v])[SWITCHES.index(switch)])


@dataclass(frozen=True)
class Assessment:
    status: str
    quantity: str
    value: float | None
    reason: str


_MODES = {m.name: m.gates for m in MODES}
_EVENT_MODE = {Event.L1_ZERO: "M2", Event.I2_ZERO: "M3",
               Event.I2_TARGET: "M4", Event.H2_ZERO: "M5"}


def _quantity(state: Snapshot, event: Event, reference: PeakReference | None):
    if event not in _EVENT_MODE:
        raise ValueError("only first-handoff physical root guards supported")
    if state.gates != _MODES[_EVENT_MODE[event]]:
        raise ValueError("gate pattern incompatible with guarded event")
    if event == Event.L1_ZERO:
        return "Vds_SL1_V", state.switch_voltage("SL1")
    if event == Event.H2_ZERO:
        return "Vds_SH2_V", state.switch_voltage("SH2")
    if event == Event.I2_ZERO:
        return "iL2_A", state.current_a[1]
    if reference is None:
        raise ValueError("explicit phase-2 peak reference required")
    return "iL2_minus_target_A", state.current_a[1]-negative_target_a(state.boundary, reference)


def downward_bracket(left: Snapshot, right: Snapshot, event: Event,
                     *, reference: PeakReference | None = None) -> Assessment:
    """Endpoint evidence only: g(left)>0, g(right)<=0; root still to locate.

    Does not prove first crossing, uniqueness, continuity of an interpolant,
    or compatibility of intermediate circuit states.
    """
    left_key = (left.boundary, left.run_id, left.clock_id, left.cycle)
    right_key = (right.boundary, right.run_id, right.clock_id, right.cycle)
    if left_key != right_key or right.time_s <= left.time_s:
        raise ValueError("one run/module/clock/cycle and strictly ordered times required")
    name, a = _quantity(left, event, reference)
    _, b = _quantity(right, event, reference)
    if a > 0 and b <= 0:
        return Assessment("BRACKET_ONLY", name, b, "locate and validate a root; do not fire a gate at the endpoint")
    return Assessment("NOT_BRACKETED", name, b, "missing positive-to-nonpositive endpoint bracket")


def gate_voltage_criterion(state: Snapshot, switch: str, *, tolerance_v: float) -> Assessment:
    """Recheck voltage AT gate request, not at an earlier zero event."""
    if not isfinite(tolerance_v) or tolerance_v < 0:
        raise ValueError("explicit finite nonnegative voltage tolerance required")
    modes = {"SL1": "M2", "SH2": "M5"}
    if switch not in modes or state.gates != _MODES[modes[switch]]:
        raise ValueError("target must be off, complementary gate off, other gates in required mode")
    value = state.switch_voltage(switch)
    status = "VOLTAGE_CRITERION_ONLY" if abs(value) <= tolerance_v else "VOLTAGE_REJECTED"
    return Assessment(status, f"Vds_{switch}_V", value,
                      "does not certify driver delay, reverse path, loss, or full-period feasibility")


def target_residual(state: Snapshot, reference: PeakReference, *, tolerance_a: float) -> Assessment:
    """Distinguish an accurately located target from a large overshoot."""
    if not isfinite(tolerance_a) or tolerance_a < 0:
        raise ValueError("explicit finite nonnegative current tolerance required")
    name, value = _quantity(state, Event.I2_TARGET, reference)
    if abs(value) <= tolerance_a:
        status = "TARGET_CRITERION_ONLY"
    else:
        status = "TARGET_NOT_REACHED" if value > 0 else "TARGET_OVERSHOT"
    return Assessment(status, name, value, "current criterion is not actual gate turn-off")


@dataclass(frozen=True)
class ReverseBoundary:
    vds_boundary_v: float
    model: str
    source: str

    def __post_init__(self):
        if not isfinite(self.vds_boundary_v) or self.vds_boundary_v > 0:
            raise ValueError("explicit finite nonpositive reverse boundary required")
        if not self.model.strip() or not self.source.strip():
            raise ValueError("reverse model and provenance required")


def reverse_boundary_status(state: Snapshot, switch: str,
                            rule: ReverseBoundary | None) -> Assessment:
    """A boundary screen, NOT a clamp current or complementarity solution."""
    value = state.switch_voltage(switch)
    index = SWITCHES.index(switch)
    if (*state.gates.high, *state.gates.low)[index]:
        return Assessment("NOT_APPLICABLE", f"Vds_{switch}_V", value, "gate is on; use bidirectional channel model")
    if rule is None:
        return Assessment("UNRESOLVED", f"Vds_{switch}_V", value, "missing reverse model/threshold; do not default to zero")
    if value <= rule.vds_boundary_v:
        return Assessment("REVERSE_MODEL_REQUIRED", f"Vds_{switch}_V", value,
                          "at/beyond boundary: stop unclamped mode and solve reverse-current admissibility")
    return Assessment("ABOVE_DECLARED_BOUNDARY", f"Vds_{switch}_V", value,
                      "only the supplied voltage boundary was checked")
