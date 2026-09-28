"""D14: endpoint volt-second accounting, P25 native three-phase one module.

Keeps real node residual and optional winding R; no fixed-Vo timing budget.
No assertion of first-event order, periodicity or startup reachability.
"""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class FreewheelMargin:
    phase: int
    start_s: float
    end_s: float
    initial_flux_vs: float
    output_volt_seconds: float
    switch_node_volt_seconds: float
    winding_volt_seconds: float
    consumed_flux_vs: float
    remaining_flux_vs: float
    predicted_current_a: float
    actual_current_a: float
    balance_residual_vs: float
    sign_status: str
    scope: str = "ENDPOINT_ACCOUNTING_ONLY; not a first-root/periodic feasibility certificate"


def freewheel_margin(flow, phase: int, end_s: float, *, current_tolerance_a: float) -> FreewheelMargin:
    s=flow.start; b=s.boundary
    if b.branch!="P25" or b.nP!=3 or b.nM!=1 or b.module!=1:
        raise ValueError("P25 native three-phase single module only")
    if type(phase) is not int or not 1<=phase<=3:
        raise ValueError("phase must be 1, 2 or 3")
    k=phase-1
    if not s.gates.low[k] or s.gates.high[k]:
        raise ValueError("selected phase must freewheel through its ON low-side gate")
    if not isfinite(current_tolerance_a) or current_tolerance_a<0:
        raise ValueError("explicit finite current tolerance required")
    z=flow.integrated_coordinates(end_s); end=flow.at(end_s)
    inductance=flow.parts.inductance_h[k]
    initial=inductance*s.current_a[k]
    output=float(z[5]); node=float(z[2+k]); winding=flow.parts.winding_ohm[k]*float(z[6+k])
    consumed=output-node+winding
    remaining=initial-consumed
    predicted=remaining/inductance; actual=end.current_a[k]
    status="POSITIVE_AT_ENDPOINT" if actual>current_tolerance_a else (
        "NEGATIVE_AT_ENDPOINT" if actual < -current_tolerance_a else "ZERO_BAND_AT_ENDPOINT")
    return FreewheelMargin(phase,s.time_s,end_s,initial,output,node,winding,consumed,remaining,
                           predicted,actual,remaining-inductance*actual,status)
