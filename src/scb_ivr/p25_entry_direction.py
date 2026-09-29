"""D11/D40: P25 nP=3/nM=1 fixed-mode entry directions, without epsilon steps.

D11: exact zero with a strictly positive resolved first derivative can leave
a reverse boundary. D40 adds one explicit case: a reverse gap whose value lies
within the declared voltage tolerance (0 < |g| <= tol, either sign) AND whose
resolved rate is strictly outward (> rate tolerance) is released with its own
status, LEAVING_REVERSE_BOUNDARY_WITHIN_TOLERANCE. Such gaps are what a root
located to that same tolerance leaves behind (e.g. an ON switch preserving a
-6 nV ZVS-root residual into its next turn-off). The value is kept as is,
never projected to zero. Tangent, inward, target and current-domain cases
within the band remain blocked; values below -tol remain OUTSIDE_DOMAIN.
This classifier does not implement a reverse clamp or activate any gate.
"""
from dataclasses import dataclass
from math import isfinite
import numpy as np
from .p25_nodal_contract import SWITCHES, incidence
from .p25_reverse_contract import ReverseModel
from .p25_cycle_modes import current_signs, commutation_target


@dataclass(frozen=True)
class DirectionTolerance:
    voltage_v: float
    current_a: float
    voltage_rate_v_s: float
    current_rate_a_s: float

    def __post_init__(self):
        if not all(isfinite(x) and x>=0 for x in (
            self.voltage_v,self.current_a,self.voltage_rate_v_s,self.current_rate_a_s)):
            raise ValueError("explicit separate finite V/A/(V/s)/(A/s) tolerances required")


@dataclass(frozen=True)
class EntryItem:
    name: str
    value: float
    rate: float
    unit: str
    status: str


@dataclass(frozen=True)
class EntryReport:
    items: tuple[EntryItem,...]
    release_names: tuple[str,...]
    blockers: tuple[str,...]
    scope: str = "LOCAL_FIRST_DERIVATIVE_ONLY; no finite-interval certificate or gate action"


def classify_entry(flow, reverse: ReverseModel, tolerance: DirectionTolerance) -> EntryReport:
    s=flow.start
    if s.boundary.branch!="P25" or s.boundary.nP!=3 or s.boundary.nM!=1 or s.boundary.module!=1:
        raise ValueError("D11 currently requires P25 native three-phase SINGLE module")
    target=commutation_target(flow.mode)
    if not isinstance(reverse,ReverseModel):
        raise ValueError("explicit reverse surrogate required")
    dz=flow.generator@np.r_[s.voltage_v,s.current_a,1.]
    rates=incidence().T@np.r_[0.,dz[:6]]
    rows=[("target."+target,s.switch_voltage(target),rates[SWITCHES.index(target)],"V","target")]
    for k,(name,on) in enumerate(zip(SWITCHES,(*s.gates.high,*s.gates.low))):
        if not on:
            rows.append(("reverse."+name,s.switch_voltage(name)+reverse.drop_v[k],rates[k],"V","reverse"))
    signs=current_signs(flow.mode)
    for k,sign in enumerate(signs):
        rows.append((f"domain.iL{k+1}",sign*s.current_a[k],sign*dz[6+k],"A","domain"))
    items=[]
    for name,value,rate,unit,role in rows:
        tol=tolerance.voltage_v if unit=="V" else tolerance.current_a
        rt=tolerance.voltage_rate_v_s if unit=="V" else tolerance.current_rate_a_s
        if not isfinite(value) or not isfinite(rate):
            raise ValueError("nonfinite entry value/rate")
        if value!=0 and abs(value)<=tol and role=="reverse" and rate>rt:
            # D40: tolerance-band gap moving strictly outward; value retained, not projected
            status="LEAVING_REVERSE_BOUNDARY_WITHIN_TOLERANCE"
        elif value<0:
            status="OUTSIDE_DOMAIN"  # no projection even inside numerical tolerance
        elif value>tol:
            status="INTERIOR"
        elif value!=0:
            status="NEAR_BOUNDARY_UNRESOLVED"
        elif role=="target":
            status="TARGET_AT_ENTRY_REQUIRES_EVENT_ACTION"
        elif role=="domain":
            status="CURRENT_BOUNDARY_REQUIRES_EVENT_RULE"
        elif rate>rt:
            status="LEAVING_REVERSE_BOUNDARY"
        elif rate < -rt:
            status="REVERSE_RESOLUTION_REQUIRED"
        else:
            status="TANGENT_OR_RATE_UNRESOLVED"
        items.append(EntryItem(name,float(value),float(rate),unit,status))
    leaving={"LEAVING_REVERSE_BOUNDARY","LEAVING_REVERSE_BOUNDARY_WITHIN_TOLERANCE"}
    release=tuple(i.name for i in items if i.status in leaving)
    blockers=tuple(i.name for i in items if i.status not in {"INTERIOR",*leaving})
    return EntryReport(tuple(items),release,blockers)
