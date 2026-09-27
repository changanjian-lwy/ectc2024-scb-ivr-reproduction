"""Refine the sampled all-ZVS point closest to rated power; no optimum claim."""
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run_joint_local_grid import S, asymmetric_ron_context, build_epc2067_boundary, metered_orbit


def main():
    source=json.loads((HERE/'joint_local_grid.json').read_text())
    if source.get('status')!='LOCAL_GRID_COMPLETED_NO_OPTIMUM_CLAIM':
        raise RuntimeError('Grid is incomplete')
    points=[p for p in source['probes'] if p.get('all_eight_zvs') and p.get('current_screen_pass')]
    result=dict(classification='SELECTED_GRID_POINT_STEP_REFINEMENT_NOT_OPTIMIZATION',
        selection='smallest absolute 250 W power error among converged all-eight-ZVS current-screen-passing sampled points',
        runs=[])
    out=HERE/'joint_refinement.json'
    if out.exists():
        raise RuntimeError('Do not overwrite prior refinement')
    def save():
        out.write_text(json.dumps(result,indent=2,default=str)+'\n')
    if not points:
        result['status']='NO_ELIGIBLE_GRID_POINT'
        save()
        return
    chosen=min(points,key=lambda p:abs(p['rated_power_relative_error']))
    result['source_label']=chosen['label']
    result['original_metrics']=chosen['metrics']
    seed=chosen['z_star']
    for coarse,sub in ((31.25e-12,2.5e-12),(15.625e-12,1.25e-12)):
        r=dict(label=chosen['label']+f'_step_{sub*1e12:g}ps',
            phase_inductance_h=chosen['phase_inductance_h'],dead_time_s=chosen['dead_time_s'],
            coarse_step_s=coarse,sub_step_s=sub)
        b=build_epc2067_boundary(phase_inductance_h=r['phase_inductance_h'],dead_time_s=r['dead_time_s'])
        try:
            with asymmetric_ron_context():
                s=S.solve_fixed_point(b,np.array(seed),coarse_step_s=coarse,
                    sub_step_s=sub,tolerance=1e-6,max_iterations=30)
            r.update(converged=s['converged'],relative_residual=s['final_relative_residual'],
                history=s['history'],safety=s['safety'],z_star=s['z_star'].tolist())
            if s['converged']:
                r['metrics']=metered_orbit(r)
                seed=r['z_star']
        except (RuntimeError, ValueError, np.linalg.LinAlgError) as e:
            r['error']=str(e)
        result['runs'].append(r)
        save()
        m=r.get('metrics',{})
        print(json.dumps(dict(label=r['label'],converged=r.get('converged'),
            flags=m.get('natural_zvs_flags'),power=m.get('actual_load_power_w'))),flush=True)
    result['status']='REFINEMENT_COMPLETED_CHECK_INDIVIDUAL_GATES'
    save()


if __name__=='__main__':
    main()
