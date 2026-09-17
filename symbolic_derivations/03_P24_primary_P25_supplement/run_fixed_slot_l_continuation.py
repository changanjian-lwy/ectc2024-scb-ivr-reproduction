"""Continue a feasible fixed-slot state while L is reduced in small steps.

At each L, a narrow common-J grid is tested first. A state optimizer runs only
from a full-ring-admissible point. J is a diagnostic P25-supplement control,
not paper-provided data. The process stops at the first lost feasible bridge.
"""
import argparse,ast,json,subprocess,sys
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring

HERE=Path(__file__).resolve().parent;LCRIT=1.4666666666666668
SCALE=np.r_[np.full(7,12.),np.full(4,125.)]
def load_state(path):
    line=[x for x in path.read_text().splitlines() if x.startswith('retained state ')][-1]
    return np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))

def main():
    p=argparse.ArgumentParser();p.add_argument('--seed-log',type=Path,required=True)
    p.add_argument('--initial-j-a',type=float,required=True);p.add_argument('--start-fraction',type=float,required=True)
    p.add_argument('--stop-fraction',type=float,required=True);p.add_argument('--step-fraction',type=float,default=.001)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--iterations',type=int,default=5)
    p.add_argument('--min-negative-fraction',type=float,default=.05)
    p.add_argument('--max-negative-fraction',type=float,default=.10)
    p.add_argument('--fraction-planning-margin',type=float,default=0.)
    args=p.parse_args()
    if not 0<args.min_negative_fraction<=args.max_negative_fraction: p.error('invalid fraction range')
    if args.fraction_planning_margin<0 or 2*args.fraction_planning_margin>=args.max_negative_fraction-args.min_negative_fraction:
        p.error('invalid fraction planning margin')
    args.output_dir.mkdir(parents=True,exist_ok=True);seedlog=args.seed_log;Jprev=args.initial_j_a
    fractions=np.arange(args.start_fraction,args.stop_fraction-args.step_fraction/2,-args.step_fraction)
    manifest=[]
    for frac in fractions:
        Lnh=LCRIT*frac;z=load_state(seedlog);model.L=Lnh*1e-9;candidates=[]
        for J in np.arange(Jprev-.3,Jprev+.3001,.01):
            h,end,start=ring(z,di3=0.,origin=50e-9,max_handoffs=4,negative_target=float(J),
                             tolerances=dict(rtol=1e-9,atol=1e-9))
            if len(h)==4 and not any('failure' in r for r in h):
                fractions_actual=[J/r['peak_a'] for r in h]
                if all(args.min_negative_fraction+args.fraction_planning_margin<=x<=args.max_negative_fraction-args.fraction_planning_margin for x in fractions_actual):
                    candidates.append((float(np.linalg.norm((end-start)/SCALE)),float(J)))
        if not candidates:
            row=dict(fraction=float(frac),inductance_nh=float(Lnh),status='STOP no full-ring common-J bridge',
                     seed_log=str(seedlog),searched_J_a=[Jprev-.3,Jprev+.3],
                     required_actual_fraction=[args.min_negative_fraction,args.max_negative_fraction]);manifest.append(row);print(json.dumps(row),flush=True);break
        _,J=min(candidates);out=args.output_dir/f'L{frac:.3f}_J{J:.3f}_continuation.txt'
        cmd=[sys.executable,str(HERE/'constrained_fixed_point_direction.py'),'--start-log',str(seedlog),
             '--iterations',str(args.iterations),'--inductance-nh',str(Lnh),'--negative-target-a',str(J),
             '--trust-scale','.1','--max-node-return-mv','5.23','--node-planning-safety-mv','1.5']
        run=subprocess.run(cmd,text=True,capture_output=True);out.write_text(run.stdout+run.stderr)
        if run.returncode or 'retained state ' not in run.stdout:
            row=dict(fraction=float(frac),inductance_nh=float(Lnh),J_a=J,status='STOP optimizer error',log=str(out));manifest.append(row);print(json.dumps(row),flush=True);break
        zr=load_state(out);h,end,start=ring(zr,di3=0.,origin=50e-9,max_handoffs=4,negative_target=J,
          tolerances=dict(rtol=1e-10,atol=1e-10));complete=len(h)==4 and not any('failure' in r for r in h)
        residual=(end-start);actual_pct=[100*J/r['peak_a'] for r in h]
        fraction_ok=all(args.min_negative_fraction<=x/100<=args.max_negative_fraction for x in actual_pct)
        accepted=complete and fraction_ok
        row=dict(fraction=float(frac),inductance_nh=float(Lnh),J_a=J,
          J_fraction_of_peak_pct_range=[min(actual_pct),max(actual_pct)],
          status=('retained' if accepted else ('STOP final fraction outside strict range' if complete else 'STOP retained state infeasible')),
          max_node_return_mv=float(np.max(abs(residual[:7]))*1e3),max_current_return_a=float(np.max(abs(residual[7:]))),
          normalized_return_norm=float(np.linalg.norm(residual/SCALE)),log=str(out),seed_log=str(seedlog))
        manifest.append(row);print(json.dumps(row),flush=True)
        if not accepted:break
        seedlog=out;Jprev=J
    name=f'manifest_{args.start_fraction:.3f}_to_{args.stop_fraction:.3f}.jsonl'
    (args.output_dir/name).write_text('\n'.join(json.dumps(x) for x in manifest)+'\n')
    print('No continuation point certifies startup, stability, target power, or paper reproduction.',flush=True)

if __name__=='__main__':main()
