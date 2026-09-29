"""D23: full affine-network commutation balance; not isolated-device Qoss."""
from dataclasses import dataclass
import numpy as np
from .p25_cycle_modes import cycle_mode,commutation_target
from .p25_nodal_contract import incidence,SWITCHES


@dataclass(frozen=True)
class CommutationCharge:
    target: str
    phase: int
    start_vds_v: float
    end_vds_v: float
    normalized_capacitance_f: float
    required_normalized_charge_c: float
    negative_phase_charge_c: float
    other_normalized_charge_c: float
    remaining_normalized_charge_c: float
    voltage_balance_residual_v: float
    rate_coefficients: tuple[float,...]
    scope: str = "AFFINE_ENDPOINT_ACCOUNTING; not device Qoss, first-root or ZVS feasibility proof"


def commutation_charge(flow, end_s):
    """Normalize Vds evolution by its active-phase current coefficient.

    ALL other coordinate/bias terms are retained, including tiny floating-point
    coefficients. C_norm=1/k is a network transfer normalization, not the
    MOSFET capacitor value. Caller owns the accepted interval boundary.
    """
    b=flow.start.boundary; spec=cycle_mode(flow.mode)
    if b.branch!="P25" or b.nP!=3 or b.nM!=1 or b.module!=1 or spec.slot!="up_comm":
        raise ValueError("P25 single-module M5/M10/M15 flow required")
    target=commutation_target(flow.mode); q=spec.next_phase-1
    w=incidence()[1:,SWITCHES.index(target)]@flow.generator[:6]
    coefficient=float(w[6+q])
    if not np.isfinite(coefficient) or coefficient<=0:
        raise ValueError("positive finite phase-to-target coefficient required")
    integrated=flow.integrated_coordinates(end_s)
    terms=w[:9]*integrated
    bias=w[9]*(end_s-flow.start.time_s)
    phase_delta=float(terms[6+q])
    other=float(np.sum(np.delete(terms,6+q))+bias)
    end=flow.at(end_s)
    initial=flow.start.switch_voltage(target); final=end.switch_voltage(target)
    c=1/coefficient
    return CommutationCharge(target,q+1,initial,final,c,c*initial,
        -float(integrated[6+q]),-c*other,c*final,
        final-initial-phase_delta-other,tuple(float(x) for x in w))
