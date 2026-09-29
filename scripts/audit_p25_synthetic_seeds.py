"""D29: deterministic one-coordinate ±10% audit, NOT paper/device fitting.

Run from the project after installing the editable package:
python3 scripts/audit_p25_synthetic_seeds.py
Writes JSON to stdout only; never changes device/experimental files.
"""
import json
from scb_ivr.p25_control_memory import KnownPeak,Policy,start_at_high_on
from scb_ivr.p25_cycle_modes import cycle_mode
from scb_ivr.p25_entry_direction import DirectionTolerance
from scb_ivr.p25_event_guards import Snapshot
from scb_ivr.p25_local_flow import ConstantPorts
from scb_ivr.p25_native_events import NativeBoundary,PeakReference
from scb_ivr.p25_nodal_contract import Components
from scb_ivr.p25_periodic_section import ModelIdentity,ReturnTolerance
from scb_ivr.p25_reverse_contract import ReverseModel,Tolerances
from scb_ivr.p25_root_location import RootSettings
from scb_ivr.p25_seed_evaluation import evaluate_seed
from scb_ivr.p25_shooting_contract import ShootingContract,SectionSeed,SEED_COORDINATES


def make_synthetic_context(intervals=200):
    """Shared frozen D21/D29 fixture; callers must label new seed diagnostics."""
    parts=Components((1.,)*6,(0.,)*6,(17.,19.),23.,(2.,3.,4.),(0.,)*3,"D12 synthetic F/H/s")
    policy=Policy((.02,)*3,1e-8,1e-8,1e-9,True,"D12 ideal synthetic control")
    ports=ConstantPorts(1.,0.,"D12 synthetic constant current")
    reverse=ReverseModel("ideal_zero_drop",(0.,)*6,"declared ideal mathematical branch")
    boundary=NativeBoundary(3,1,1,"dynamic_Co_current_ports",.05)
    state=Snapshot(boundary,"D29 synthetic one-coordinate diagnostic","absolute",0,0.,12.,
                   (12.,4.,2.,0.,0.,1.),(20.,2.,3.),cycle_mode("M1").gates)
    peaks=tuple(KnownPeak(PeakReference(k,20.,"declared_design_peak","D21 synthetic fixed references"),0.)
                for k in (1,2,3))
    memory=start_at_high_on(state,phase=1,peaks=peaks,policy=policy)
    contract=ShootingContract(memory,ModelIdentity(parts,reverse,policy,"constant synthetic current"),
                              ports,"D29 only one initial coordinate varies, no device/control fitting")
    root=RootSettings(1e-9,1e-8,100,"sampled continuous local affine flow")
    options=dict(return_tolerance=ReturnTolerance(1e-8,1e-8,1e-9,0.),
                 stage_horizons_s=(1.,10.,10.,10.),intervals=intervals,
                 voltage_root=root,current_root=root,electrical=Tolerances(1e-8,1e-8,1e-8),
                 direction=DirectionTolerance(1e-8,1e-8,1e-10,1e-10))
    return contract, options


def run_audit(intervals=200):
    contract, options = make_synthetic_context(intervals)
    base=(4.,2.,1.,20.,2.,3.)
    cases=[("baseline",base)]
    for k,(name,unit) in enumerate(SEED_COORDINATES):
        for factor in (.9,1.1):
            z=list(base);z[k]*=factor
            cases.append((f"{name}_x{factor}",tuple(z)))
    rows=[]
    for label,z in cases:
        seed=SectionSeed(z[0],z[1],z[2],tuple(z[3:]))
        r=evaluate_seed(contract,seed,**options)
        last=r.attempt.steps[-1].outcome
        rows.append(dict(case=label,seed=z,status=r.status,failed_mode=r.attempt.failed_mode,
            last_action=last.status,events=last.scan.candidates,
            windows=[dict(event=w.name,earliest_s=w.earliest_s,latest_s=w.latest_s) for w in last.scan.windows],
            state_return=None if r.state_return is None else r.state_return.state_returns))
    return dict(scope="SYNTHETIC_INITIAL_STATE_DIAGNOSTIC_NOT_PAPER_REPRODUCTION",
                intervals=intervals,coordinates=SEED_COORDINATES,cases=rows)


if __name__=="__main__":
    print(json.dumps(run_audit(),indent=2))
