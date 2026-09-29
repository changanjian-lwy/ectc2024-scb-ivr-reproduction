"""D13/D17/D41: P25 nP=3/nM=1 negative target, timed low-off and next-high handoff.

Fixed constant-port linear device boundary inherited from D10. Conditional
sampled event coverage, no parameter fitting, state projection or gate timeout.
"""
from math import isfinite
import numpy as np
from .p25_cycle_modes import cycle_mode, current_signs, commutation_target
from .p25_control_memory import Stage, Trigger, transition, phase_shift_due
from .p25_handoff import LowHandoff
from .p25_local_flow import LocalFlow, ScanReport, scan_commutation
from .p25_nodal_contract import SWITCHES
from .p25_reverse_contract import resolve_local_reverse
from .p25_root_location import Quantity, EventWindow, order_windows, locate_downward, ideal_gate_reverse_batch, trace_key


def _contract(memory, stage, policy, reverse, voltage_root, current_root, electrical, end_s, intervals):
    b=memory.last_event.boundary
    if b.branch!="P25" or b.nP!=3 or b.nM!=1 or b.module!=1:
        raise ValueError("P25 native three-phase single module only")
    if type(memory.phase) is not int or memory.phase not in (1,2,3) or memory.stage!=stage:
        raise ValueError("native phase and correct stage required")
    if reverse.kind!="ideal_zero_drop":
        raise ValueError("explicit ideal-zero-drop branch required")
    if not (voltage_root.value_tolerance==policy.voltage_tolerance_v==electrical.voltage_v and
            current_root.value_tolerance==policy.current_tolerance_a==electrical.current_a):
        raise ValueError("cross-layer V/A tolerances must match")
    if not isfinite(end_s) or end_s<=memory.last_event.time_s or type(intervals) is not int or intervals<1:
        raise ValueError("finite forward horizon and positive sample count required")


def reach_negative_target(memory, parts, ports, policy, reverse, *, end_s, intervals,
                          voltage_root, current_root, electrical, current_rate_tolerance_a_s):
    """Next-phase negative target. D06 latch is immutable; no new peak estimate."""
    _contract(memory,Stage.NEGATIVE,policy,reverse,voltage_root,current_root,electrical,end_s,intervals)
    target=memory.latched_target_a
    if target is None or not isfinite(target) or target>=0:
        raise ValueError("explicit previously latched negative target required")
    if not isfinite(current_rate_tolerance_a_s) or current_rate_tolerance_a_s<0:
        raise ValueError("explicit A/s tolerance required")
    s=memory.last_event
    mode=f"M{5*(memory.phase-1)+4}"
    following=f"M{5*(memory.phase-1)+5}"
    q=cycle_mode(mode).next_phase-1
    event=f"target.iL{q+1}_negative"
    flow=LocalFlow(s,parts,mode,ports,voltage_tolerance_v=policy.voltage_tolerance_v)
    watches=[Quantity(event,"A",lambda x:x.current_a[q]-target)]
    for k,sign in enumerate(current_signs(mode)):
        watches.append(Quantity(f"domain.iL{k+1}","A",lambda x,k=k,d=sign:d*x.current_a[k]))
    for k,name in enumerate(SWITCHES[:3]):
        watches.append(Quantity("reverse."+name,"V",lambda x,k=k,n=name:x.switch_voltage(n)+reverse.drop_v[k]))
    # At exact next-phase current=0, accept only inward derivative under this fixed mode.
    # Small negative current from root location is retained, never reset to zero.
    rhs=flow.generator@np.r_[s.voltage_v,s.current_a,1.]
    released=set()
    blockers=[]
    for w in watches:
        value=w.evaluate(s)
        if w.name==f"domain.iL{q+1}":
            if value==0 and -rhs[6+q]>current_rate_tolerance_a_s:
                released.add(w.name)
            elif value<=0:
                blockers.append(w.name)
        elif value <= (voltage_root.value_tolerance if w.unit=="V" else current_root.value_tolerance):
            blockers.append(w.name)
    if blockers:
        return LowHandoff(f"{mode}_ENTRY_UNRESOLVED",ScanReport("ENTRY_BOUNDARY_UNRESOLVED",tuple(blockers),(),s.time_s),
                          None,None,None,"entry domain/target must be resolved without reset")
    left=s
    for t in np.linspace(s.time_s,end_s,intervals+1)[1:]:
        right=flow.at(float(t)); roots=[]
        if released and -right.current_a[q]<=0:
            return LowHandoff(f"{mode}_ENTRY_RELEASE_UNRESOLVED",ScanReport("ENTRY_RELEASE_NOT_RESOLVED_ON_GRID",
                tuple(sorted(released)),(),float(t)),None,None,None,"no positive signed-current sample after release")
        for w in watches:
            if w.evaluate(left)>0 and w.evaluate(right)<=0:
                roots.append(locate_downward(w,flow.at,left_s=left.time_s,right_s=right.time_s,
                    settings=voltage_root if w.unit=="V" else current_root))
        if roots:
            windows=tuple(EventWindow.from_root(r) for r in roots); order=order_windows(windows)
            scan=ScanReport(order.status,order.possible_first,windows,float(t))
            if order.possible_first!=(event,):
                return LowHandoff(f"OTHER_{mode}_BOUNDARY_FIRST_OR_OVERLAP",scan,None,None,None,
                                  "negative target not reached before competing event")
            root=next(r for r in roots if r.name==event)
            kwargs=dict(dvin_v_s=0.,load_current_a=ports.load_current_a,
                        other_modules_current_a=ports.other_modules_current_a,tolerances=electrical)
            try:
                pre=resolve_local_reverse(root.right,parts,reverse,**kwargs)
                if pre.status!="LOCAL_COMPLEMENTARITY_ONLY":
                    return LowHandoff(f"{mode}_ROOT_ELECTRICALLY_UNRESOLVED",scan,None,pre.status,None,"reverse resolution")
                after=transition(memory,Trigger.NEGATIVE_TARGET,root.right,left=root.left,policy=policy)
                post=resolve_local_reverse(after.last_event,parts,reverse,**kwargs)
            except ValueError as exc:
                return LowHandoff("NEGATIVE_TARGET_EVENT_REJECTED",scan,None,None,None,str(exc))
            if post.status!="LOCAL_COMPLEMENTARITY_ONLY":
                return LowHandoff(f"{following}_ENTRY_ELECTRICALLY_UNRESOLVED",scan,None,pre.status,post.status,"reverse resolution")
            if any(c.reverse_active for c in post.candidates):
                return LowHandoff(f"{following}_REQUIRES_ACTIVE_REVERSE_FLOW",scan,None,pre.status,post.status,
                                  "D10 unclamped continuation cannot advance an active reverse channel")
            return LowHandoff(f"CONDITIONAL_{following}_ENTRY",scan,after,pre.status,post.status,
                              f"SL{q+1} off at latched negative target; electrical state unchanged")
        released.clear(); left=right
    return LowHandoff(f"{mode}_NO_EVENT_OBSERVED",ScanReport("NO_DOWNWARD_BRACKET_OBSERVED",(),(),end_s),
                      None,None,None,"finite horizon only, not physical infeasibility")


def reach_phase_shift_due(memory, parts, ports, policy, reverse, *, end_s, intervals,
                          voltage_root, current_root, electrical, current_rate_tolerance_a_s):
    """D41: a timed phase's low side turns off at its declared phase-shift time.

    Mirrors D18's scheduled high-off: every OFF reverse gap and every current
    domain of this mode is screened up to the due time; a competing physical
    event is reported, never overridden by the timer. The latched D06 target is
    NOT used for a timed phase. `end_s` is only a sanity bound on the due time.
    """
    _contract(memory,Stage.NEGATIVE,policy,reverse,voltage_root,current_root,electrical,end_s,intervals)
    if not isfinite(current_rate_tolerance_a_s) or current_rate_tolerance_a_s<0:
        raise ValueError("explicit A/s tolerance required")
    s=memory.last_event
    mode=f"M{5*(memory.phase-1)+4}"
    following=f"M{5*(memory.phase-1)+5}"
    q=cycle_mode(mode).next_phase-1
    if not policy.timed(q+1):
        raise ValueError("phase is current-sensed; use reach_negative_target")
    due=phase_shift_due(memory,policy,q+1)
    if not isfinite(due) or due<=s.time_s:
        return LowHandoff(f"{mode}_PHASE_SHIFT_DUE_NOT_AFTER_ENTRY",
            ScanReport("TIMER_NOT_AFTER_ENTRY",("control.phase_shift",),(),s.time_s),None,None,None,
            "timed low-off would precede the zero crossing that opened this stage")
    if due>end_s:
        raise ValueError("declared search horizon ends before the phase-shift time")
    flow=LocalFlow(s,parts,mode,ports,voltage_tolerance_v=policy.voltage_tolerance_v)
    watches=[]
    for k,sign in enumerate(current_signs(mode)):
        watches.append(Quantity(f"domain.iL{k+1}","A",lambda x,k=k,d=sign:d*x.current_a[k]))
    for k,name in enumerate(SWITCHES[:3]):
        watches.append(Quantity("reverse."+name,"V",lambda x,k=k,n=name:x.switch_voltage(n)+reverse.drop_v[k]))
    rhs=flow.generator@np.r_[s.voltage_v,s.current_a,1.]
    released=set(); blockers=[]
    for w in watches:
        value=w.evaluate(s)
        if w.name==f"domain.iL{q+1}":
            if value==0 and -rhs[6+q]>current_rate_tolerance_a_s:
                released.add(w.name)
            elif value<=0:
                blockers.append(w.name)
        elif value <= (voltage_root.value_tolerance if w.unit=="V" else current_root.value_tolerance):
            blockers.append(w.name)
    if blockers:
        return LowHandoff(f"{mode}_ENTRY_UNRESOLVED",ScanReport("ENTRY_BOUNDARY_UNRESOLVED",tuple(blockers),(),s.time_s),
                          None,None,None,"entry domain must be resolved without reset")
    clock=EventWindow("control.phase_shift",due,due,trace_key(s),"declared D41 phase-shift endpoint")
    left=s
    for t in np.linspace(s.time_s,due,intervals+1)[1:]:
        right=flow.at(float(t)); windows=[]
        if released and -right.current_a[q]<=0:
            return LowHandoff(f"{mode}_ENTRY_RELEASE_UNRESOLVED",ScanReport("ENTRY_RELEASE_NOT_RESOLVED_ON_GRID",
                tuple(sorted(released)),(),float(t)),None,None,None,"no positive signed-current sample after release")
        for w in watches:
            if w.evaluate(left)>0 and w.evaluate(right)<=0:
                root=locate_downward(w,flow.at,left_s=left.time_s,right_s=right.time_s,
                    settings=voltage_root if w.unit=="V" else current_root)
                windows.append(EventWindow.from_root(root))
        if windows:
            supplied=tuple(windows)+(clock,)
            order=order_windows(supplied)
            return LowHandoff(f"OTHER_{mode}_BOUNDARY_BEFORE_PHASE_SHIFT",
                ScanReport(order.status,order.possible_first,supplied,float(t)),None,None,None,
                "competing physical event is not overridden by the phase-shift timer")
        released.clear(); left=right
    margin=tuple(w.name for w in watches if w.evaluate(left)<=
                 (voltage_root.value_tolerance if w.unit=="V" else current_root.value_tolerance))
    if margin:
        return LowHandoff(f"{mode}_PHASE_SHIFT_MARGIN_UNRESOLVED",
            ScanReport("ENDPOINT_BOUNDARY_UNRESOLVED",margin,(clock,),due),None,None,None,
            "near-boundary endpoint needs resolution before gate action")
    scan=ScanReport("SCHEDULED_LOW_OFF_AFTER_SAMPLED_SCREEN",("control.phase_shift",),(clock,),due)
    kwargs=dict(dvin_v_s=0.,load_current_a=ports.load_current_a,
                other_modules_current_a=ports.other_modules_current_a,tolerances=electrical)
    try:
        pre=resolve_local_reverse(left,parts,reverse,**kwargs)
        if pre.status!="LOCAL_COMPLEMENTARITY_ONLY":
            return LowHandoff(f"{mode}_PHASE_SHIFT_PRE_ELECTRICALLY_UNRESOLVED",scan,None,pre.status,None,"reverse resolution")
        after=transition(memory,Trigger.PHASE_SHIFT_DUE,left,policy=policy)
        post=resolve_local_reverse(after.last_event,parts,reverse,**kwargs)
    except ValueError as exc:
        return LowHandoff("PHASE_SHIFT_EVENT_REJECTED",scan,None,None,None,str(exc))
    if post.status!="LOCAL_COMPLEMENTARITY_ONLY":
        return LowHandoff(f"{following}_ENTRY_ELECTRICALLY_UNRESOLVED",scan,None,pre.status,post.status,"reverse resolution")
    if any(c.reverse_active for c in post.candidates):
        return LowHandoff(f"{following}_REQUIRES_ACTIVE_REVERSE_FLOW",scan,None,pre.status,post.status,
                          "D10 unclamped continuation cannot advance an active reverse channel")
    return LowHandoff(f"CONDITIONAL_{following}_ENTRY",scan,after,pre.status,post.status,
                      f"SL{q+1} off at declared phase shift; iL{q+1}={left.current_a[q]:.6g} A; electrical state unchanged")


def enter_next_high(memory, parts, ports, policy, reverse, *, end_s, intervals,
                      voltage_root, current_root, electrical, direction):
    """Conditional next-high zero/reverse event, including M15 -> M1 wrap."""
    _contract(memory,Stage.UP_COMM,policy,reverse,voltage_root,current_root,electrical,end_s,intervals)
    mode=f"M{5*memory.phase}"
    target=commutation_target(mode)
    following=f"M{5*(cycle_mode(mode).next_phase-1)+1}"
    flow=LocalFlow(memory.last_event,parts,mode,ports,voltage_tolerance_v=policy.voltage_tolerance_v)
    scan=scan_commutation(flow,reverse,end_s=end_s,intervals=intervals,
        voltage_settings=voltage_root,current_settings=current_root,entry_direction=direction)
    if set(scan.candidates)!={"target."+target,"reverse."+target} or not scan.windows:
        return LowHandoff("BLOCKED_BEFORE_JOINT_HIGH_EVENT",scan,None,None,None,
                          "target/reverse pair not isolated as first supplied candidate set")
    window=next(w for w in scan.windows if w.name=="target."+target)
    root=locate_downward(Quantity("target."+target,"V",lambda s:s.switch_voltage(target)),
        flow.at,left_s=window.earliest_s,right_s=window.latest_s,settings=voltage_root)
    try:
        after,pre,post=ideal_gate_reverse_batch(memory,Trigger.NEXT_HIGH_ZERO,root.right,left=root.left,
            policy=policy,parts=parts,reverse_model=reverse,dvin_v_s=0.,
            load_current_a=ports.load_current_a,other_modules_current_a=ports.other_modules_current_a,
            tolerances=electrical)
    except ValueError as exc:
        return LowHandoff("JOINT_HIGH_EVENT_REJECTED",scan,None,None,None,str(exc))
    return LowHandoff(f"CONDITIONAL_{following}_ENTRY",scan,after,pre.status,post.status,
                      f"{target} ZVS gate admission; negative entry current retained")


def enter_second_high(memory, *args, **kwargs):
    """Legacy first-handoff API; use enter_next_high for the full phase map."""
    if memory.phase != 1:
        raise ValueError("legacy second-high interface requires phase 1")
    return enter_next_high(memory, *args, **kwargs)
