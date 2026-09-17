"""Exact KVL decomposition of each high-on peak-current deficit."""
import argparse,ast,json
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path)
    p.add_argument('--inductance-nh',type=float,required=True);p.add_argument('--negative-target-a',type=float,required=True);args=p.parse_args()
    line=[x for x in args.candidate_log.read_text().splitlines() if x.startswith('retained state ')][-1]
    z=np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]));model.L=args.inductance_nh*1e-9
    metrics={};h,_,_=ring(z,di3=0.,origin=50e-9,max_handoffs=4,negative_target=args.negative_target_a,
      metrics=metrics,tolerances=dict(rtol=1e-10,atol=1e-10))
    if len(h)!=4 or any('failure' in r for r in h):raise RuntimeError(str(h[-1]))
    rows=[];L=args.inductance_nh*1e-9
    for s in metrics['segments']:
        if not s['name'].endswith('_on'):continue
        phase=int(s['name'][1]);k=phase-1;start=np.asarray(s['start_state']);end=np.asarray(s['end_state'])
        dt=s['duration_ns']*1e-9;mean_i=np.asarray(s['charge_a_ns'])/s['duration_ns']
        delta=end[7+k]-start[7+k]
        mean_x=1.+model.RIND*mean_i[k]+L*delta/dt
        ideal_delta_same_L=(12.-1.)*dt/L
        rows.append(dict(phase=phase,start_current_a=float(start[7+k]),peak_current_a=float(end[7+k]),
          current_rise_a=float(delta),mean_phase_node_v=float(mean_x),mean_inductor_current_a=float(mean_i[k]),
          ideal_current_rise_at_12v_node_same_L_a=float(ideal_delta_same_L),
          rise_deficit_from_effective_voltage_a=float(delta-ideal_delta_same_L),
          peak_minus_p24_125a=float(end[7+k]-125.),
          identity_error_a=float(end[7+k]-(start[7+k]+(mean_x-1.-model.RIND*mean_i[k])*dt/L))))
    print(json.dumps(dict(inductance_nh=args.inductance_nh,rows=rows,
      exact_identity='Ipk=Istart+(mean(Vx)-Vo-Rind mean(I))*Ton/L',
      interpretation='negative start current and mean phase-node voltage below 12V are separately visible; no unique device attribution is inferred'),indent=2))

if __name__=='__main__':main()
