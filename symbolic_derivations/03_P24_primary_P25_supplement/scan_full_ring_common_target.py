"""Search a common J across all four fixed-spacing handoffs.

The preselected N4 seed and all other model parameters remain fixed.
"""
import argparse,ast,csv,json
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring

HERE=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--inductance-nh',type=float,required=True)
    p.add_argument('--seed-log',type=Path,default=HERE/'node_cap_5p23mv_buffer_half_run.txt')
    p.add_argument('--low-policy',choices=['p25_all_inactive','p24_adjacent_literal'],default='p25_all_inactive')
    p.add_argument('--start-a',type=float,default=1.);p.add_argument('--stop-a',type=float,default=20.)
    p.add_argument('--step-a',type=float,default=.05);p.add_argument('--csv',type=Path,required=True);args=p.parse_args()
    line=next(x for x in args.seed_log.read_text().splitlines() if x.startswith('retained state '))
    z=np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]));model.L=args.inductance_nh*1e-9
    rows=[]
    for J in np.arange(args.start_a,args.stop_a+args.step_a/2,args.step_a):
        h,end,start=ring(z,di3=0.,origin=50e-9,max_handoffs=4,negative_target=float(J),
                         tolerances=dict(rtol=1e-9,atol=1e-9),low_policy=args.low_policy)
        complete=len(h)==4 and not any('failure' in r for r in h)
        fail=next((r for r in h if 'failure' in r),None)
        rows.append(dict(J_a=float(J),complete_ring=complete,
          completed_handoffs=sum('failure' not in r for r in h),
          failure_active_phase=None if fail is None else fail['active_phase'],
          failure=None if fail is None else fail['failure'],
          failure_vds_slot_v=None if fail is None else fail.get('vds_slot_v'),
          max_node_return_v=(float(np.max(abs((end-start)[:7]))) if complete else None),
          max_current_return_a=(float(np.max(abs((end-start)[7:]))) if complete else None)))
    with args.csv.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    full=[r for r in rows if r['complete_ring']];furthest=max(r['completed_handoffs'] for r in rows)
    print(json.dumps(dict(inductance_nh=args.inductance_nh,scan_step_a=args.step_a,
      complete_count=len(full),sampled_complete_interval_a=([full[0]['J_a'],full[-1]['J_a']] if full else None),
      furthest_completed_handoffs=furthest,
      J_at_furthest=[r['J_a'] for r in rows if r['completed_handoffs']==furthest],
      seed_log=str(args.seed_log),
      low_policy=args.low_policy,
      limitation='sampled common-J search at one preselected seed; full-ring admission is not periodic closure'),indent=2))

if __name__=='__main__':main()
