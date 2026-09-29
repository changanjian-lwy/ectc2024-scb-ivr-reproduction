"""D37: same-path M4/M5 current budget; no seed or control modification."""
import json
from dataclasses import asdict
from scripts.audit_p25_synthetic_seeds import make_synthetic_context
from scripts.audit_p25_voltage_seed_grid import snapshot_row
from scb_ivr.p25_shooting_contract import SectionSeed
from scb_ivr.p25_seed_evaluation import evaluate_seed
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_commutation_charge import commutation_charge
from scb_ivr.p25_residual_charge_bound import residual_charge_bound


def run_negative_budget_audit():
    contract, options = make_synthetic_context(400)
    options["stage_horizons_s"] = (10.,10.,10.,10.)
    parts = contract.model.components
    cases = []
    for x in (3.,4.):
        result = evaluate_seed(contract,SectionSeed(4.,x,.5,(-.0025,2.,3.)),**options)
        stages = []
        for step in result.attempt.steps:
            if step.mode not in ("M4","M5"):
                continue
            start = step.before.last_event
            accepted = step.outcome.memory is not None
            end_s = (step.outcome.memory.last_event.time_s if accepted else
                     next(w.latest_s for w in step.outcome.scan.windows if w.name in step.outcome.scan.candidates))
            flow = LocalFlow(start,parts,step.mode,contract.ports,voltage_tolerance_v=1e-8)
            end = flow.at(end_s)
            z = flow.integrated_coordinates(end_s)
            initial_flux = parts.inductance_h[0]*start.current_a[0]
            actual_flux = parts.inductance_h[0]*end.current_a[0]
            winding_flux = parts.winding_ohm[0]*z[6]
            row = dict(mode=step.mode,coverage="ACCEPTED_SEGMENT" if accepted else "UNACCEPTED_DIAGNOSTIC_TO_ROOT",
                start=snapshot_row(start),end=snapshot_row(end),negative_target_a=step.before.latched_target_a,
                initial_L1i1_vs=float(initial_flux),integral_Vo_vs=float(z[5]),
                integral_x1_vs=float(z[2]),integral_R1i1_vs=float(winding_flux),
                final_L1i1_vs=float(actual_flux),
                flux_balance_residual_vs=float(actual_flux-initial_flux-z[2]+z[5]+winding_flux))
            if step.mode=="M4":
                if parts.winding_ohm[1]!=0 or start.voltage_v[3]!=0:
                    raise ValueError("target-flux formula requires exact phase-2 zero R/x2")
                row["required_output_flux_for_negative_target_vs"] = float(
                    parts.inductance_h[1]*(start.current_a[1]-step.before.latched_target_a))
            else:
                row["charge"] = asdict(commutation_charge(flow,end_s))
                row["conditional_bound"] = asdict(residual_charge_bound(start,parts,step.mode,contract.ports,
                                                                       charge_margin_c=1e-10))
                row["entry_output_derivative_v_s"] = float((sum(start.current_a)-contract.ports.load_current_a)/parts.output_f)
            stages.append(row)
        cases.append(dict(initial_x1_v=x,failed_mode=result.attempt.failed_mode,stages=stages))
    return dict(scope="UNCHANGED_D36_SYNTHETIC_SEEDS_SAME_PATH_BUDGET",cases=cases)


if __name__ == "__main__":
    print(json.dumps(run_negative_budget_audit(),indent=2))
