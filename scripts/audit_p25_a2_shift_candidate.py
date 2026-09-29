"""D38: derive one new initial a2 from a verified pre-SH2 affine offset.

No local reset; candidate restarts M1 with frozen components and control.
The offset symmetry ends when SH2 turns on. No full-period symmetry claimed.
"""
import json
from scripts.audit_p25_synthetic_seeds import make_synthetic_context
from scripts.audit_p25_voltage_seed_grid import snapshot_row
from scb_ivr.p25_shooting_contract import SectionSeed
from scb_ivr.p25_seed_evaluation import evaluate_seed
from scb_ivr.p25_local_flow import LocalFlow


def run_a2_shift_audit(intervals=400):
    contract, options = make_synthetic_context(intervals)
    options["stage_horizons_s"] = (10.,)*4
    baseline = evaluate_seed(contract,SectionSeed(4.,4.,.5,(-.0025,2.,3.)),**options)
    last = baseline.attempt.steps[-1]
    if last.mode!="M5" or last.outcome.scan.candidates!=("domain.iL1",):
        raise ValueError("D36 baseline failure changed")
    flows = [LocalFlow(s.before.last_event,contract.model.components,s.mode,contract.ports,
                       voltage_tolerance_v=1e-8) for s in baseline.attempt.steps]
    # dy = delta*e_a2 must remain constant before SH2-on.
    shift_rates = [float(abs(f.generator[:,1]).max()) for f in flows]
    if any(rate != 0. for rate in shift_rates):
        raise ValueError("a2-shift symmetry not exact in the stored affine generators")
    end = flows[-1].at(last.outcome.scan.windows[0].latest_s)
    lower = 4.+end.switch_voltage("SH2")
    upper = 4.+flows[-1].start.switch_voltage("SH2")
    candidate_a2 = (lower+upper)/2
    candidate = evaluate_seed(contract,SectionSeed(candidate_a2,4.,.5,(-.0025,2.,3.)),**options)
    rows=[]
    for step in candidate.attempt.steps:
        row=dict(mode=step.mode,status=step.outcome.status,events=step.outcome.scan.candidates,
                 before=snapshot_row(step.before.last_event),reason=step.outcome.reason,
                 accepted_after=None if step.outcome.memory is None else snapshot_row(step.outcome.memory.last_event))
        if step.outcome.memory is None and step.mode=="M6":
            flow=LocalFlow(step.before.last_event,contract.model.components,step.mode,contract.ports,
                           voltage_tolerance_v=1e-8)
            due=step.before.entered_at_s+contract.model.control.on_time_s[1]
            entry=step.before.last_event
            vl=entry.voltage_v[3]-entry.voltage_v[5]
            row["entry_inductor_voltage_v"]=float(vl)
            row["entry_current_derivative_a_s"]=float((vl-contract.model.components.winding_ohm[1]*entry.current_a[1])/
                                                       contract.model.components.inductance_h[1])
            row["entry_rise_direction"]= "POSITIVE" if row["entry_current_derivative_a_s"]>0 else "NONPOSITIVE"
            row["unaccepted_high_off_continuation"]=snapshot_row(flow.at(due))
        rows.append(row)
    return dict(scope="SYNTHETIC_ONE_INITIAL_COORDINATE_DERIVATION_NOT_PAPER_RESULT",
                intervals=intervals,baseline_a2_v=4.,pre_SH2_null_column_max=shift_rates,
                conditional_open_a2_window_v=(lower,upper),candidate_a2_v=candidate_a2,
                failed_mode=candidate.attempt.failed_mode,
                state_return=None if candidate.state_return is None else candidate.state_return.state_returns,
                stages=rows)


if __name__=="__main__":
    print(json.dumps(run_a2_shift_audit(),indent=2))
