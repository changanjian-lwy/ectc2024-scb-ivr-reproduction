"""Audit ring-to-ring drift without changing the controller or model.

The exact endpoint identity used here is
    mean(v_L,net) = L * (i_end-i_start) / T,
where v_L,net already includes the model's winding-resistance drop.
This diagnoses the size and sign of the missing volt-second balance; it does
not infer an unmeasured gate waveform or claim a physical cause by itself.
"""
import argparse,csv,json
from pathlib import Path
import numpy as np
from full_matrix_interval_propagator import C

NAMES=['a1','a2','a3','x1','x2','x3','x4','i1','i2','i3','i4']

def one_json(path,predicate):
    return next(json.loads(line) for line in path.read_text().splitlines()
                if line.startswith('{') and predicate(json.loads(line)))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('candidate_log',type=Path)
    p.add_argument('verification_log',type=Path)
    p.add_argument('--tolerance',type=float,default=1e-9)
    p.add_argument('--csv',type=Path)
    args=p.parse_args()
    case=one_json(args.candidate_log,lambda r:r.get('fitted_control_candidate'))
    result=one_json(args.verification_log,lambda r:r.get('tolerance')==args.tolerance)
    rings=result['details']['all_rings']
    if not rings:raise ValueError('no completed rings')
    L=(case['inductance_nh'] if case.get('inductance_nh') is not None else 1.4666666666666668)*1e-9
    start=np.asarray(case['state'],float)
    rows=[]
    for ring in rings:
        end=np.asarray(ring['end_state'],float);T=ring['period_ns']*1e-9
        dz=end-start
        mean_net_vl=L*dz[7:]/T
        ec0=.5*start[:7]@C@start[:7];ec1=.5*end[:7]@C@end[:7]
        el0=.5*L*np.dot(start[7:],start[7:]);el1=.5*L*np.dot(end[7:],end[7:])
        rows.append(dict(ring=ring['completed_ring'],period_ns=ring['period_ns'],
                         power_w=ring['converter_power_at_ideal_1v_w'],
                         **{f'd_{NAMES[k]}':float(dz[k]) for k in range(11)},
                         **{f'mean_net_vl_{k+1}_mv':float(mean_net_vl[k]*1e3) for k in range(4)},
                         capacitor_energy_change_nj=float((ec1-ec0)*1e9),
                         inductor_energy_change_nj=float((el1-el0)*1e9)))
        start=end
    if args.csv:
        with args.csv.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    # Exclude the first ring from the linear trend because it starts from the
    # optimizer seed and visibly contains a one-time settling displacement.
    stable=rows[1:] if len(rows)>2 else rows
    summary={
      'completed_rings':len(rows),
      'failure':result['details'].get('failure'),
      'failure_handoff':result['details'].get('handoff'),
      'mean_period_ns_after_first':float(np.mean([r['period_ns'] for r in stable])),
      'mean_power_w_after_first':float(np.mean([r['power_w'] for r in stable])),
      'mean_net_inductor_voltage_mv_after_first':[
        float(np.mean([r[f'mean_net_vl_{k+1}_mv'] for r in stable])) for k in range(4)],
      'mean_current_change_a_per_ring_after_first':[
        float(np.mean([r[f'd_i{k+1}'] for r in stable])) for k in range(4)],
      'last_ring_current_change_a':[
        float(rows[-1][f'd_i{k+1}']) for k in range(4)],
      'interpretation_limit':'endpoint volt-second imbalance only; it does not identify a unique physical cause'}
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
