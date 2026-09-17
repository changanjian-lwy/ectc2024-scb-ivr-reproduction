"""Compare P24's ideal triangular design equations with the detailed fixture."""
import argparse,ast,json
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring

VIN=48.;VO=1.;P=1000.;NP=4;NM=4;F=5e6
def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path)
    p.add_argument('--inductance-nh',type=float,required=True);p.add_argument('--negative-target-a',type=float,required=True);args=p.parse_args()
    line=[x for x in args.candidate_log.read_text().splitlines() if x.startswith('retained state ')][-1]
    z=np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]));model.L=args.inductance_nh*1e-9
    metrics={};h,end,start=ring(z,di3=0.,origin=50e-9,max_handoffs=4,negative_target=args.negative_target_a,
      metrics=metrics,tolerances=dict(rtol=1e-10,atol=1e-10))
    if len(h)!=4 or any('failure' in r for r in h):raise RuntimeError(str(h[-1]))
    Ts=1/F;slot=Ts/NP;Io=P/VO;D=NP*VO/VIN;ton=D*Ts
    Ipk=2*Io/(NP*NM);Lcrit=NP*NM*VO/(2*Io*F)*(1-NP*VO/VIN)
    detailed_power=float(metrics['charge_a_s'].sum()/metrics['elapsed_s'])
    print(json.dumps(dict(
      p24_ideal=dict(Ts_ns=Ts*1e9,slot_ns=slot*1e9,duty=D,ton_ns=ton*1e9,
        total_output_current_a=Io,per_module_mean_current_a=Io/NM,
        per_phase_mean_current_a=Io/(NP*NM),peak_current_a=Ipk,Lcrit_nh=Lcrit*1e9,
        identities=['Ipk=2Io/(NP NM)','D=NP Vo/Vin','Lcrit=(Vin/NP-Vo) Ton/Ipk']),
      detailed_fixture=dict(inductance_nh=args.inductance_nh,negative_target_a=args.negative_target_a,
        peak_current_range_a=[min(r['peak_a'] for r in h),max(r['peak_a'] for r in h)],
        negative_fraction_pct_range=[100*args.negative_target_a/max(r['peak_a'] for r in h),
                                     100*args.negative_target_a/min(r['peak_a'] for r in h)],
        per_phase_mean_current_a=(metrics['charge_a_s']/metrics['elapsed_s']).tolist(),
        single_module_power_at_ideal_1v_w=detailed_power,
        target_fraction=detailed_power/(P/NM),power_deficit_w=P/NM-detailed_power,
        included=['finite Coss commutation','Ron and winding R','negative-current target','finite flying capacitors'],
        excluded=['zero startup','closed-loop regulation','nonlinear manufacturer GaN model','four-module coupling']),
      conclusion='The P24 ideal equations reproduce 250 W/module algebraically; the detailed borrowed-parameter fixture does not.'),indent=2))

if __name__=='__main__':main()
