"""D35: unchanged D34 small-negative seeds; diagnostic prefix, not accepted M2."""
import json
from dataclasses import asdict
from scripts.audit_p25_synthetic_seeds import make_synthetic_context
from scb_ivr.p25_shooting_contract import SectionSeed
from scb_ivr.p25_seed_evaluation import evaluate_seed
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_down_commutation_charge import down_commutation_charge


def run_down_charge_audit():
    contract, options = make_synthetic_context(400)
    options["stage_horizons_s"] = (10.,10.,10.,10.)
    rows = []
    for i1 in (-.0025,-.005):
        result = evaluate_seed(contract, SectionSeed(4.,2.,1.,(i1,2.,3.)), **options)
        last = result.attempt.steps[-1]
        if last.mode != "M2" or last.outcome.scan.candidates != ("domain.iL2",):
            raise ValueError("D34 failure changed; do not silently reuse old diagnostic boundary")
        end_s = last.outcome.scan.windows[0].latest_s
        flow = LocalFlow(last.before.last_event,contract.model.components,"M2",contract.ports,
                         voltage_tolerance_v=1e-8)
        rows.append(dict(initial_i1_a=i1,end_s=end_s,coverage="UNACCEPTED_M2_DIAGNOSTIC_TO_COMPETING_ROOT",
                         budget=asdict(down_commutation_charge(flow,end_s))))
    return dict(scope="SYNTHETIC_P25_THREE_PHASE_ONE_MODULE_NOT_PAPER_VALUES",cases=rows)


if __name__ == "__main__":
    print(json.dumps(run_down_charge_audit(),indent=2))
