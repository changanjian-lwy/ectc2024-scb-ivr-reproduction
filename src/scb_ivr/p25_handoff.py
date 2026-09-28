"""D12: conditional P25 three-phase/single-module M2 -> M3 assembly.

Reuses D03/D05/D06/D07/D10/D11; no parameter defaults or electrical resets.
Finite-grid event completeness remains unproved, explicitly in every result.
"""
from dataclasses import dataclass
from math import isfinite
import numpy as np
from .p25_control_memory import Memory, Policy, Stage, Trigger, transition
from .p25_entry_direction import DirectionTolerance
from .p25_local_flow import LocalFlow, ConstantPorts, ScanReport, scan_commutation
from .p25_nodal_contract import Components, SWITCHES
from .p25_reverse_contract import ReverseModel, Tolerances, resolve_local_reverse
from .p25_root_location import Quantity, RootSettings, EventWindow, order_windows, locate_downward, ideal_gate_reverse_batch


@dataclass(frozen=True)
class LowHandoff:
    status: str
    scan: ScanReport
    memory: Memory | None
    pre_reverse_status: str | None
    post_reverse_status: str | None
    reason: str
    scope: str = "CONDITIONAL_SAMPLED_HANDOFF; not complete-cycle or startup evidence"


def enter_all_low(memory: Memory, parts: Components, ports: ConstantPorts,
                  policy: Policy, reverse: ReverseModel, *, end_s: float, intervals: int,
                  voltage_root: RootSettings, current_root: RootSettings,
                  direction: DirectionTolerance, electrical: Tolerances) -> LowHandoff:
    s=memory.last_event
    if s.boundary.nP!=3 or s.boundary.nM!=1 or s.boundary.branch!="P25":
        raise ValueError("P25 native three-phase single module only")
    if memory.phase!=1 or memory.stage!=Stage.DOWN_COMM:
        raise ValueError("first handoff DOWN_COMM only; phase rotation not yet wired")
    if reverse.kind!="ideal_zero_drop":
        raise ValueError("zero-delay/ideal-zero-drop joint event only")
    if not (direction.voltage_v==voltage_root.value_tolerance==policy.voltage_tolerance_v==electrical.voltage_v
            and direction.current_a==current_root.value_tolerance==policy.current_tolerance_a==electrical.current_a):
        raise ValueError("value tolerance contracts must match across layers")
    flow=LocalFlow(s,parts,"M2",ports,voltage_tolerance_v=policy.voltage_tolerance_v)
    scan=scan_commutation(flow,reverse,end_s=end_s,intervals=intervals,
        voltage_settings=voltage_root,current_settings=current_root,entry_direction=direction)
    compatible={"target.SL1","reverse.SL1"}
    if set(scan.candidates)!=compatible or not scan.windows:
        return LowHandoff("BLOCKED_BEFORE_JOINT_LOW_EVENT",scan,None,None,None,
                          "target/reverse pair not isolated as first supplied candidate set")
    # The two guards are algebraically identical only under ideal_zero_drop.
    # Their simultaneous interpretation is explicit; no arbitrary priority.
    window=next(w for w in scan.windows if w.name=="target.SL1")
    root=locate_downward(Quantity("target.SL1","V",lambda p:p.switch_voltage("SL1")),
        flow.at,left_s=window.earliest_s,right_s=window.latest_s,settings=voltage_root)
    try:
        after,before,post=ideal_gate_reverse_batch(memory,Trigger.LOW_ZERO,root.right,
            left=root.left,policy=policy,parts=parts,reverse_model=reverse,dvin_v_s=0.,
            load_current_a=ports.load_current_a,other_modules_current_a=ports.other_modules_current_a,
            tolerances=electrical)
    except ValueError as exc:
        return LowHandoff("JOINT_EVENT_REJECTED",scan,None,None,None,str(exc))
    return LowHandoff("CONDITIONAL_M3_ENTRY",scan,after,before.status,post.status,
                      "electrical state unchanged; pre/post complementarity checked; sampled coverage only")


def reach_second_current_zero(memory: Memory, parts: Components, ports: ConstantPorts,
                              policy: Policy, reverse: ReverseModel, *, end_s: float,
                              intervals: int, voltage_root: RootSettings,
                              current_root: RootSettings, electrical: Tolerances) -> LowHandoff:
    """M3 -> M4: all lows remain on, target -alpha*known peak is latched.

    No automatic peak estimate. All current domains and OFF reverse gaps watched.
    Returns the same structured outcome type, with no fabricated gate change.
    """
    s=memory.last_event
    if s.boundary.branch!="P25" or s.boundary.nP!=3 or s.boundary.nM!=1:
        raise ValueError("P25 native three-phase single module only")
    if memory.phase!=1 or memory.stage!=Stage.ALL_LOW:
        raise ValueError("first handoff ALL_LOW only")
    if not (policy.voltage_tolerance_v==voltage_root.value_tolerance==electrical.voltage_v and
            policy.current_tolerance_a==current_root.value_tolerance==electrical.current_a):
        raise ValueError("value tolerance contracts must match")
    if not isfinite(end_s) or end_s<=s.time_s or type(intervals) is not int or intervals<1:
        raise ValueError("explicit finite forward horizon and positive sample count required")
    flow=LocalFlow(s,parts,"M3",ports,voltage_tolerance_v=policy.voltage_tolerance_v)
    watches=[Quantity(f"domain.iL{k+1}","A",lambda x,k=k:x.current_a[k]) for k in range(3)]
    for k,name in enumerate(SWITCHES[:3]):
        watches.append(Quantity("reverse."+name,"V",lambda x,k=k,n=name:x.switch_voltage(n)+reverse.drop_v[k]))
    blockers=tuple(w.name for w in watches if w.evaluate(s)<=
                   (voltage_root.value_tolerance if w.unit=="V" else current_root.value_tolerance))
    if blockers:
        return LowHandoff("M3_ENTRY_UNRESOLVED",ScanReport("ENTRY_BOUNDARY_UNRESOLVED",blockers,(),s.time_s),
                          None,None,None,"M3 expects strictly interior current/gap guards")
    left=s
    for t in np.linspace(s.time_s,end_s,intervals+1)[1:]:
        right=flow.at(float(t)); roots=[]
        for w in watches:
            if w.evaluate(left)>0 and w.evaluate(right)<=0:
                roots.append(locate_downward(w,flow.at,left_s=left.time_s,right_s=right.time_s,
                    settings=voltage_root if w.unit=="V" else current_root))
        if roots:
            windows=tuple(EventWindow.from_root(r) for r in roots)
            order=order_windows(windows)
            scan=ScanReport(order.status,order.possible_first,windows,float(t))
            if order.possible_first!=("domain.iL2",):
                return LowHandoff("OTHER_M3_BOUNDARY_FIRST_OR_OVERLAP",scan,None,None,None,
                                  "do not skip another phase or reverse event")
            root=next(r for r in roots if r.name=="domain.iL2")
            kwargs=dict(dvin_v_s=0.,load_current_a=ports.load_current_a,
                        other_modules_current_a=ports.other_modules_current_a,tolerances=electrical)
            pre=resolve_local_reverse(root.right,parts,reverse,**kwargs)
            if pre.status!="LOCAL_COMPLEMENTARITY_ONLY":
                return LowHandoff("M3_ROOT_ELECTRICALLY_UNRESOLVED",scan,None,pre.status,None,"reverse resolution")
            try:
                after=transition(memory,Trigger.NEXT_CURRENT_ZERO,root.right,left=root.left,policy=policy)
            except ValueError as exc:
                return LowHandoff("M3_CONTROL_REJECTED",scan,None,pre.status,None,str(exc))
            post=resolve_local_reverse(after.last_event,parts,reverse,**kwargs)
            if post.status!="LOCAL_COMPLEMENTARITY_ONLY":
                return LowHandoff("M4_ENTRY_ELECTRICALLY_UNRESOLVED",scan,None,pre.status,post.status,"reverse resolution")
            return LowHandoff("CONDITIONAL_M4_ENTRY",scan,after,pre.status,post.status,
                              "current zero located; gates unchanged; causal negative target latched")
        left=right
    return LowHandoff("M3_NO_EVENT_OBSERVED",ScanReport("NO_DOWNWARD_BRACKET_OBSERVED",(),(),end_s),
                      None,None,None,"finite horizon without bracket is not proof of infeasibility")
