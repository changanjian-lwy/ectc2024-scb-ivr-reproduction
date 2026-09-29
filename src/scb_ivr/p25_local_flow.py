"""D10: constant-port, fixed-gate affine flow and conditional event screening.

No gate actions, state resets, nonlinear devices or reverse-active continuation.
Matrix exponential is evaluated numerically. A sampled event scan is NOT a
certified first-root search: tangencies/multiple crossings may be missed.
"""
from dataclasses import dataclass, replace
from math import isfinite
import numpy as np
from scipy.linalg import expm

from .p25_event_guards import Snapshot
from .p25_cycle_modes import cycle_mode, current_signs, commutation_target
from .p25_nodal_contract import Components, SWITCHES, incidence, inductor_incidence, instantaneous_rates
from .p25_reverse_contract import ReverseModel, paper_mode_violations
from .p25_root_location import Quantity, RootSettings, locate_downward, EventWindow, order_windows


@dataclass(frozen=True)
class ConstantPorts:
    load_current_a: float
    other_modules_current_a: float
    declaration: str

    def __post_init__(self):
        if not all(isfinite(v) for v in (self.load_current_a, self.other_modules_current_a)) or not self.declaration.strip():
            raise ValueError("explicit finite constant-current ports and declaration required")


class LocalFlow:
    """One mathematical pre-event continuation, not an accepted mode trajectory."""
    def __init__(self, start: Snapshot, parts: Components, mode: str,
                 ports: ConstantPorts, *, voltage_tolerance_v: float):
        if start.gates != cycle_mode(mode).gates:
            raise ValueError("mode/gates mismatch")
        # D03 validates original algebraic constraints and module/port boundary.
        instantaneous_rates(start.boundary, parts, mode, voltage_v=start.voltage_v,
            current_a=start.current_a, vin_v=start.vin_v, dvin_v_s=0.,
            load_current_a=ports.load_current_a, other_modules_current_a=ports.other_modules_current_a,
            constraint_tolerance_v=voltage_tolerance_v,
            reverse_path_regime="off_reverse_channels_excluded_until_admission")
        self.start, self.parts, self.mode, self.ports = start, parts, mode, ports
        af = incidence(); a = af[1:]; b = inductor_incidence()[1:]
        c = (a*parts.capacitances())@a.T
        on = np.array((*start.gates.high,*start.gates.low))
        s = a[:,:6][:,on]
        kkt = np.block([[c,s],[s.T,np.zeros((s.shape[1],s.shape[1]))]])
        # Build derivative operator directly, NOT by projecting inadmissible
        # perturbed states through D03. Vin and both current ports are constant.
        rhs = np.zeros((len(kkt),10))
        rhs[:6,6:9] = -b
        rhs[5,9] = ports.other_modules_current_a-ports.load_current_a
        solution = np.linalg.solve(kkt,rhs)
        generator = np.zeros((10,10))
        generator[:6] = solution[:6]
        generator[6:9,:6] = b.T/np.array(parts.inductance_h)[:,None]
        generator[6:9,6:9] = -np.diag(np.array(parts.winding_ohm)/parts.inductance_h)
        # Encode exact derivative identities of the fixed ideal ON topology.
        # KKT roundoff can otherwise put ~1e-16 coefficients in a mathematically
        # zero row and manufacture a negative low-side gap at its later release.
        # This changes NO stored voltage: a nonzero entry residual stays nonzero.
        # All capacitors remain in the KKT; only redundant solved identities are
        # written exactly, not inferred from a numeric smallness threshold.
        for k, enabled in enumerate(start.gates.low):
            if enabled:
                generator[2+k,:]=0.
        if start.gates.high[0]:
            generator[0,:]=0.  # da1/dt=dVin/dt=0 for constant Vin
        if start.gates.high[1]:
            generator[1,:]=generator[0,:]  # d(a1-a2)/dt=0
        if start.gates.high[2]:
            generator[4,:]=generator[1,:]  # d(a2-x3)/dt=0
        generator.setflags(write=False)
        self.generator = generator

    def at(self, time_s: float) -> Snapshot:
        if not isfinite(time_s) or time_s < self.start.time_s:
            raise ValueError("finite forward time required")
        if time_s == self.start.time_s:
            return self.start
        y = expm(self.generator*(time_s-self.start.time_s)) @ np.r_[self.start.voltage_v,self.start.current_a,1.]
        if not np.all(np.isfinite(y)):
            raise ArithmeticError("nonfinite affine continuation")
        return replace(self.start,time_s=time_s,voltage_v=tuple(y[:6]),current_a=tuple(y[6:9]))

    def integrated_coordinates(self, time_s: float) -> np.ndarray:
        """Integrals of six node voltages and three currents from entry.

        Augmented matrix exponential; no inverse of potentially singular A,
        no sampled quadrature or assumption that Vo is constant. Same pre-event
        continuation limitation as at(); an integral is not a path certificate.
        """
        if not isfinite(time_s) or time_s < self.start.time_s:
            raise ValueError("finite forward time required")
        augmented=np.zeros((19,19))
        augmented[:10,:10]=self.generator
        augmented[10:,:9]=np.eye(9)
        initial=np.r_[self.start.voltage_v,self.start.current_a,1.,np.zeros(9)]
        result=expm(augmented*(time_s-self.start.time_s))@initial
        if not np.all(np.isfinite(result)):
            raise ArithmeticError("nonfinite coordinate integral")
        return result[10:]


@dataclass(frozen=True)
class ScanReport:
    status: str
    candidates: tuple[str,...]
    windows: tuple[EventWindow,...]
    sampled_until_s: float
    scope: str = "CONDITIONAL_SAMPLED_SCREEN_ONLY; no gate action or first-root certificate"


def scan_commutation(flow: LocalFlow, reverse: ReverseModel, *, end_s: float,
                     intervals: int, voltage_settings: RootSettings,
                     current_settings: RootSettings, entry_direction=None) -> ScanReport:
    """Watch target Vds, ALL OFF reverse gaps, ALL current-sign boundaries.

    All guards must start strictly interior beyond their numerical tolerance.
    Optional D11 entry_direction admits only locally inward exact-zero reverse
    gaps in the P25 single-module branch. Other entry roots remain unresolved.
    No external events: ConstantPorts/Vin define the entire supplied interval.
    """
    target = commutation_target(flow.mode)
    if not isinstance(reverse,ReverseModel):
        raise ValueError("explicit reverse surrogate required")
    if not isfinite(end_s) or end_s <= flow.start.time_s or type(intervals) is not int or intervals<1:
        raise ValueError("explicit finite forward horizon and positive sample count required")
    watches = [Quantity("target."+target,"V",lambda s:s.switch_voltage(target))]
    for name,on,drop in zip(SWITCHES,(*flow.start.gates.high,*flow.start.gates.low),reverse.drop_v):
        if not on:
            watches.append(Quantity("reverse."+name,"V",lambda s,n=name,d=drop:s.switch_voltage(n)+d))
    signs = current_signs(flow.mode)
    for k,sign in enumerate(signs):
        watches.append(Quantity(f"domain.iL{k+1}","A",lambda s,k=k,sign=sign:sign*s.current_a[k]))
    released=set()
    if entry_direction is not None:
        from .p25_entry_direction import classify_entry
        if (entry_direction.voltage_v != voltage_settings.value_tolerance or
                entry_direction.current_a != current_settings.value_tolerance):
            raise ValueError("entry and scan value tolerances must match")
        report=classify_entry(flow,reverse,entry_direction)
        if report.blockers:
            return ScanReport("ENTRY_DIRECTION_BLOCKED",report.blockers,(),flow.start.time_s)
        released=set(report.release_names)
    for watch in watches:
        tol = voltage_settings.value_tolerance if watch.unit=="V" else current_settings.value_tolerance
        g=watch.evaluate(flow.start)
        if g < -tol:
            return ScanReport("ENTRY_OUTSIDE_DOMAIN",(watch.name,),(),flow.start.time_s)
    entry=tuple(w.name for w in watches if w.name not in released and w.evaluate(flow.start)<=
                (voltage_settings.value_tolerance if w.unit=="V" else current_settings.value_tolerance))
    if entry:
        return ScanReport("ENTRY_BOUNDARY_UNRESOLVED",entry,(),flow.start.time_s)
    if paper_mode_violations(flow.start,flow.mode,tolerance_a=current_settings.value_tolerance):
        raise ValueError("entry mode-sign mismatch")
    left=flow.start
    for t in np.linspace(flow.start.time_s,end_s,intervals+1)[1:]:
        right=flow.at(float(t)); windows=[]
        # A locally inward gap must produce a positive sample before it can
        # be armed for return. Never silently skip an unseen excursion.
        unresolved=tuple(w.name for w in watches if w.name in released and w.evaluate(right)<=0)
        if unresolved:
            return ScanReport("ENTRY_RELEASE_NOT_RESOLVED_ON_GRID",unresolved,(),float(t))
        for w in watches:
            if w.evaluate(left)>0 and w.evaluate(right)<=0:
                root=locate_downward(w,flow.at,left_s=left.time_s,right_s=right.time_s,
                    settings=voltage_settings if w.unit=="V" else current_settings)
                windows.append(EventWindow.from_root(root))
        if windows:
            ordering=order_windows(tuple(windows))
            return ScanReport(ordering.status,ordering.possible_first,tuple(windows),float(t))
        released.clear()
        left=right
    return ScanReport("NO_DOWNWARD_BRACKET_OBSERVED",(),(),end_s)
