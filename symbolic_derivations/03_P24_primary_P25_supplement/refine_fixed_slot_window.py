"""Refine one Vds(slot)=0 boundary bracket for the first handoff."""
import argparse,ast,json
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring

HERE=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--inductance-nh',type=float,required=True)
    p.add_argument('--lo-a',type=float,required=True);p.add_argument('--hi-a',type=float,required=True)
    p.add_argument('--iterations',type=int,default=24);args=p.parse_args()
    line=next(x for x in (HERE/'node_cap_5p23mv_buffer_half_run.txt').read_text().splitlines() if x.startswith('retained state '))
    z=np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]));model.L=args.inductance_nh*1e-9
    def calc(J):
        r=ring(z,di3=0.,origin=50e-9,max_handoffs=1,negative_target=J,
               tolerances=dict(rtol=1e-10,atol=1e-10))[0][0]
        return r['vds_slot_v'],r
    lo,hi=args.lo_a,args.hi_a;flo,_=calc(lo);fhi,_=calc(hi)
    if flo*fhi>=0:raise ValueError(f'not a sign bracket {flo} {fhi}')
    for _ in range(args.iterations):
        mid=(lo+hi)/2;fm,_=calc(mid)
        if flo*fm<=0:hi,fhi=mid,fm
        else:lo,flo=mid,fm
    mid=(lo+hi)/2;fm,r=calc(mid)
    print(json.dumps(dict(inductance_nh=args.inductance_nh,boundary_target_a=mid,
      actual_peak_a=r['peak_a'],fraction_pct=100*mid/r['peak_a'],vds_slot_v=fm,
      release_ns=r.get('release_ns'),first_zero_ns=(r.get('natural_zero_ns') or [None])[0],
      bracket_a=[lo,hi],limitation='first handoff and fixed N4 seed only'),indent=2))

if __name__=='__main__':main()
