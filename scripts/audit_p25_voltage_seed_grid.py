"""D36: bounded 3x2 INITIAL-voltage grid; no device/control fitting.

python3 -m scripts.audit_p25_voltage_seed_grid
Every case restarts from its declared seed; output JSON only.
"""
import json
from dataclasses import asdict
from scripts.audit_p25_synthetic_seeds import make_synthetic_context
from scb_ivr.p25_shooting_contract import SectionSeed
from scb_ivr.p25_section_necessity import section_return_necessity
from scb_ivr.p25_seed_evaluation import evaluate_seed
from scb_ivr.p25_local_flow import LocalFlow
from scb_ivr.p25_down_commutation_charge import down_commutation_charge


def snapshot_row(s):
    return dict(time_s=s.time_s, node_order=("a1","a2","x1","x2","x3","out"),
                node_voltage_v=tuple(float(v) for v in s.voltage_v),
                inductor_current_a=tuple(float(i) for i in s.current_a),gates=asdict(s.gates))


def run_voltage_grid(intervals=400):
    contract, options = make_synthetic_context(intervals)
    options["stage_horizons_s"] = (10.,10.,10.,10.)
    rows = []
    for vo in (1.,.5):
        for x1 in (2.,3.,4.):
            seed = SectionSeed(4.,x1,vo,(-.0025,2.,3.))
            initial = contract.make_candidate(seed)
            direction = section_return_necessity(initial,current_margin_a=1e-8)
            result = evaluate_seed(contract,seed,**options)
            last = result.attempt.steps[-1]
            scan = last.outcome.scan
            windows = [w for w in scan.windows if w.name in scan.candidates]
            root = None
            if len(windows)==1:
                flow = LocalFlow(last.before.last_event,contract.model.components,last.mode,
                                 contract.ports,voltage_tolerance_v=1e-8)
                root = snapshot_row(flow.at(windows[0].latest_s))
            down = result.attempt.steps[1]
            flow2 = LocalFlow(down.before.last_event,contract.model.components,"M2",contract.ports,
                              voltage_tolerance_v=1e-8)
            end2 = (down.outcome.memory.last_event.time_s if down.outcome.memory is not None
                    else next(w.latest_s for w in down.outcome.scan.windows
                              if w.name in down.outcome.scan.candidates))
            rows.append(dict(seed=asdict(seed),direction=direction.status,
                accepted_modes=[step.mode for step in result.attempt.steps if step.outcome.memory is not None],
                failed_mode=result.attempt.failed_mode,last_action=last.outcome.status,
                events=scan.candidates,
                event_windows=[asdict(w) for w in windows],
                last_accepted=snapshot_row(result.attempt.last_accepted.last_event),
                unaccepted_competing_endpoint=root,
                m2_charge=asdict(down_commutation_charge(flow2,end2)),
                state_return=None if result.state_return is None else result.state_return.state_returns))
    return dict(scope="SYNTHETIC_INITIAL_VOLTAGE_GRID_NOT_PAPER_REPRODUCTION",intervals=intervals,
                frozen_model=asdict(contract.model),frozen_ports=asdict(contract.ports),cases=rows)


if __name__ == "__main__":
    print(json.dumps(run_voltage_grid(),indent=2))
