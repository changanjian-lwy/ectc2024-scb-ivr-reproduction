"""Report where one fixed ring's output charge is transferred."""
import argparse,ast,json
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path)
    p.add_argument('--inductance-nh',type=float,required=True);p.add_argument('--negative-target-a',type=float,required=True)
    args=p.parse_args();line=next(x for x in args.candidate_log.read_text().splitlines() if x.startswith('retained state '))
    z=np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]));model.L=args.inductance_nh*1e-9
    metrics={};h,end,start=ring(z,di3=0.,origin=50e-9,max_handoffs=4,metrics=metrics,
      negative_target=args.negative_target_a,tolerances=dict(rtol=1e-10,atol=1e-10))
    if len(h)!=4 or any('failure' in r for r in h):raise RuntimeError(str(h[-1]))
    rows=[]
    for s in metrics['segments']:
        q=np.asarray(s['charge_a_ns']);rows.append(dict(s,total_charge_a_ns=float(q.sum()),
          output_average_contribution_a=float(q.sum()/(metrics['elapsed_s']*1e9))))
    print(json.dumps(dict(inductance_nh=args.inductance_nh,negative_target_a=args.negative_target_a,
      period_ns=metrics['elapsed_s']*1e9,phase_mean_current_a=(metrics['charge_a_s']/metrics['elapsed_s']).tolist(),
      total_mean_current_a=float(metrics['charge_a_s'].sum()/metrics['elapsed_s']),segments=rows),indent=2))

if __name__=='__main__':main()
