"""D13: P25 nP=3/nM=1 M4 negative target and M5 -> M6 handoff.

Fixed constant-port linear device boundary inherited from D10. Conditional
sampled event coverage, no parameter fitting, state projection or gate timeout.
"""
from math import isfinite
import numpy as np
from .p25_control_memory import Stage, Trigger, transition
from .p25_handoff import LowHandoff
from .p25_local_flow import LocalFlow, ScanReport, scan_commutation
from .p25_nodal_contract import SWITCHES
from .p25_reverse_contract import resolve_local_reverse
from .p25_root_location import Quantity, EventWindow, order_windows, locate_downward, ideal_gate_reverse_batch


def _contract(memory, stage, policy, reverse, voltage_root, current_root, electrical, end_s, intervals):
    b=memory.last_event.boundary
    if b.branch!="P25" or b.nP!=3 or b.nM!=1 or b.module!=1:
        raise ValueError("P25 native three-phase single module only")
    if memory.phase!=1 or memory.stage!=stage:
        raise ValueError("first handoff only; wrong stage or phase")
    if reverse.kind!="ideal_zero_drop":
        raise ValueError("explicit ideal-zero-drop branch required")
    if not (voltage_root.value_tolerance==policy.voltage_tolerance_v==electrical.voltage_v and
            current_root.value_tolerance==policy.current_tolerance_a==electrical.current_a):
        raise ValueError("cross-layer V/A tolerances must match")
    if not isfinite(end_s) or end_s<=memory.last_event.time_s or type(intervals) is not int or intervals<1:
        raise ValueError("finite forward horizon and positive sample count required")


def reach_negative_target(memory, parts, ports, policy, reverse, *, end_s, intervals,
                          voltage_root, current_root, electrical, current_rate_tolerance_a_s):
    """M4 -> M5. Latch from D06 is immutable; do not estimate a new peak."""
    _contract(memory,Stage.NEGATIVE,policy,reverse,voltage_root,current_root,electrical,end_s,intervals)
    target=memory.latched_target_a
    if target is None or not isfinite(target) or target>=0:
        raise ValueError("explicit previously latched negative target required")
    if not isfinite(current_rate_tolerance_a_s) or current_rate_tolerance_a_s<0:
        raise ValueError("explicit A/s tolerance required")
    s=memory.last_event
    flow=LocalFlow(s,parts,"M4",ports,voltage_tolerance_v=policy.voltage_tolerance_v)
    watches=[Quantity("target.iL2_negative","A",lambda x:x.current_a[1]-target)]
    for k,sign in enumerate((1,-1,1)):
        watches.append(Quantity(f"domain.iL{k+1}","A",lambda x,k=k,d=sign:d*x.current_a[k]))
    for k,name in enumerate(SWITCHES[:3]):
        watches.append(Quantity("reverse."+name,"V",lambda x,k=k,n=name:x.switch_voltage(n)+reverse.drop_v[k]))
    # At exact i2=0, accept only inward derivative under this fixed mode.
    # Small negative i2 from root location is retained, never reset to zero.
    rhs=flow.generator@np.r_[s.voltage_v,s.current_a,1.]
    released=set()
    blockers=[]
    for w in watches:
        value=w.evaluate(s)
        if w.name=="domain.iL2":
            if value==0 and -rhs[7]>current_rate_tolerance_a_s:
                released.add(w.name)
            elif value<=0:
                blockers.append(w.name)
        elif value <= (voltage_root.value_tolerance if w.unit=="V" else current_root.value_tolerance):
            blockers.append(w.name)
    if blockers:
        return LowHandoff("M4_ENTRY_UNRESOLVED",ScanReport("ENTRY_BOUNDARY_UNRESOLVED",tuple(blockers),(),s.time_s),
                          None,None,None,"entry domain/target must be resolved without reset")
    left=s
    for t in np.linspace(s.time_s,end_s,intervals+1)[1:]:
        right=flow.at(float(t)); roots=[]
        if released and -right.current_a[1]<=0:
            return LowHandoff("M4_ENTRY_RELEASE_UNRESOLVED",ScanReport("ENTRY_RELEASE_NOT_RESOLVED_ON_GRID",
                tuple(sorted(released)),(),float(t)),None,None,None,"no positive signed-current sample after release")
        for w in watches:
            if w.evaluate(left)>0 and w.evaluate(right)<=0:
                roots.append(locate_downward(w,flow.at,left_s=left.time_s,right_s=right.time_s,
                    settings=voltage_root if w.unit=="V" else current_root))
        if roots:
            windows=tuple(EventWindow.from_root(r) for r in roots); order=order_windows(windows)
            scan=ScanReport(order.status,order.possible_first,windows,float(t))
            if order.possible_first!=("target.iL2_negative",):
                return LowHandoff("OTHER_M4_BOUNDARY_FIRST_OR_OVERLAP",scan,None,None,None,
                                  "negative target not reached before competing event")
            root=next(r for r in roots if r.name=="target.iL2_negative")
            kwargs=dict(dvin_v_s=0.,load_current_a=ports.load_current_a,
                        other_modules_current_a=ports.other_modules_current_a,tolerances=electrical)
            try:
                pre=resolve_local_reverse(root.right,parts,reverse,**kwargs)
                if pre.status!="LOCAL_COMPLEMENTARITY_ONLY":
                    return LowHandoff("M4_ROOT_ELECTRICALLY_UNRESOLVED",scan,None,pre.status,None,"reverse resolution")
                after=transition(memory,Trigger.NEGATIVE_TARGET,root.right,left=root.left,policy=policy)
                post=resolve_local_reverse(after.last_event,parts,reverse,**kwargs)
            except ValueError as exc:
                return LowHandoff("NEGATIVE_TARGET_EVENT_REJECTED",scan,None,None,None,str(exc))
            if post.status!="LOCAL_COMPLEMENTARITY_ONLY":
                return LowHandoff("M5_ENTRY_ELECTRICALLY_UNRESOLVED",scan,None,pre.status,post.status,"reverse resolution")
            if any(c.reverse_active for c in post.candidates):
                return LowHandoff("M5_REQUIRES_ACTIVE_REVERSE_FLOW",scan,None,pre.status,post.status,
                                  "D10 unclamped continuation cannot advance an active reverse channel")
            return LowHandoff("CONDITIONAL_M5_ENTRY",scan,after,pre.status,post.status,
                              "SL2 off at latched negative target; electrical state unchanged")
        released.clear(); left=right
    return LowHandoff("M4_NO_EVENT_OBSERVED",ScanReport("NO_DOWNWARD_BRACKET_OBSERVED",(),(),end_s),
                      None,None,None,"finite horizon only, not physical infeasibility")


def enter_second_high(memory, parts, ports, policy, reverse, *, end_s, intervals,
                      voltage_root, current_root, electrical, direction):
    """M5 -> M6, conditional joint SH2-zero/SH2-reverse event, no forced turn-on."""
    _contract(memory,Stage.UP_COMM,policy,reverse,voltage_root,current_root,electrical,end_s,intervals)
    flow=LocalFlow(memory.last_event,parts,"M5",ports,voltage_tolerance_v=policy.voltage_tolerance_v)
    scan=scan_commutation(flow,reverse,end_s=end_s,intervals=intervals,
        voltage_settings=voltage_root,current_settings=current_root,entry_direction=direction)
    if set(scan.candidates)!={"target.SH2","reverse.SH2"} or not scan.windows:
        return LowHandoff("BLOCKED_BEFORE_JOINT_HIGH_EVENT",scan,None,None,None,
                          "target/reverse pair not isolated as first supplied candidate set")
    window=next(w for w in scan.windows if w.name=="target.SH2")
    root=locate_downward(Quantity("target.SH2","V",lambda s:s.switch_voltage("SH2")),
        flow.at,left_s=window.earliest_s,right_s=window.latest_s,settings=voltage_root)
    try:
        after,pre,post=ideal_gate_reverse_batch(memory,Trigger.NEXT_HIGH_ZERO,root.right,left=root.left,
            policy=policy,parts=parts,reverse_model=reverse,dvin_v_s=0.,
            load_current_a=ports.load_current_a,other_modules_current_a=ports.other_modules_current_a,
            tolerances=electrical)
    except ValueError as exc:
        return LowHandoff("JOINT_HIGH_EVENT_REJECTED",scan,None,None,None,str(exc))
    return LowHandoff("CONDITIONAL_M6_ENTRY",scan,after,pre.status,post.status,
                      "SH2 ZVS gate admission; negative entry current retained")
