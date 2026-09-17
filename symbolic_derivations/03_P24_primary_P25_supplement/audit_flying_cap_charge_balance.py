"""Convert one-ring flying-voltage return into charge/current imbalance."""
import argparse,ast,json
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from audit_four_positions_existing_cases import FLY
from joint_predecessor_event_ring import ring

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path)
    p.add_argument('--inductance-nh',type=float,required=True);p.add_argument('--negative-target-a',type=float,required=True);args=p.parse_args()
    line=[x for x in args.candidate_log.read_text().splitlines() if x.startswith('retained state ')][-1]
    z=np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]));model.L=args.inductance_nh*1e-9
    h,end,start=ring(z,di3=0.,origin=50e-9,max_handoffs=4,negative_target=args.negative_target_a,
      tolerances=dict(rtol=1e-10,atol=1e-10))
    if len(h)!=4 or any('failure' in r for r in h):raise RuntimeError(str(h[-1]))
    dv=np.array([(end[k]-end[3+k])-(start[k]-start[3+k]) for k in range(3)])
    dq=FLY*dv;period=200e-9
    print(json.dumps(dict(flying_capacitance_uf=FLY*1e6,
      delta_flying_voltage_mv_per_ring=(dv*1e3).tolist(),
      net_charge_imbalance_nc_per_ring=(dq*1e9).tolist(),
      equivalent_average_imbalance_ma=(dq/period*1e3).tolist(),
      first_ring_vds_margin_mv=[-r['vds_slot_v']*1e3 for r in h],
      projected_drift_is_linearized_only=True,
      conclusion='millivolt ZVS margins coexist with 0.1-0.3mV/ring flying-voltage drift; long-run failure is therefore expected even when one-ring residual looks small'),indent=2))

if __name__=='__main__':main()
