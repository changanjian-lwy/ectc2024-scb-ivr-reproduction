"""D06: ideal zero-delay P25 three-phase event controller, not a plant solver.

Physical topology/Coss remain in D03/D05. Only gates, clocks and memory may
change at an event. Caller must locate roots and certify electrical feasibility.
No prescribed global frequency or numerical prototype values are introduced.
"""
from dataclasses import dataclass, replace
from enum import Enum
from math import isfinite

from .p25_event_guards import Snapshot
from .p25_native_events import GateState, PeakReference


class Stage(str, Enum):
    RISE = "high_on"
    DOWN_COMM = "high_off_to_low_zero"
    ALL_LOW = "all_low_until_next_current_zero"
    NEGATIVE = "next_current_zero_to_negative_target"
    UP_COMM = "next_low_off_to_next_high_zero"


class Trigger(str, Enum):
    HIGH_OFF_DUE = "actual_high_on_time_elapsed"
    LOW_ZERO = "active_low_vds_zero"
    NEXT_CURRENT_ZERO = "next_inductor_downward_zero"
    NEGATIVE_TARGET = "next_inductor_negative_target"
    NEXT_HIGH_ZERO = "next_high_vds_zero"


@dataclass(frozen=True)
class Policy:
    on_time_s: tuple[float, float, float]
    voltage_tolerance_v: float
    current_tolerance_a: float
    time_tolerance_s: float
    ideal_zero_delay: bool
    declaration: str

    def __post_init__(self):
        if not isinstance(self.on_time_s, tuple) or len(self.on_time_s) != 3 or not all(isfinite(t) and t > 0 for t in self.on_time_s):
            raise ValueError("three explicit positive high-side on-times required")
        if len(set(self.on_time_s)) != 1:
            raise ValueError("native common D*T required; unequal on-times need a separate extension branch")
        if not all(isfinite(t) and t >= 0 for t in (self.voltage_tolerance_v, self.current_tolerance_a, self.time_tolerance_s)):
            raise ValueError("separate finite nonnegative V/A/s tolerances required")
        if self.ideal_zero_delay is not True or not self.declaration.strip():
            raise ValueError("explicit ideal zero-delay assumption required; real driver not implemented")


@dataclass(frozen=True)
class KnownPeak:
    reference: PeakReference
    available_at_s: float

    def __post_init__(self):
        if not isfinite(self.available_at_s):
            raise ValueError("peak availability must be finite")


@dataclass(frozen=True)
class Memory:
    phase: int  # active/most recently active high side, 1-based
    stage: Stage
    entered_at_s: float
    last_event: Snapshot
    peaks: tuple[KnownPeak | None, ...]
    latched_target_a: float | None


def gate_pattern(phase: int, stage: Stage) -> GateState:
    if type(phase) is not int or not 1 <= phase <= 3 or not isinstance(stage, Stage):
        raise ValueError("native phase/stage required")
    k, q = phase-1, phase % 3
    high, low = [False]*3, [True]*3
    if stage == Stage.RISE:
        high[k], low[k] = True, False
    elif stage == Stage.DOWN_COMM:
        low[k] = False
    elif stage == Stage.UP_COMM:
        low[q] = False
    return GateState(tuple(high), tuple(low))


def _key(s: Snapshot):
    return (s.boundary, s.run_id, s.clock_id, s.cycle)


def _admit_snapshot(memory: Memory, s: Snapshot, policy: Policy):
    if _key(s) != _key(memory.last_event) or s.time_s < memory.last_event.time_s:
        raise ValueError("snapshot run/module/clock/cycle/time does not match controller memory")
    if s.gates != gate_pattern(memory.phase, memory.stage):
        raise ValueError("effective gate state does not match latched controller state")
    for k, on in enumerate((*s.gates.high, *s.gates.low)):
        if on and abs(s.switch_voltage(("SH1", "SH2", "SH3", "SL1", "SL2", "SL3")[k])) > policy.voltage_tolerance_v:
            raise ValueError("ideal ON gate has incompatible voltage; plant state not admissible")
    active, next_phase = memory.phase-1, memory.phase % 3
    for k, current in enumerate(s.current_a):
        if memory.stage == Stage.RISE and k == active:
            continue  # preserve negative entry current; never reset it
        sign = -1 if memory.stage in {Stage.NEGATIVE, Stage.UP_COMM} and k == next_phase else 1
        if sign*current < -policy.current_tolerance_a:
            raise ValueError(f"iL{k+1} outside current-sign domain of {memory.stage.value}")


def start_at_high_on(s: Snapshot, *, phase: int, peaks: tuple[KnownPeak | None, ...], policy: Policy) -> Memory:
    """Declare an already reached high-on section, NOT zero-start reachability."""
    if len(peaks) != 3:
        raise ValueError("three peak-memory entries required, unknowns must be None")
    for k, peak in enumerate(peaks, 1):
        if peak is not None and (peak.reference.phase != k or peak.available_at_s > s.time_s):
            raise ValueError("wrong-phase or future peak in initial memory")
    memory = Memory(phase, Stage.RISE, s.time_s, s, tuple(peaks), None)
    _admit_snapshot(memory, s, policy)
    return memory


def update_peak(memory: Memory, peak: KnownPeak, *, observed: Snapshot, policy: Policy) -> Memory:
    """Supply a past peak; measurement/window definition is an external module.

    Updating a record cannot change a target already latched for this handoff.
    The source field must document peak/window provenance; no sampled-max claim
    is generated here, and high-off current is never automatically the peak.
    """
    _admit_snapshot(memory, observed, policy)
    if peak.available_at_s > observed.time_s:
        raise ValueError("future peak cannot control present switching")
    records = list(memory.peaks)
    previous = records[peak.reference.phase-1]
    if previous is not None and peak.available_at_s < previous.available_at_s:
        raise ValueError("cannot replace peak with an older record")
    records[peak.reference.phase-1] = peak
    return replace(memory, peaks=tuple(records), last_event=observed)


def transition(memory: Memory, trigger: Trigger, at: Snapshot, *, policy: Policy,
               left: Snapshot | None = None) -> Memory:
    """Consume a located endpoint, not a time-step overshoot.

    For physical roots a same-stage left snapshot with positive g is required.
    It is only a witness: trajectory continuity, first-root location and D05
    admissibility must be certified by the caller, not by this controller.
    """
    expected = {Stage.RISE: Trigger.HIGH_OFF_DUE, Stage.DOWN_COMM: Trigger.LOW_ZERO,
                Stage.ALL_LOW: Trigger.NEXT_CURRENT_ZERO, Stage.NEGATIVE: Trigger.NEGATIVE_TARGET,
                Stage.UP_COMM: Trigger.NEXT_HIGH_ZERO}
    if trigger != expected[memory.stage]:
        raise ValueError("event out of order or duplicate event")
    _admit_snapshot(memory, at, policy)
    phase, stage, target = memory.phase, memory.stage, memory.latched_target_a
    q = phase % 3 + 1
    if trigger == Trigger.HIGH_OFF_DUE:
        due = memory.entered_at_s+policy.on_time_s[phase-1]
        if abs(at.time_s-due) > policy.time_tolerance_s:
            raise ValueError("locate actual high-on duration endpoint; no early/late time substitution")
        next_stage = Stage.DOWN_COMM
    else:
        if left is None:
            raise ValueError("physical event needs a left-state witness, not a timer")
        _admit_snapshot(memory, left, policy)
        if not memory.entered_at_s <= left.time_s < at.time_s:
            raise ValueError("root witness must lie within the current stage")
        if trigger == Trigger.LOW_ZERO:
            f = lambda s: s.switch_voltage(f"SL{phase}")
            tol, next_stage = policy.voltage_tolerance_v, Stage.ALL_LOW
        elif trigger == Trigger.NEXT_CURRENT_ZERO:
            f = lambda s: s.current_a[q-1]
            tol, next_stage = policy.current_tolerance_a, Stage.NEGATIVE
        elif trigger == Trigger.NEGATIVE_TARGET:
            if target is None:
                raise ValueError("negative target was not latched")
            f = lambda s: s.current_a[q-1]-target
            tol, next_stage = policy.current_tolerance_a, Stage.UP_COMM
        else:
            f = lambda s: s.switch_voltage(f"SH{q}")
            tol, next_stage = policy.voltage_tolerance_v, Stage.RISE
        if f(left) <= 0 or abs(f(at)) > tol:
            raise ValueError("root not located at stated endpoint; missing direction or excessive residual")
        if trigger == Trigger.NEXT_CURRENT_ZERO:
            peak = memory.peaks[q-1]
            if peak is None or peak.available_at_s > at.time_s:
                raise ValueError(f"phase {q} causal peak reference unavailable")
            target = -at.boundary.alpha*peak.reference.amperes
        elif trigger == Trigger.NEXT_HIGH_ZERO:
            phase, target = q, None
    # Identity reset for ALL electrical coordinates. Only gate/memory metadata change.
    cycle = at.cycle + (1 if trigger == Trigger.NEXT_HIGH_ZERO and phase == 1 else 0)
    after = replace(at, gates=gate_pattern(phase, next_stage), cycle=cycle)
    result = Memory(phase, next_stage, at.time_s, after, memory.peaks, target)
    _admit_snapshot(result, after, policy)
    return result
