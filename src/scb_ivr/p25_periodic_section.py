"""D08: full-state return at the P25 SH1-on section, not an orbit certificate.

All capacitor-bank voltages (including Coss/snubber), L currents and relevant
control memory are compared with dimensionally separate tolerances. Absolute
clock/cycle are bookkeeping, not coordinates required to repeat numerically.
"""
from dataclasses import dataclass
from math import isfinite

import numpy as np

from .p25_control_memory import Memory, Policy, Stage, gate_pattern, start_at_high_on
from .p25_nodal_contract import Components, CAPACITORS, incidence
from .p25_reverse_contract import ReverseModel


@dataclass(frozen=True)
class ModelIdentity:
    components: Components
    reverse_model: ReverseModel
    control: Policy
    port_model_id: str

    def __post_init__(self):
        if not isinstance(self.components, Components) or not isinstance(self.reverse_model, ReverseModel) or not isinstance(self.control, Policy):
            raise ValueError("typed explicit component/reverse/control models required")
        if not self.port_model_id.strip():
            raise ValueError("external-port law identity required; it is not proof of periodicity")


@dataclass(frozen=True)
class ReturnTolerance:
    voltage_v: float
    current_a: float
    time_s: float
    relative: float

    def __post_init__(self):
        if not all(isfinite(x) and x > 0 for x in (self.voltage_v, self.current_a, self.time_s)):
            raise ValueError("explicit positive finite V/A/s absolute tolerances required")
        if not isfinite(self.relative) or self.relative < 0:
            raise ValueError("finite nonnegative relative tolerance required")


@dataclass(frozen=True)
class Coordinate:
    name: str
    unit: str
    value: float


@dataclass(frozen=True)
class Residual:
    name: str
    unit: str
    delta: float
    allowance: float
    scaled: float


@dataclass(frozen=True)
class StateReturn:
    period_s: float
    residuals: tuple[Residual, ...]
    max_scaled: float
    state_returns: bool
    scope: str = "STATE_RETURN_ONLY; trajectory, external forcing, feasibility and stability unverified"


def section_coordinates(memory: Memory) -> tuple[Coordinate, ...]:
    s = memory.last_event
    if memory.phase != 1 or memory.stage != Stage.RISE or s.gates != gate_pattern(1, Stage.RISE):
        raise ValueError("requires the same SH1-on post-event section")
    if memory.entered_at_s != s.time_s or memory.latched_target_a is not None:
        raise ValueError("not a fresh SH1-on section or stale latched target")
    if len(memory.peaks) != 3:
        raise ValueError("all three peak records required")
    caps = incidence().T @ np.r_[s.vin_v, s.voltage_v]
    coords = [Coordinate(f"V_{name}", "V", float(value)) for name, value in zip(CAPACITORS, caps)]
    coords += [Coordinate(f"iL{k}", "A", value) for k, value in enumerate(s.current_a, 1)]
    coords.append(Coordinate("Vin", "V", s.vin_v))
    for phase, peak in enumerate(memory.peaks, 1):
        if peak is None:
            raise ValueError(f"phase {phase} peak memory unresolved; cannot certify controller-state return")
        if peak.reference.phase != phase or peak.available_at_s > s.time_s:
            raise ValueError("wrong-phase or future peak record")
        coords.append(Coordinate(f"peak_ref_{phase}", "A", peak.reference.amperes))
        if peak.reference.basis == "previous_measured_peak":
            coords.append(Coordinate(f"peak_age_{phase}", "s", s.time_s-peak.available_at_s))
    return tuple(coords)


def scaled_residual(left: Coordinate, right: Coordinate, tol: ReturnTolerance) -> Residual:
    if left.name != right.name or left.unit != right.unit or left.unit not in {"V", "A", "s"}:
        raise ValueError("matching named coordinates and units required")
    if not all(isfinite(v) for v in (left.value, right.value)):
        raise ValueError("finite coordinate values required")
    absolute = {"V": tol.voltage_v, "A": tol.current_a, "s": tol.time_s}[left.unit]
    allowance = absolute+tol.relative*max(abs(left.value), abs(right.value))
    delta = right.value-left.value
    return Residual(left.name, left.unit, delta, allowance, abs(delta)/allowance)


def compare_sections(start: Memory, end: Memory, *, start_model: ModelIdentity,
                     end_model: ModelIdentity, tolerance: ReturnTolerance) -> StateReturn:
    """One-cycle state-return screen; endpoints alone cannot prove a trajectory."""
    a, b = start.last_event, end.last_event
    if start_model != end_model:
        raise ValueError("component/controller/port boundary changed between sections")
    if (a.boundary, a.run_id, a.clock_id) != (b.boundary, b.run_id, b.clock_id):
        raise ValueError("different branch/module/run/clock")
    if b.cycle != a.cycle+1 or b.time_s <= a.time_s:
        raise ValueError("exactly one forward cycle required")
    x, y = section_coordinates(start), section_coordinates(end)
    start_at_high_on(a, phase=1, peaks=start.peaks, policy=start_model.control)
    start_at_high_on(b, phase=1, peaks=end.peaks, policy=end_model.control)
    # Provenance describes the same reference policy/window, not an arbitrary
    # new source silently swapped in to improve closure.
    for p, q in zip(start.peaks, end.peaks):
        if (p.reference.basis, p.reference.source) != (q.reference.basis, q.reference.source):
            raise ValueError("peak-reference basis/source changed between sections")
    if tuple((c.name, c.unit) for c in x) != tuple((c.name, c.unit) for c in y):
        raise ValueError("different reduced state definitions")
    rows = tuple(scaled_residual(p, q, tolerance) for p, q in zip(x, y))
    maximum = max(r.scaled for r in rows)
    return StateReturn(b.time_s-a.time_s, rows, maximum, maximum <= 1.)
