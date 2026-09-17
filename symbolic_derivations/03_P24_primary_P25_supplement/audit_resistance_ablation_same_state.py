"""One-variable resistance ablation at the same state/control.

Counterfactual scales diagnose sensitivity only. A changed profile must later
receive its own periodic-state solve before quantitative comparison.
"""
import argparse,ast,json
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring

PROFILES=[('baseline',1.,1.),('zero_winding_R_only',1.,0.),
          ('half_switch_Ron',.5,1.),('near_ideal_switch_Ron',1e-4,1.)]
def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path)
    p.add_argument('--inductance-nh',type=float,required=True);p.add_argument('--negative-target-a',type=float,required=True);args=p.parse_args()
    line=[x for x in args.candidate_log.read_text().splitlines() if x.startswith('retained state ')][-1]
    z=np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
    base_ron=model.RON.copy();base_rind=model.RIND;model.L=args.inductance_nh*1e-9
    for name,ron_scale,rind_scale in PROFILES:
        model.RON=base_ron*ron_scale;model.RIND=base_rind*rind_scale;metrics={}
        h,end,start=ring(z,di3=0.,origin=50e-9,max_handoffs=4,negative_target=args.negative_target_a,
          metrics=metrics,tolerances=dict(rtol=1e-9,atol=1e-9))
        complete=len(h)==4 and not any('failure' in r for r in h)
        row=dict(profile=name,ron_scale=ron_scale,rind_scale=rind_scale,complete_ring=complete,
          completed_handoffs=sum('failure' not in r for r in h),
          earliest_failure=next((r for r in h if 'failure' in r),None))
        if complete:row.update(power_w=float(metrics['charge_a_s'].sum()/metrics['elapsed_s']),
          peak_range_a=[min(r['peak_a'] for r in h),max(r['peak_a'] for r in h)],
          max_node_return_mv=float(np.max(abs((end-start)[:7]))*1e3),
          max_current_return_a=float(np.max(abs((end-start)[7:]))))
        print(json.dumps(row),flush=True)
    model.RON=base_ron;model.RIND=base_rind
    print('Only resistance changed; same old state/control means nonbaseline rows are sensitivity probes, not fitted working points.')

if __name__=='__main__':main()
