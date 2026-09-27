"""Local continuation bracket for A55; not an optimization or paper match.

Keep 2.15 ns dead time fixed; re-solve each candidate with asymmetric Ron.
An unconverged/unsafe point never updates the ZVS bracket. Save every probe.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "A53_lphase_zvs_load_tradeoff"))
import a53_solve as S
from asymmetric_ron_dynamics import asymmetric_ron_context, build_epc2067_boundary
from path_resolved_period import evaluate_period_map_with_paths


def evaluate(label, inductance, seed, coarse=62.5e-12, sub=5e-12):
    b = build_epc2067_boundary(phase_inductance_h=inductance)
    record = dict(label=label, phase_inductance_h=inductance,
                  dead_time_s=b.dead_time_s, coarse_step_s=coarse, sub_step_s=sub)
    try:
        with asymmetric_ron_context():
            solved = S.solve_fixed_point(b, np.array(seed), coarse_step_s=coarse,
                                        sub_step_s=sub, max_iterations=30)
            p, integrals, loss = evaluate_period_map_with_paths(
                b, solved['z_star'], coarse_step_s=coarse, sub_step_s=sub)
        # Rollback-corrected accepted path, excluding provisional probes.
        current = np.array([sample[1] for sample in p.monitor.path_samples])
        record.update(
            converged=solved['converged'],
            relative_residual=solved['final_relative_residual'],
            stalled_reason=solved['stalled_reason'],
            natural_zvs_flags=list(p.natural_zvs_flags),
            turn_on_verdicts=solved['final_turn_on_verdicts'],
            final_orbit_phase_min_a=current.min(axis=0).tolist(),
            final_orbit_phase_max_a=current.max(axis=0).tolist(),
            final_orbit_peak_abs_a=float(np.max(np.abs(current))),
            all_solver_probes_peak_abs_a=solved['safety']['maximum_abs_phase_current_a'],
            solver_current_screen_pass=solved['safety']['within_limit'],
            inherited_orbit_metrics=solved['final_orbit_metrics'],
            inherited_power_metric_note='mean(Vout)^2/R from legacy monitor; not exact mean(Vout^2)/R',
            channel_loss_w=loss.modeled_loss_w,
            dead_time_i2dt_a2s=list(integrals.dead_time_a2s),
            high_side_i2dt_a2s=list(integrals.high_side_a2s),
            low_side_i2dt_a2s=list(integrals.low_side_a2s),
            complete_loss=False,
            z_star=solved['z_star'].tolist(),
            iteration_history=solved['history'])
        record['eligible_for_bracket'] = bool(solved['converged'] and solved['safety']['within_limit'])
        record['all_four_zvs'] = bool(all(p.natural_zvs_flags))
    except (RuntimeError, ValueError, np.linalg.LinAlgError) as error:
        record.update(eligible_for_bracket=False, error=str(error))
    print(json.dumps({k: record[k] for k in ('label', 'phase_inductance_h',
          'eligible_for_bracket', 'natural_zvs_flags', 'relative_residual') if k in record}), flush=True)
    return record


def main():
    prior = json.loads((HERE / 'asymmetric_baseline_points.json').read_text())['points']
    result = dict(classification='LOCAL_ZVS_BOUNDARY_SENSITIVITY_ONLY',
                  controls='only L changes in bracket; dead time 2.15 ns; fixed 4 mOhm load',
                  not_paper_reproduction=True, not_joint_optimization=True, probes=[])
    out = HERE / 'critical_boundary_result.json'
    def save():
        out.write_text(json.dumps(result, indent=2) + '\n')
    for key in ('margin', 'critical'):
        r = evaluate('endpoint_' + key, prior[key]['phase_inductance_h'], prior[key]['z_star'])
        result['probes'].append(r)
        save()
    lo, hi = result['probes']
    if not (lo['eligible_for_bracket'] and hi['eligible_for_bracket']
            and lo['all_four_zvs'] and not hi['all_four_zvs']):
        result['status'] = 'ENDPOINT_GATE_FAILED'
        save()
        return
    for i in range(7):
        mid = (lo['phase_inductance_h'] + hi['phase_inductance_h']) / 2
        r = evaluate(f'bisect_{i+1}', mid, lo['z_star'])
        result['probes'].append(r)
        if not r['eligible_for_bracket']:
            result['status'] = 'UNRESOLVED_NUMERICAL_OR_CURRENT_GATE'
            save()
            return
        if r['all_four_zvs']:
            lo = r
        else:
            hi = r
        result['bracket_h'] = [lo['phase_inductance_h'], hi['phase_inductance_h']]
        save()
    # Re-solve BOTH endpoints with finer steps, not merely replay old states.
    result['refinement'] = []
    for endpoint in (lo, hi):
        r = evaluate('fine_' + endpoint['label'], endpoint['phase_inductance_h'],
                     endpoint['z_star'], coarse=31.25e-12, sub=2.5e-12)
        result['refinement'].append(r)
        save()
    a, b = result['refinement']
    result['status'] = ('BRACKET_RETAINED_ON_REFINEMENT' if
        a['eligible_for_bracket'] and b['eligible_for_bracket'] and
        a['all_four_zvs'] and not b['all_four_zvs'] else
        'BRACKET_STEP_SENSITIVE_DO_NOT_CLAIM_THRESHOLD')
    save()


if __name__ == '__main__':
    main()
