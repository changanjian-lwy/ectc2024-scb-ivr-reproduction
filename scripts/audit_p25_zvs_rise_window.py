"""D39: bound the D38 pre-SH2 window, rather than sampling more a2 seeds."""
import json
from dataclasses import asdict
from scripts.audit_p25_synthetic_seeds import make_synthetic_context
from scb_ivr.p25_shooting_contract import SectionSeed
from scb_ivr.p25_seed_evaluation import evaluate_seed
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_affine_envelope import affine_envelope


def run_rise_window_audit():
    contract, options=make_synthetic_context(400)
    options["stage_horizons_s"]=(10.,)*4
    result=evaluate_seed(contract,SectionSeed(4.,4.,.5,(-.0025,2.,3.)),**options)
    step=result.attempt.steps[-1]
    if step.mode!="M5" or step.outcome.scan.candidates!=("domain.iL1",):
        raise ValueError("baseline changed; rederive window")
    flow=LocalFlow(step.before.last_event,contract.model.components,"M5",contract.ports,
                   voltage_tolerance_v=1e-8)
    if any(flow.generator[:,1]!=0):
        raise ValueError("a2 shift no longer leaves M5 current/voltage flow invariant")
    end=step.outcome.scan.windows[0].latest_s
    b=affine_envelope(flow,end)
    p=contract.model.components
    max_vl=b.upper[3]-b.lower[5]
    max_rate=(max_vl-p.winding_ohm[1]*b.lower[7])/p.inductance_h[1]
    return dict(scope="D38_FROZEN_OTHER_COORDINATES_PRE_SH2_WINDOW_ONLY",
        inherited_first_event_scope=step.outcome.scan.scope,
        envelope=asdict(b),x2_upper_v=b.upper[3],output_lower_v=b.lower[5],
        inductor_voltage_upper_v=max_vl,current_derivative_upper_a_s=max_rate,
        rise_status="POSITIVE_ENTRY_RISE_EXCLUDED_ON_DECLARED_WINDOW" if max_rate<0 else "NOT_EXCLUDED")


if __name__=="__main__":print(json.dumps(run_rise_window_audit(),indent=2))
