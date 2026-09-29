"""D19: compose one conditional P25 cycle attempt without state replacement.

Finite-scan event detection remains conditional. Reaching the next section is
NOT a periodic orbit: full state/controller return is a separate D08 check.
"""
from dataclasses import dataclass
from math import isfinite
from .p25_control_memory import Memory, Stage, start_at_high_on
from .p25_cycle_modes import cycle_mode
from .p25_handoff import LowHandoff, enter_all_low, reach_next_current_zero
from .p25_high_on import advance_high_on
from .p25_negative_handoff import reach_negative_target, enter_next_high
from .p25_local_flow import LocalFlow


@dataclass(frozen=True)
class PeriodStep:
    mode: str
    phase: int
    before: Memory
    outcome: LowHandoff


@dataclass(frozen=True)
class PeriodAttempt:
    status: str
    start: Memory
    steps: tuple[PeriodStep, ...]
    last_accepted: Memory
    end: Memory | None
    failed_mode: str | None
    scope: str = "CONDITIONAL_SAMPLED_CYCLE_ATTEMPT; not a periodic-orbit or startup certificate"


def attempt_period(start, parts, ports, policy, reverse, *, stage_horizons_s,
                   intervals, voltage_root, current_root, electrical, direction):
    """Try M1..M15 exactly once, returning at the first unresolved boundary.

    Horizons are explicit search bounds for down_comm/all_low/negative/up_comm,
    not physical dwell times or timeouts that force a gate. Common Ton remains
    in policy. No peak observer or seed/parameter adjustment is installed.
    """
    b=start.last_event.boundary
    if b.branch!="P25" or b.nP!=3 or b.nM!=1 or b.module!=1:
        raise ValueError("P25 native three-phase single module only")
    if start.phase!=1 or start.stage!=Stage.RISE or start.entered_at_s!=start.last_event.time_s:
        raise ValueError("fresh SH1-on section required")
    if start.latched_target_a is not None:
        raise ValueError("fresh SH1-on entry cannot retain a previous negative target")
    # Validate the supplied memory without replacing it or erasing its state.
    validated=start_at_high_on(start.last_event,phase=1,peaks=start.peaks,policy=policy)
    if validated!=start:
        raise ValueError("initial control memory does not match declared SH1-on section")
    if not isinstance(stage_horizons_s,tuple) or len(stage_horizons_s)!=4 or not all(
            isfinite(x) and x>0 for x in stage_horizons_s):
        raise ValueError("four explicit positive event-search horizons required")
    if type(intervals) is not int or intervals<1:
        raise ValueError("positive integer sample count required")
    if (direction.voltage_v!=voltage_root.value_tolerance or
            direction.current_a!=current_root.value_tolerance):
        raise ValueError("entry-direction and event tolerances must match")
    stages=(Stage.RISE,Stage.DOWN_COMM,Stage.ALL_LOW,Stage.NEGATIVE,Stage.UP_COMM)
    common=dict(intervals=intervals,voltage_root=voltage_root,
                current_root=current_root,electrical=electrical)
    current=start; steps=[]
    for index in range(15):
        spec=cycle_mode(f"M{index+1}"); slot=index%5
        if (current.phase!=spec.phase or current.stage!=stages[slot] or
                current.last_event.gates!=spec.gates):
            raise RuntimeError("mode/controller mismatch; cannot silently skip or rotate a phase")
        if slot==0:
            outcome=advance_high_on(current,parts,ports,policy,reverse,**common)
        else:
            kwargs=dict(common,end_s=current.last_event.time_s+stage_horizons_s[slot-1])
            if slot==1:
                outcome=enter_all_low(current,parts,ports,policy,reverse,direction=direction,**kwargs)
            elif slot==2:
                outcome=reach_next_current_zero(current,parts,ports,policy,reverse,**kwargs)
            elif slot==3:
                outcome=reach_negative_target(current,parts,ports,policy,reverse,
                    current_rate_tolerance_a_s=direction.current_rate_a_s,**kwargs)
            else:
                outcome=enter_next_high(current,parts,ports,policy,reverse,direction=direction,**kwargs)
        steps.append(PeriodStep(spec.name,spec.phase,current,outcome))
        if outcome.memory is None:
            return PeriodAttempt("STOPPED_AT_UNRESOLVED_STEP",start,tuple(steps),current,None,spec.name)
        after=outcome.memory
        next_spec=cycle_mode(f"M{(index+1)%15+1}")
        if (after.phase!=next_spec.phase or after.stage!=stages[(slot+1)%5] or
                after.last_event.gates!=next_spec.gates):
            raise RuntimeError("returned controller does not match the next physical mode")
        if after.last_event.time_s<=current.last_event.time_s:
            raise RuntimeError("accepted segment must advance time")
        # Independent identity check against the SAME pre-event local flow.
        # This is not another physical simulation or a first-root certificate.
        expected=LocalFlow(current.last_event,parts,spec.name,ports,
                           voltage_tolerance_v=policy.voltage_tolerance_v).at(after.last_event.time_s)
        actual=after.last_event
        if (expected.voltage_v,expected.current_a,expected.vin_v)!=(actual.voltage_v,actual.current_a,actual.vin_v):
            raise RuntimeError("electrical state was reset or replaced across handoff")
        if (expected.boundary,expected.run_id,expected.clock_id)!=(actual.boundary,actual.run_id,actual.clock_id):
            raise RuntimeError("trajectory identity changed")
        if actual.cycle!=current.last_event.cycle+int(index==14):
            raise RuntimeError("cycle count changed outside M15-to-M1")
        if after.peaks!=current.peaks:
            raise RuntimeError("peak memory changed without a declared observer")
        current=after
    return PeriodAttempt("NEXT_SH1_SECTION_REACHED_NOT_PERIODICITY",start,tuple(steps),current,current,None)
