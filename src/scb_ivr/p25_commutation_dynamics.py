"""D25: full-flow check of the phase-specific forced second-order equation."""
from dataclasses import dataclass
import numpy as np
from .p25_commutation_closed_form import normalized_capacitance,switch_node_gain
from .p25_cycle_modes import cycle_mode,commutation_target
from .p25_nodal_contract import incidence,SWITCHES


@dataclass(frozen=True)
class CommutationDynamics:
    phase: int
    target: str
    normalized_capacitance_f: float
    node_capacitance_f: float
    gamma: float
    node_relation_residual_v: float
    ode_residual_v: float
    actual_output_v: float
    scope: str = "LOCAL_FORCED_ODE_IDENTITY; not isolated resonance or trajectory feasibility proof"


def audit_commutation_dynamics(flow, time_s):
    """LCn V'' + RCn V' + gamma V = xq0 + gamma V0 - Vo(t).

    Derivatives come independently from the full generator. Vo is the actual
    dynamic output state, not a substituted constant. No finite differencing.
    """
    s=flow.start
    cn=normalized_capacitance(s.boundary,flow.parts,flow.mode)
    gamma=switch_node_gain(s.boundary,flow.parts,flow.mode)
    q=cycle_mode(flow.mode).next_phase-1
    target=commutation_target(flow.mode)
    a=incidence()[1:,SWITCHES.index(target)]
    end=flow.at(time_s); y=np.r_[end.voltage_v,end.current_a,1.]
    first=flow.generator@y; second=flow.generator@first
    v0=s.switch_voltage(target); v=end.switch_voltage(target)
    vp=float(a@first[:6]); vpp=float(a@second[:6])
    x0=s.voltage_v[2+q]; x=end.voltage_v[2+q]; vo=end.voltage_v[5]
    lhs=flow.parts.inductance_h[q]*cn*vpp+flow.parts.winding_ohm[q]*cn*vp+gamma*v
    rhs=x0+gamma*v0-vo
    return CommutationDynamics(q+1,target,cn,cn/gamma,gamma,
                              x-x0+gamma*(v-v0),lhs-rhs,vo)
