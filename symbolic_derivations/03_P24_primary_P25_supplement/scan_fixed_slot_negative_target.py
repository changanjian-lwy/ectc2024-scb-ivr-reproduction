"""Scan J for the first fixed-spacing handoff without changing its seed."""
import argparse,ast,csv,json
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring

HERE=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--inductance-nh',type=float,required=True)
    p.add_argument('--start-a',type=float,default=1.);p.add_argument('--stop-a',type=float,default=20.)
    p.add_argument('--step-a',type=float,default=.05);p.add_argument('--csv',type=Path,required=True);args=p.parse_args()
    line=next(x for x in (HERE/'node_cap_5p23mv_buffer_half_run.txt').read_text().splitlines() if x.startswith('retained state '))
    z=np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
    model.L=args.inductance_nh*1e-9;rows=[]
    for J in np.arange(args.start_a,args.stop_a+args.step_a/2,args.step_a):
        h,_,_=ring(z,di3=0.,origin=50e-9,max_handoffs=1,negative_target=float(J),
                   tolerances=dict(rtol=1e-9,atol=1e-9))
        r=h[0];zeros=r.get('natural_zero_ns',[])
        rows.append(dict(J_a=float(J),peak_a=r['peak_a'],fraction_pct=100*J/r['peak_a'],
                         release_ns=r.get('release_ns'),first_zero_ns=zeros[0] if zeros else None,
                         vds_slot_v=r.get('vds_slot_v'),next_current_slot_a=r.get('next_current_slot_a'),
                         pass_fixed_slot='failure' not in r,failure=r.get('failure')))
    with args.csv.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    passed=[r for r in rows if r['pass_fixed_slot']]
    closest=min((r for r in rows if r['vds_slot_v'] is not None),key=lambda r:abs(r['vds_slot_v']))
    print(json.dumps(dict(inductance_nh=args.inductance_nh,seed='same N4 preselected state',
      fixed_slot_ns=100.,scan_step_a=args.step_a,pass_count=len(passed),
      sampled_pass_interval_a=([passed[0]['J_a'],passed[-1]['J_a']] if passed else None),
      sampled_pass_fraction_pct=([passed[0]['fraction_pct'],passed[-1]['fraction_pct']] if passed else None),
      closest_sample=closest,
      limitation='sampled first handoff only; interval endpoints are not yet root-refined and do not certify a full ring'),indent=2))

if __name__=='__main__':main()
