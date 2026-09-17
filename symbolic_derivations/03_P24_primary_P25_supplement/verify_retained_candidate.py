"""Report candidate drift, power and two-ring failure without declaring success.

No paper acceptance tolerances are invented; observed quantities are reported.
The ideal 1 V sink measures converter current, not output regulation.
"""
import argparse
import ast
import json
from pathlib import Path
import numpy as np
from joint_predecessor_event_ring import ring
import finite_resistance_interval as interval_model

def main():
    p=argparse.ArgumentParser()
    p.add_argument('candidate_log',type=Path)
    p.add_argument('--inductance-nh',type=float)
    p.add_argument('--negative-target-a',type=float)
    p.add_argument('--long-handoffs',type=int,default=8)
    args=p.parse_args()
    if args.inductance_nh is not None:interval_model.L=args.inductance_nh*1e-9
    line=next(x for x in args.candidate_log.read_text().splitlines()
              if x.startswith('retained state '))
    z=np.array(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
    if z.shape!=(11,) or not np.all(np.isfinite(z)):
        raise ValueError('invalid full-state candidate')
    for tol in [1e-9,1e-10]:
        metrics={}
        h,end,start=ring(z,di3=0,origin=50e-9,metrics=metrics,
                         tolerances=dict(rtol=tol,atol=tol),window_extension_ns=5.,
                         negative_target=(11.25 if args.negative_target_a is None else args.negative_target_a))
        one_pass=len(h)==4 and not any('failure' in r for r in h)
        result=dict(candidate=str(args.candidate_log),tolerance=tol,
                    one_ring_admission=one_pass,one_ring_events=h,
                    node_return_v=(end-start)[:7].tolist(),
                    current_return_a=(end-start)[7:].tolist(),
                    integrated_duration_ns=metrics['elapsed_s']*1e9,
                    converter_mean_current_a=(metrics['charge_a_s']/metrics['elapsed_s']).tolist(),
                    converter_power_at_ideal_1v_w=float(metrics['charge_a_s'].sum()/metrics['elapsed_s']))
        h2,e2,s2=ring(z,di3=0,origin=50e-9,max_handoffs=args.long_handoffs,
                      tolerances=dict(rtol=tol,atol=tol),
                      negative_target=(11.25 if args.negative_target_a is None else args.negative_target_a))
        result.update(two_ring_admission=len(h2)==8 and not any('failure' in r for r in h2),
                      two_ring_handoffs=len(h2),two_ring_last_event=h2[-1])
        result.update(inductance_nh=args.inductance_nh,negative_target_a=args.negative_target_a,
                      requested_long_handoffs=args.long_handoffs,
                      all_requested_handoffs_pass=len(h2)==args.long_handoffs and not any('failure' in r for r in h2))
        if not one_pass:
            result['warning']='return vector and mean current concern only partial failed trajectory'
        print(json.dumps(result),flush=True)
    print('No periodicity, stability, startup, regulation, or paper reproduction is certified.')

if __name__=='__main__':main()
