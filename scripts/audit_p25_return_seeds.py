"""D34: return-direction initial-value diagnostics, not parameter fitting.

Run: python3 -m scripts.audit_p25_return_seeds
Only stdout JSON. Physical/control context is shared unchanged with D29.
"""
import json
from scripts.audit_p25_synthetic_seeds import make_synthetic_context
from scb_ivr.p25_shooting_contract import SectionSeed
from scb_ivr.p25_section_necessity import section_return_necessity
from scb_ivr.p25_seed_evaluation import evaluate_seed
from scb_ivr.p25_local_flow import LocalFlow


def run_return_audit(intervals=200, down_horizon_s=1.):
    contract, options = make_synthetic_context(intervals)
    options["stage_horizons_s"] = (down_horizon_s, *options["stage_horizons_s"][1:])
    s = contract.anchor.last_event
    parts = contract.model.components
    ton = contract.model.control.on_time_s[0]
    # First-order entry slope is a seed SCALE only, not an integrated peak.
    rise_scale = ton*(s.voltage_v[2]-s.voltage_v[5])/parts.inductance_h[0]
    if rise_scale <= 0:
        raise ValueError("this diagnostic requires a positive entry-slope scale")
    cases = [(f"entry_rise_scale_x{factor}", -factor*rise_scale) for factor in (.25,.5,1.)]
    cases += [("negative_target_scale_not_claimed_turnon_current",
               -s.boundary.alpha*contract.anchor.peaks[0].reference.amperes)]
    rows = []
    for label, current in cases:
        seed = SectionSeed(4.,2.,1.,(current,2.,3.))
        initial = contract.make_candidate(seed)
        admission = section_return_necessity(initial, current_margin_a=1e-8)
        result = evaluate_seed(contract, seed, **options)
        last = result.attempt.steps[-1].outcome
        # Diagnostic pre-event continuation is named as such, never accepted.
        flow = LocalFlow(initial.last_event, parts, "M1", contract.ports, voltage_tolerance_v=1e-8)
        at_off = flow.at(initial.last_event.time_s+ton)
        rows.append(dict(case=label,seed=(4.,2.,1.,current,2.,3.),
            direction=admission.status,
            failed_mode=result.attempt.failed_mode,last_action=last.status,reason=last.reason,
            scan_status=last.scan.status, sampled_until_s=last.scan.sampled_until_s,
            events=last.scan.candidates,
            windows=[dict(event=w.name,earliest_s=w.earliest_s,latest_s=w.latest_s) for w in last.scan.windows],
            accepted_modes=[step.mode for step in result.attempt.steps if step.outcome.memory is not None],
            nominal_high_off_i1_continuation_a=float(at_off.current_a[0]),
            state_return=None if result.state_return is None else result.state_return.state_returns))
    return dict(scope="SYNTHETIC_RETURN_DIRECTION_DIAGNOSTIC_NOT_PAPER_REPRODUCTION",
                intervals=intervals,down_horizon_s=down_horizon_s,
                entry_rise_scale_a=rise_scale,cases=rows)


if __name__ == "__main__":
    print(json.dumps(run_return_audit(),indent=2))
