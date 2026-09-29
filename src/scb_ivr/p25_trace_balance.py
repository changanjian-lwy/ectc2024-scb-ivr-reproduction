"""D28: integral ledger for accepted segments; failed trial points excluded."""
from dataclasses import dataclass
import numpy as np
from .p25_local_flow import LocalFlow
from .p25_nodal_contract import incidence


@dataclass(frozen=True)
class SegmentBalance:
    mode: str
    start_s: float
    end_s: float
    net_output_charge_c: float
    inductor_volt_seconds: tuple[float,...]
    capacitor_charge_c: tuple[float,...]


@dataclass(frozen=True)
class TraceBalance:
    coverage: str
    segments: tuple[SegmentBalance,...]
    total_output_charge_c: float
    output_charge_residual_c: float
    inductor_residual_vs: tuple[float,...]
    capacitor_residual_c: tuple[float,...]
    scope: str = "INTEGRAL_STATE_BALANCE; not first-event, periodicity or stability certificate"


def trace_balance(attempt,parts,ports,*,voltage_tolerance_v):
    """Use D10 augmented-exponential integrals, no sampled quadrature.

    Input is a single D19 trace, not independent successful fixtures.
    Reports identity residuals; a prefix need not have zero net charge/flux.
    """
    current=attempt.start; rows=[]
    cap_total=np.zeros(9); flux_total=np.zeros(3); output_total=0.
    for index,step in enumerate(attempt.steps):
        if step.before!=current or step.mode!=f"M{index+1}":
            raise ValueError("disconnected or reordered trace")
        if step.outcome.memory is None:
            if index!=len(attempt.steps)-1 or attempt.end is not None:
                raise ValueError("failed segment must terminate a partial attempt")
            break  # Do not integrate to a trial/root endpoint not accepted.
        after=step.outcome.memory
        flow=LocalFlow(current.last_event,parts,step.mode,ports,voltage_tolerance_v=voltage_tolerance_v)
        dt=after.last_event.time_s-current.last_event.time_s
        if dt<=0: raise ValueError("forward accepted segment required")
        z=flow.integrated_coordinates(after.last_event.time_s)
        output=float(sum(z[6:9])+(ports.other_modules_current_a-ports.load_current_a)*dt)
        flux=z[2:5]-z[5]-np.array(parts.winding_ohm)*z[6:9]
        integrated_dv=flow.generator[:6]@np.r_[z,dt]
        cap=parts.capacitances()*(incidence().T@np.r_[0.,integrated_dv])
        rows.append(SegmentBalance(step.mode,current.last_event.time_s,after.last_event.time_s,
                                   output,tuple(flux),tuple(cap)))
        output_total+=output; flux_total+=flux; cap_total+=cap; current=after
    if current!=attempt.last_accepted:
        raise ValueError("last accepted state does not match trace prefix")
    complete=attempt.end is not None
    if complete and (len(rows)!=15 or attempt.end!=current or attempt.failed_mode is not None):
        raise ValueError("full-cycle coverage requires all 15 accepted stages")
    a=attempt.start.last_event; b=current.last_event
    delta_v=np.array(b.voltage_v)-a.voltage_v
    actual_cap=parts.capacitances()*(incidence().T@np.r_[b.vin_v-a.vin_v,delta_v])
    actual_flux=np.array(parts.inductance_h)*(np.array(b.current_a)-a.current_a)
    return TraceBalance("FULL_CYCLE_ATTEMPT" if complete else "ACCEPTED_PREFIX_ONLY",
        tuple(rows),output_total,output_total-parts.output_f*delta_v[5],
        tuple(flux_total-actual_flux),tuple(cap_total-actual_cap))
