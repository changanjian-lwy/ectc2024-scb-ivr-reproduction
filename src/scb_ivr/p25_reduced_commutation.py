"""D26: five coupled local states, independently assembled from D24/D25.

This is pre-event mathematical continuation, NOT an event detector. D27 adds
full snapshots, but the main event executor still uses the full-node flow.
"""
from dataclasses import dataclass, replace
from math import isfinite
import numpy as np
from scipy.linalg import expm
from .p25_cycle_modes import cycle_mode,commutation_target
from .p25_nodal_contract import SWITCHES
from .p25_commutation_closed_form import normalized_capacitance,switch_node_gain,voltage_reconstruction_slopes


@dataclass(frozen=True)
class ReducedState:
    time_s: float
    target_vds_v: float
    current_a: tuple[float,float,float]
    output_v: float


class ReducedCommutation:
    def __init__(self,start,parts,mode,ports,*,gate_tolerance_v):
        cn=normalized_capacitance(start.boundary,parts,mode)
        gamma=switch_node_gain(start.boundary,parts,mode)
        spec=cycle_mode(mode)
        if start.boundary.output_boundary!="dynamic_Co_current_ports" or ports.other_modules_current_a!=0:
            raise ValueError("single-module dynamic output current-port boundary required")
        if start.gates!=spec.gates:
            raise ValueError("mode/gate mismatch")
        if not isfinite(gate_tolerance_v) or gate_tolerance_v<0:
            raise ValueError("explicit finite gate voltage tolerance required")
        for name,on in zip(SWITCHES,(*start.gates.high,*start.gates.low)):
            if on and abs(start.switch_voltage(name))>gate_tolerance_v:
                raise ValueError("ideal ON constraint violated; no projection")
        q=spec.next_phase-1
        self.start=start; self.target=commutation_target(mode)
        self.voltage_slopes=voltage_reconstruction_slopes(start.boundary,parts,mode)
        v0=start.switch_voltage(self.target)
        g=np.zeros((6,6))  # Vtarget, i1, i2, i3, Vo, constant 1
        g[0,1+q]=1/cn
        for k in range(3):
            g[1+k,1+k]=-parts.winding_ohm[k]/parts.inductance_h[k]
            g[1+k,4]=-1/parts.inductance_h[k]
            g[1+k,5]=start.voltage_v[2+k]/parts.inductance_h[k]
        g[1+q,0]=-gamma/parts.inductance_h[q]
        g[1+q,5]+=gamma*v0/parts.inductance_h[q]
        g[4,1:4]=1/parts.output_f
        g[4,5]=-ports.load_current_a/parts.output_f
        g.setflags(write=False); self.generator=g
        initial=np.r_[v0,start.current_a,start.voltage_v[5],1.]
        initial.setflags(write=False); self.initial=initial

    def at(self,time_s):
        if not isfinite(time_s) or time_s<self.start.time_s:
            raise ValueError("finite forward time required")
        y=expm(self.generator*(time_s-self.start.time_s))@self.initial
        if not np.all(np.isfinite(y)): raise ArithmeticError("nonfinite reduced continuation")
        return ReducedState(time_s,float(y[0]),tuple(float(x) for x in y[1:4]),float(y[4]))

    def snapshot_at(self,time_s):
        """Reconstruct all nodes from their own entry constants, no state reset.

        Snapshot availability is not a certificate that preceding guards hold.
        """
        reduced=self.at(time_s)
        if time_s==self.start.time_s:
            return self.start
        delta=reduced.target_vds_v-self.initial[0]
        voltage=tuple(float(v+s*delta) for v,s in zip(self.start.voltage_v[:5],self.voltage_slopes))
        return replace(self.start,time_s=time_s,voltage_v=(*voltage,reduced.output_v),
                       current_a=reduced.current_a)
