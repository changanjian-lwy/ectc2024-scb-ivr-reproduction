"""D20: fixed-boundary six-coordinate SH1 section, not an optimizer.

Only declared-design peak control is admitted here. Measured-peak policies
need a declared observer/window and memory update before periodic shooting.
"""
from dataclasses import dataclass, replace
from math import isfinite
from .p25_control_memory import Memory, Stage, start_at_high_on
from .p25_local_flow import ConstantPorts
from .p25_periodic_section import ModelIdentity
from .p25_nodal_contract import SWITCHES


SEED_COORDINATES = (("a2","V"),("x1","V"),("out","V"),
                    ("iL1","A"),("iL2","A"),("iL3","A"))


@dataclass(frozen=True)
class SectionSeed:
    a2_v: float
    x1_v: float
    out_v: float
    current_a: tuple[float,float,float]

    def __post_init__(self):
        if not isinstance(self.current_a,tuple) or len(self.current_a)!=3:
            raise ValueError("three explicit phase currents required")
        if not all(isfinite(x) for x in (self.a2_v,self.x1_v,self.out_v,*self.current_a)):
            raise ValueError("finite six-coordinate candidate required")


@dataclass(frozen=True)
class ShootingContract:
    anchor: Memory
    model: ModelIdentity
    ports: ConstantPorts
    declaration: str

    def __post_init__(self):
        m=self.anchor; s=m.last_event; b=s.boundary
        if b.branch!="P25" or b.nP!=3 or b.nM!=1 or b.module!=1:
            raise ValueError("P25 native three-phase single module only")
        if b.output_boundary!="dynamic_Co_current_ports":
            raise ValueError("dynamic output boundary required")
        if self.ports.other_modules_current_a!=0:
            raise ValueError("no other-module injection in single-module shooting")
        if not self.declaration.strip():
            raise ValueError("explicit seed-search purpose and boundary declaration required")
        if m.phase!=1 or m.stage!=Stage.RISE or m.latched_target_a is not None:
            raise ValueError("fresh SH1 section required")
        if start_at_high_on(s,phase=1,peaks=m.peaks,policy=self.model.control)!=m:
            raise ValueError("invalid anchor memory or section time")
        if any(p is None or p.reference.basis!="declared_design_peak" for p in m.peaks):
            raise ValueError("all three fixed design peaks required; measured peaks need an observer")
        if self.model.reverse_model.kind!="ideal_zero_drop":
            raise ValueError("current cycle executor requires ideal-zero-drop branch")
        # Exact constraints define this coordinate chart, not a numerical
        # projection of a previously integrated state.
        if (s.voltage_v[0],s.voltage_v[3],s.voltage_v[4])!=(s.vin_v,0.,0.):
            raise ValueError("anchor must satisfy exact SH1/SL2/SL3 coordinate chart")

    def make_candidate(self, seed: SectionSeed) -> Memory:
        """Declare a new initial guess; NEVER use as an event-state reset."""
        if any(i<0 for i in seed.current_a[1:]):
            raise ValueError("non-active phase currents must be in the nonnegative entry domain")
        s=self.anchor.last_event
        candidate=replace(s,voltage_v=(s.vin_v,seed.a2_v,seed.x1_v,0.,0.,seed.out_v),
                          current_a=seed.current_a)
        result=start_at_high_on(candidate,phase=1,peaks=self.anchor.peaks,
                                policy=self.model.control)
        # Exact OFF voltage feasibility; no repair of an invalid seed.
        for name,on in zip(SWITCHES,(*candidate.gates.high,*candidate.gates.low)):
            if not on and candidate.switch_voltage(name)<0:
                raise ValueError("candidate violates an OFF reverse gap; no projection")
        return result

    def assert_frozen(self, candidate: Memory, model: ModelIdentity, ports: ConstantPorts):
        """Reject physical/control/port changes masquerading as seed search."""
        if model!=self.model or ports!=self.ports:
            raise ValueError("component, control, reverse or port boundary changed")
        a=self.anchor.last_event; s=candidate.last_event
        if (s.boundary,s.vin_v,s.run_id,s.clock_id,s.cycle,s.time_s)!=(
                a.boundary,a.vin_v,a.run_id,a.clock_id,a.cycle,a.time_s):
            raise ValueError("candidate changed frozen source/context coordinates")
        if candidate.peaks!=self.anchor.peaks:
            raise ValueError("fixed peak references may not be fitted to force closure")
        reconstructed=self.make_candidate(SectionSeed(s.voltage_v[1],s.voltage_v[2],
                                                       s.voltage_v[5],s.current_a))
        if reconstructed!=candidate:
            raise ValueError("candidate is outside the declared six-coordinate section")
