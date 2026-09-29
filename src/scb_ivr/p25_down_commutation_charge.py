"""D35: low-side commutation charge from the SAME full-network trajectory."""
from dataclasses import dataclass
import numpy as np
from .p25_cycle_modes import cycle_mode, commutation_target
from .p25_commutation_closed_form import normalized_capacitance, switch_node_gain


@dataclass(frozen=True)
class DownCommutationCharge:
    target: str
    phase: int
    start_vds_v: float
    end_vds_v: float
    closed_form_capacitance_f: float
    network_rate_capacitance_f: float
    required_charge_c: float
    phase_charge_c: float
    other_charge_c: float
    remaining_charge_c: float
    voltage_balance_residual_v: float
    scope: str = "LOCAL_CONTINUATION_ACCOUNTING; caller owns first-event boundary; not device Qoss"


def down_commutation_charge(flow, end_s):
    spec = cycle_mode(flow.mode)
    if spec.slot != "down_comm":
        raise ValueError("P25 down commutation M2/M7/M12 required")
    # Same physical gate pattern, different target and allowed current sign.
    paired = {"M2":"M15", "M7":"M5", "M12":"M10"}[flow.mode]
    if spec.gates != cycle_mode(paired).gates or flow.start.gates != spec.gates:
        raise ValueError("paired physical gate pattern mismatch")
    q = spec.phase-1
    closed = normalized_capacitance(flow.start.boundary,flow.parts,paired)/switch_node_gain(
        flow.start.boundary,flow.parts,paired)
    w = flow.generator[2+q]
    coefficient = -float(w[6+q])
    if not np.isfinite(coefficient) or coefficient <= 0:
        raise ValueError("negative finite phase-to-low-voltage coefficient required")
    c = 1/coefficient
    z = flow.integrated_coordinates(end_s)
    terms = w[:9]*z
    phase_delta = float(terms[6+q])
    other = float(np.sum(np.delete(terms,6+q))+w[9]*(end_s-flow.start.time_s))
    target = commutation_target(flow.mode)
    start = flow.start.switch_voltage(target)
    end = flow.at(end_s).switch_voltage(target)
    return DownCommutationCharge(target,q+1,start,end,closed,c,c*start,float(z[6+q]),
        -c*other,c*end,end-start-phase_delta-other)
