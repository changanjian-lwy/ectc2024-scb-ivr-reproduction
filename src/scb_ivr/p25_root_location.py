"""D07: pure bracket refinement and conservative event-time ordering.

No electrical integration, state projection or gate action occurs here.
Continuous pre-event continuation must be supplied by the caller. Neither
continuity nor first-root uniqueness is proved from finitely many samples.
"""
from dataclasses import dataclass
from math import isfinite
from typing import Callable

from .p25_event_guards import Snapshot


def trace_key(s: Snapshot):
    return (s.boundary, s.run_id, s.clock_id, s.cycle, s.gates)


@dataclass(frozen=True)
class Quantity:
    name: str
    unit: str
    evaluate: Callable[[Snapshot], float]

    def __post_init__(self):
        if not self.name.strip() or self.unit not in {"V", "A"} or not callable(self.evaluate):
            raise ValueError("named voltage/current event function required")


@dataclass(frozen=True)
class RootSettings:
    time_tolerance_s: float
    value_tolerance: float  # Quantity.unit, NOT mixed with seconds
    max_iterations: int
    continuation_declaration: str

    def __post_init__(self):
        if not isfinite(self.time_tolerance_s) or self.time_tolerance_s <= 0:
            raise ValueError("strictly positive finite time tolerance required")
        if not isfinite(self.value_tolerance) or self.value_tolerance < 0:
            raise ValueError("finite nonnegative event-value tolerance required")
        if type(self.max_iterations) is not int or self.max_iterations < 1:
            raise ValueError("positive iteration bound required")
        if not self.continuation_declaration.strip():
            raise ValueError("declare supplied continuous pre-event continuation and its scope")


@dataclass(frozen=True)
class LocatedRoot:
    name: str
    unit: str
    left: Snapshot  # g>0, usable as a left witness, not a new accepted step
    right: Snapshot  # g<=0, proposed numerical event endpoint
    left_value: float
    right_value: float
    evaluations: int
    status: str = "NUMERICAL_ROOT_ONLY"


def locate_downward(quantity: Quantity, trajectory: Callable[[float], Snapshot], *,
                    left_s: float, right_s: float, settings: RootSettings) -> LocatedRoot:
    """Return a sign bracket satisfying BOTH time width and endpoint residual.

    Root endpoint is never overwritten to g=0. Starting exactly on a root is
    rejected; initial-boundary processing/arming is a separate module.
    Intermediate evaluations are mathematical trial continuation, not accepted
    circuit states (they may lie beyond the original mode's physical domain).
    """
    if not all(isfinite(t) for t in (left_s, right_s)) or left_s >= right_s:
        raise ValueError("finite strictly ordered time bracket required")
    evaluations = 0
    reference_key = None

    def sample(t):
        nonlocal evaluations, reference_key
        state = trajectory(t)
        if not isinstance(state, Snapshot) or state.time_s != t:
            raise ValueError("trajectory must return a snapshot at the requested time")
        key = trace_key(state)
        if reference_key is None:
            reference_key = key
        elif key != reference_key:
            raise ValueError("root trial changed branch/run/clock/cycle/gates")
        value = quantity.evaluate(state)
        if not isfinite(value):
            raise ValueError("nonfinite event function")
        evaluations += 1
        return state, float(value)

    left, gl = sample(left_s)
    right, gr = sample(right_s)
    if not gl > 0 or not gr <= 0:
        raise ValueError("requires positive-to-nonpositive bracket; timer/root-at-start is insufficient")
    for _ in range(settings.max_iterations):
        if right.time_s-left.time_s <= settings.time_tolerance_s and abs(gr) <= settings.value_tolerance:
            return LocatedRoot(quantity.name, quantity.unit, left, right, gl, gr, evaluations)
        midpoint = left.time_s+(right.time_s-left.time_s)/2
        if midpoint == left.time_s or midpoint == right.time_s:
            raise RuntimeError("floating-point time resolution exhausted before both criteria passed")
        state, gm = sample(midpoint)
        if gm > 0:
            left, gl = state, gm
        else:
            right, gr = state, gm
    if right.time_s-left.time_s <= settings.time_tolerance_s and abs(gr) <= settings.value_tolerance:
        return LocatedRoot(quantity.name, quantity.unit, left, right, gl, gr, evaluations)
    raise RuntimeError("root iteration limit: no certified numerical endpoint returned")


@dataclass(frozen=True)
class EventWindow:
    name: str
    earliest_s: float
    latest_s: float
    trace: tuple
    evidence: str  # e.g. numerical bracket / explicit scheduled clock

    def __post_init__(self):
        if not self.name.strip() or not self.evidence.strip():
            raise ValueError("event name/evidence required")
        if not all(isfinite(t) for t in (self.earliest_s, self.latest_s)) or self.earliest_s > self.latest_s:
            raise ValueError("finite ordered uncertainty interval required")
        if not self.trace:
            raise ValueError("pre-event trace identity required")

    @classmethod
    def from_root(cls, root: LocatedRoot):
        return cls(root.name, root.left.time_s, root.right.time_s,
                   trace_key(root.left), "numerical sign bracket; continuity/uniqueness conditional")


@dataclass(frozen=True)
class EventOrder:
    status: str
    possible_first: tuple[str, ...]


def order_windows(windows: tuple[EventWindow, ...]) -> EventOrder:
    """No midpoint ordering or priority guesses for overlapping intervals.

    Caller must enumerate ALL armed controller and physical-domain events.
    This cannot detect an event omitted from that input list or an earlier root
    omitted from a supplied window. Exact coincidence is not a reset-order rule.
    """
    if not windows or len({w.name for w in windows}) != len(windows):
        raise ValueError("nonempty distinct event set required")
    if any(w.trace != windows[0].trace for w in windows):
        raise ValueError("cannot compare events from different pre-event traces")
    upper = min(w.latest_s for w in windows)
    candidates = tuple(w for w in windows if w.earliest_s <= upper)
    names = tuple(sorted(w.name for w in candidates))
    if len(candidates) == 1:
        return EventOrder("UNIQUE_EARLIEST_AMONG_SUPPLIED_WINDOWS", names)
    if all(w.earliest_s == w.latest_s == upper for w in candidates):
        return EventOrder("EXACT_COINCIDENCE_REQUIRES_RESET_RULE", names)
    return EventOrder("OVERLAP_REFINE_OR_DECLARE_UNRESOLVED", names)


def ideal_gate_reverse_batch(memory, trigger, at, *, left, policy, parts, reverse_model,
                            dvin_v_s, load_current_a, other_modules_current_a, tolerances):
    """One explicitly defined simultaneous reset: Vds-zero gate + reverse boundary.

    This is not a general priority rule. Solve full-network complementarity
    before AND after one ideal gate action, preserving all electrical states.
    Root/trajectory validity remains caller-owned; extra simultaneous control
    events (e.g. another phase current zero) are not resolved by this function.
    """
    from .p25_control_memory import Trigger, transition
    from .p25_nodal_contract import assert_continuous_energy_state
    from .p25_reverse_contract import resolve_local_reverse

    if trigger not in {Trigger.LOW_ZERO, Trigger.NEXT_HIGH_ZERO}:
        raise ValueError("only one zero-voltage gate/reverse-boundary batch supported")
    if reverse_model.kind != "ideal_zero_drop":
        raise ValueError("zero-drop mathematical branch required; not a real-GaN transition")
    kwargs = dict(dvin_v_s=dvin_v_s, load_current_a=load_current_a,
                  other_modules_current_a=other_modules_current_a, tolerances=tolerances)
    before = resolve_local_reverse(at, parts, reverse_model, **kwargs)
    if before.status != "LOCAL_COMPLEMENTARITY_ONLY":
        raise ValueError(f"pre-event electrical boundary unresolved: {before.status}")
    after_memory = transition(memory, trigger, at, left=left, policy=policy)
    after = after_memory.last_event
    assert_continuous_energy_state(voltage_before_v=at.voltage_v, voltage_after_v=after.voltage_v,
                                   vin_before_v=at.vin_v, vin_after_v=after.vin_v,
                                   current_before_a=at.current_a, current_after_a=after.current_a,
                                   capacitor_tolerance_v=0., current_tolerance_a=0.)
    resolved = resolve_local_reverse(after, parts, reverse_model, **kwargs)
    if resolved.status != "LOCAL_COMPLEMENTARITY_ONLY":
        raise ValueError(f"post-event electrical boundary unresolved: {resolved.status}")
    return after_memory, before, resolved
