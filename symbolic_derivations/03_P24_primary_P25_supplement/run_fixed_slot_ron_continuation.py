"""Continue the fixed-slot candidate while switch Ron is reduced.

Each step scans a common J, enforces measured 5-10%, and re-solves all states.
Ron scales are counterfactual sensitivity profiles, not paper component data.
"""
import argparse,ast,json,subprocess,sys
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring

HERE=Path(__file__).resolve().parent;SCALE=np.r_[np.full(7,12.),np.full(4,125.)]
BASE_RON=model.RON.copy()
def state(path):
    line=[x for x in path.read_text().splitlines() if x.startswith('retained state ')][-1]
    return np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
def main():
    p=argparse.ArgumentParser();p.add_argument('--seed-log',type=Path,required=True);p.add_argument('--inductance-nh',type=float,required=True)
    p.add_argument('--initial-j-a',type=float,required=True);p.add_argument('--start-scale',type=float,required=True)
    p.add_argument('--stop-scale',type=float,required=True);p.add_argument('--step-scale',type=float,default=.05)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--iterations',type=int,default=5)
    p.add_argument('--max-node-return-mv',type=float,default=.3)
    p.add_argument('--max-current-return-a',type=float,default=.01)
    args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True);seed=args.seed_log;Jprev=args.initial_j_a;rows=[]
    for rs in np.arange(args.start_scale,args.stop_scale-args.step_scale/2,-args.step_scale):
        z=state(seed);model.RON=BASE_RON*rs;model.L=args.inductance_nh*1e-9;candidates=[]
        for J in np.arange(Jprev-.5,Jprev+.5001,.01):
            h,end,start=ring(z,di3=0.,origin=50e-9,max_handoffs=4,negative_target=float(J),tolerances=dict(rtol=1e-9,atol=1e-9))
            if len(h)==4 and not any('failure' in r for r in h):
                fr=[J/r['peak_a'] for r in h]
                if all(.0501<=x<=.0999 for x in fr):candidates.append((float(np.linalg.norm((end-start)/SCALE)),float(J)))
        if not candidates:
            row=dict(ron_scale=float(rs),status='STOP no strict full-ring J bridge',seed_log=str(seed));rows.append(row);print(json.dumps(row),flush=True);break
        _,J=min(candidates);out=args.output_dir/f'Ron{rs:.2f}_J{J:.3f}.txt'
        cmd=[sys.executable,str(HERE/'constrained_fixed_point_direction.py'),'--start-log',str(seed),'--iterations',str(args.iterations),
          '--inductance-nh',str(args.inductance_nh),'--negative-target-a',str(J),'--ron-scale',str(rs),
          '--trust-scale','.1','--max-node-return-mv','5.23','--node-planning-safety-mv','1.5']
        run=subprocess.run(cmd,text=True,capture_output=True);out.write_text(run.stdout+run.stderr)
        if run.returncode or 'retained state ' not in run.stdout:
            row=dict(ron_scale=float(rs),J_a=J,status='STOP optimizer error',log=str(out));rows.append(row);print(json.dumps(row),flush=True);break
        zr=state(out);model.RON=BASE_RON*rs;metrics={};h,end,start=ring(zr,di3=0.,origin=50e-9,max_handoffs=4,
          negative_target=J,metrics=metrics,tolerances=dict(rtol=1e-10,atol=1e-10))
        complete=len(h)==4 and not any('failure' in r for r in h);fr=[J/r['peak_a'] for r in h] if complete else []
        maxnode=float(np.max(abs((end-start)[:7]))*1e3) if complete else None
        maxcurrent=float(np.max(abs((end-start)[7:]))) if complete else None
        strict=complete and all(.05<=x<=.10 for x in fr) and maxnode<=args.max_node_return_mv and maxcurrent<=args.max_current_return_a
        row=dict(ron_scale=float(rs),J_a=J,status=('retained' if strict else 'STOP final strict/return check'),
          fraction_pct_range=([100*min(fr),100*max(fr)] if fr else None),
          power_w=(float(metrics['charge_a_s'].sum()/metrics['elapsed_s']) if complete else None),
          max_node_return_mv=maxnode,max_current_return_a=maxcurrent,
          log=str(out),seed_log=str(seed))
        rows.append(row);print(json.dumps(row),flush=True)
        if not strict:break
        seed=out;Jprev=J
    (args.output_dir/'manifest.jsonl').write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
    print('Ron continuation is a counterfactual sensitivity test, not a paper reproduction.',flush=True)
if __name__=='__main__':main()
