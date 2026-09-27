"""Bounded 3x3 L/dead-time sensitivity, with independent branch metering.

Rows are historical inductance anchors; columns are 0.5/1/2 times the prior
2.15 ns reference (not sourced driver limits). All candidates are re-solved.
No failed gate may be replaced by a favorable number or change to the load.
"""
from __future__ import annotations
import json
import sys
from dataclasses import asdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent/'A53_lphase_zvs_load_tradeoff'))
import a53_solve as S
from asymmetric_ron_dynamics import asymmetric_ron_context, build_epc2067_boundary
from audit_accepted_orbit import metered_orbit


def main():
    out = HERE/'joint_local_grid.json'
    if out.exists():
        raise RuntimeError('Existing experiment must not be overwritten; archive or resume explicitly')
    baseline = json.loads((HERE/'asymmetric_baseline_points.json').read_text())['points']
    nominal = json.loads((HERE/'asymmetric_nominal_smoke.json').read_text())
    refined = json.loads((HERE/'critical_boundary_result.json').read_text())['refinement'][0]
    # Extract the saved nominal state without imposing a new capacitor ladder.
    nominal_seed = nominal.get('z_star', nominal.get('solve', {}).get('z_star'))
    if nominal_seed is None:
        raise RuntimeError('Nominal checkpoint has no z_star; inspect its schema')
    anchors = [('new_passing', refined['phase_inductance_h'], refined['z_star']),
               ('old_critical', baseline['critical']['phase_inductance_h'], baseline['critical']['z_star']),
               ('nominal', 1.4666667e-9, nominal_seed)]
    result = dict(classification='LOCAL_TWO_VARIABLE_SENSITIVITY_NOT_OPTIMUM',
        paper_reproduction=False, controller='A51 fixed PWM windows and zero-voltage admission surrogate',
        load_resistance_ohm=0.004, nominal_load_power_w=250.,
        reference_dead_time_s=2.15e-9, deadtime_factors=[1., .5, 2.],
        fixed_point_tolerance=1e-6, current_screen_a=250.,
        coarse_step_s=62.5e-12, sub_step_s=5e-12, probes=[])
    def save():
        out.write_text(json.dumps(result, indent=2, default=str)+'\n')
    save()
    for name, inductance, seed in anchors:
        for factor in (1., .5, 2.):
            b = build_epc2067_boundary(phase_inductance_h=inductance, dead_time_s=2.15e-9*factor)
            r = dict(label=f'{name}_dt_x{factor:g}', phase_inductance_h=inductance,
                dead_time_s=b.dead_time_s, seed_source=name, compared_to=f'{name}_dt_x1',
                full_boundary=asdict(b), coarse_step_s=62.5e-12, sub_step_s=5e-12)
            try:
                with asymmetric_ron_context():
                    solved = S.solve_fixed_point(b, np.array(seed), tolerance=1e-6,
                        max_iterations=30, coarse_step_s=62.5e-12, sub_step_s=5e-12)
                r.update(converged=solved['converged'], stalled_reason=solved['stalled_reason'],
                    relative_residual=solved['final_relative_residual'],
                    solver_probe_safety=solved['safety'], history=solved['history'],
                    z_star=solved['z_star'].tolist())
                if not solved['converged']:
                    r['first_failure']='periodic_closure'
                else:
                    metrics = metered_orbit(r)
                    r['metrics']=metrics
                    high=all(metrics['natural_zvs_flags'])
                    low=all(v['natural'] for v in metrics['low_side_turn_on_verdicts'])
                    r['all_eight_zvs']=bool(high and low)
                    r['current_screen_pass']=metrics['maximum_abs_phase_current_a']<=250.
                    r['rated_power_relative_error']=metrics['actual_load_power_w']/250.-1
                    r['voltage_relative_error']=metrics['average_output_v']-1.
                    r['first_failure']=('phase_current_screen' if not r['current_screen_pass'] else
                         'high_side_zvs' if not high else 'low_side_zvs' if not low else None)
                    # Absolute losses across different power outputs are not efficiency rankings.
                    r['eligible_for_rated_power_optimization']=False
            except (RuntimeError, ValueError, np.linalg.LinAlgError) as error:
                r.update(first_failure='solver_exception_or_current_screen', error=str(error))
            result['probes'].append(r)
            save()
            metrics=r.get('metrics',{})
            print(json.dumps(dict(label=r['label'], first_failure=r['first_failure'],
                flags=metrics.get('natural_zvs_flags'), power_w=metrics.get('actual_load_power_w'),
                loss_w=metrics.get('actual_branch_channel_loss_w'))), flush=True)
    result['status']='LOCAL_GRID_COMPLETED_NO_OPTIMUM_CLAIM'
    save()


if __name__=='__main__':
    main()
