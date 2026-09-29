"""D22: necessary current-order bound, not a trajectory or ZVS certificate."""
from dataclasses import dataclass
from math import isfinite
from .p25_cycle_modes import cycle_mode


@dataclass(frozen=True)
class PhaseBudget:
    phase: int
    initial_flux_vs: float
    margin_at_target_vs: float
    status: str


@dataclass(frozen=True)
class AllLowNecessity:
    next_phase: int
    required_flux_vs: float
    rows: tuple[PhaseBudget,...]
    unsupported_phases: tuple[int,...]
    status: str
    scope: str = "NECESSARY_ORDER_ONLY; no target reachability, ZVS or periodicity proof"


def all_low_necessity(state, parts, mode, *, negative_target_a, flux_tolerance_vs):
    """For exact xk=xq=0, Rk=Rq=0: Lk*ik=Lk*ik0-Phi, Phi=integral Vo dt.

    To reach iq=target, Phi must reach Lq*(iq0-target). By continuity,
    another phase with a smaller positive Lk*ik0 crosses zero first.
    No constant/positive Vo assumption is needed for this NECESSARY bound.
    Nonzero numerical node residuals are NOT erased; unsupported pairs are
    reported explicitly. A declared V*s tolerance is only a numeric guard band.
    """
    b=state.boundary; spec=cycle_mode(mode)
    if b.branch!="P25" or b.nP!=3 or b.nM!=1 or b.module!=1:
        raise ValueError("P25 native three-phase single module only")
    if spec.slot!="all_low" or state.gates!=spec.gates:
        raise ValueError("all-low entry M3/M8/M13 required")
    if not isfinite(negative_target_a) or negative_target_a>=0:
        raise ValueError("explicit finite negative target required")
    if not isfinite(flux_tolerance_vs) or flux_tolerance_vs<0:
        raise ValueError("explicit finite nonnegative V*s tolerance required")
    if any(i<=0 for i in state.current_a):
        raise ValueError("strictly positive all-low entry currents required")
    q=spec.next_phase-1
    if parts.winding_ohm[q]!=0 or state.voltage_v[2+q]!=0:
        raise ValueError("target phase must have exact zero winding R and switch-node voltage")
    required=parts.inductance_h[q]*(state.current_a[q]-negative_target_a)
    rows=[]; skipped=[]
    for k in range(3):
        if k==q: continue
        if parts.winding_ohm[k]!=0 or state.voltage_v[2+k]!=0:
            skipped.append(k+1); continue
        budget=parts.inductance_h[k]*state.current_a[k]
        margin=budget-required
        status=("MUST_CROSS_BEFORE_TARGET" if margin < -flux_tolerance_vs else
                "ORDER_UNRESOLVED_OR_COINCIDENT" if margin<=flux_tolerance_vs else
                "NECESSARY_MARGIN_POSITIVE")
        rows.append(PhaseBudget(k+1,budget,margin,status))
    if any(r.status=="MUST_CROSS_BEFORE_TARGET" for r in rows):
        status="TARGET_BEFORE_ALL_OTHER_ZEROS_IMPOSSIBLE"
    elif skipped or any(r.status=="ORDER_UNRESOLVED_OR_COINCIDENT" for r in rows):
        status="NECESSARY_CHECK_INCOMPLETE"
    else:
        status="NECESSARY_CURRENT_ORDER_PASSED_NOT_SUFFICIENT"
    return AllLowNecessity(spec.next_phase,required,tuple(rows),tuple(skipped),status)
