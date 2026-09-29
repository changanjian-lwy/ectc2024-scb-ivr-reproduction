"""D18: P25 nP=3/nM=1 high-on interval with competing-event screening.

Constant-port linear flow, ideal-zero-drop reverse boundary, zero driver delay.
Finite-grid coverage is conditional; no sampled maximum is called a peak.
Only an unmodified high-on entry is accepted, not a resume that skips history.
"""
from math import isfinite
import numpy as np
from .p25_control_memory import Stage, Trigger, transition
from .p25_cycle_modes import current_signs
from .p25_handoff import LowHandoff
from .p25_local_flow import LocalFlow, ScanReport
from .p25_nodal_contract import SWITCHES
from .p25_reverse_contract import resolve_local_reverse
from .p25_root_location import Quantity, EventWindow, trace_key, order_windows, locate_downward


def advance_high_on(memory, parts, ports, policy, reverse, *, intervals,
                    voltage_root, current_root, electrical):
    """M1/M6/M11 -> M2/M7/M12 only if scheduled turn-off is admissible.

    OFF reverse gaps and the two other-phase current domains are monitored.
    Active-phase current can cross zero while its ideal channel remains ON.
    Peak memory is left unchanged: a peak observer is a separate contract.
    """
    s=memory.last_event
    b=s.boundary
    if b.branch!="P25" or b.nP!=3 or b.nM!=1 or b.module!=1:
        raise ValueError("P25 native three-phase single module only")
    if type(memory.phase) is not int or memory.phase not in (1,2,3) or memory.stage!=Stage.RISE:
        raise ValueError("native phase and RISE stage required")
    if not isfinite(memory.entered_at_s) or s.time_s!=memory.entered_at_s:
        raise ValueError("complete high-on entry required; do not skip unchecked history")
    if reverse.kind!="ideal_zero_drop":
        raise ValueError("explicit ideal-zero-drop boundary required")
    if type(intervals) is not int or intervals<1:
        raise ValueError("positive integer sample count required")
    if not (voltage_root.value_tolerance==policy.voltage_tolerance_v==electrical.voltage_v
            and current_root.value_tolerance==policy.current_tolerance_a==electrical.current_a):
        raise ValueError("cross-layer V/A tolerances must match")
    mode=f"M{5*(memory.phase-1)+1}"
    following=f"M{5*(memory.phase-1)+2}"
    due=memory.entered_at_s+policy.on_time_s[memory.phase-1]
    if not isfinite(due) or due<=s.time_s:
        raise ValueError("high-off time must be finite and representably later")
    flow=LocalFlow(s,parts,mode,ports,voltage_tolerance_v=policy.voltage_tolerance_v)
    watches=[]
    for name,on,drop in zip(SWITCHES,(*s.gates.high,*s.gates.low),reverse.drop_v):
        if not on:
            watches.append(Quantity("reverse."+name,"V",
                                    lambda x,n=name,d=drop:x.switch_voltage(n)+d))
    for k,sign in enumerate(current_signs(mode)):
        if sign:
            watches.append(Quantity(f"domain.iL{k+1}","A",lambda x,k=k:x.current_a[k]))
    def unresolved_at(state):
        return tuple(w.name for w in watches if w.evaluate(state)<=
                     (voltage_root.value_tolerance if w.unit=="V" else current_root.value_tolerance))
    entry=unresolved_at(s)
    if entry:
        return LowHandoff("HIGH_ON_ENTRY_UNRESOLVED",
            ScanReport("ENTRY_BOUNDARY_UNRESOLVED",entry,(),s.time_s),None,None,None,
            "no initial reverse/current boundary is skipped or projected")
    clock=EventWindow("control.high_off",due,due,trace_key(s),"explicit actual on-time endpoint")
    left=s
    for t in np.linspace(s.time_s,due,intervals+1)[1:]:
        right=flow.at(float(t)); windows=[]
        for w in watches:
            if w.evaluate(left)>0 and w.evaluate(right)<=0:
                root=locate_downward(w,flow.at,left_s=left.time_s,right_s=right.time_s,
                    settings=voltage_root if w.unit=="V" else current_root)
                windows.append(EventWindow.from_root(root))
        if windows:
            supplied=tuple(windows)+(clock,)
            order=order_windows(supplied)
            return LowHandoff("HIGH_ON_BOUNDARY_BEFORE_OR_AT_OFF",
                ScanReport(order.status,order.possible_first,supplied,float(t)),
                None,None,None,"competing physical event is not overridden by the turn-off timer")
        left=right
    margin=unresolved_at(left)
    if margin:
        return LowHandoff("HIGH_OFF_BOUNDARY_MARGIN_UNRESOLVED",
            ScanReport("ENDPOINT_BOUNDARY_UNRESOLVED",margin,(clock,),due),None,None,None,
            "near-boundary endpoint needs resolution before gate action")
    scan=ScanReport("SCHEDULED_OFF_AFTER_SAMPLED_SCREEN",("control.high_off",),(clock,),due)
    kwargs=dict(dvin_v_s=0.,load_current_a=ports.load_current_a,
                other_modules_current_a=ports.other_modules_current_a,tolerances=electrical)
    try:
        pre=resolve_local_reverse(left,parts,reverse,**kwargs)
        if pre.status!="LOCAL_COMPLEMENTARITY_ONLY":
            return LowHandoff("HIGH_OFF_PRE_ELECTRICALLY_UNRESOLVED",scan,None,pre.status,None,
                              "reverse solution not unique")
        after=transition(memory,Trigger.HIGH_OFF_DUE,left,policy=policy)
        post=resolve_local_reverse(after.last_event,parts,reverse,**kwargs)
    except ValueError as exc:
        return LowHandoff("HIGH_OFF_EVENT_REJECTED",scan,None,None,None,str(exc))
    if post.status!="LOCAL_COMPLEMENTARITY_ONLY":
        return LowHandoff("HIGH_OFF_POST_ELECTRICALLY_UNRESOLVED",scan,None,pre.status,post.status,
                          "reverse solution not unique")
    if any(c.reverse_active for c in post.candidates):
        return LowHandoff("HIGH_OFF_REQUIRES_ACTIVE_REVERSE_FLOW",scan,None,pre.status,post.status,
                          "unclamped local flow cannot advance an active reverse branch")
    return LowHandoff(f"CONDITIONAL_{following}_ENTRY",scan,after,pre.status,post.status,
                      "actual on-time preserved; electrical state and peak records unchanged")
