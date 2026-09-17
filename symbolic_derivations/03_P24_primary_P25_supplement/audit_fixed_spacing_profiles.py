"""Compare source-labelled L/J profiles under the same fixed P24 spacing.

Only L and negative target vary as listed. The N4 preselected steady-state
candidate is reused and is not re-optimized for a changed L. This is an
admission audit, not zero startup or a successful periodic reproduction.
"""
import ast,json
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring

HERE=Path(__file__).resolve().parent
SEED_LOG=HERE/'node_cap_5p23mv_buffer_half_run.txt'
TON=4/48*200e-9
PROFILES=[
 dict(name='Lcrit_P25supp_9pct_nominal',L_nh=1.4666666666666668,J_a=11.25,
      source='P24 Eq4 Lcrit; P25 5-10% extension; 9% of nominal 125A'),
 dict(name='P24_L98_nominal_2pct',L_nh=1.4373333333333334,J_a=2.5,
      source='P24 2% below Lcrit selection and 2% of nominal 125A'),
 dict(name='P25_L95_9pct_nominal',L_nh=1.3933333333333333,J_a=11.25,
      source='P25 Eq20 0.95 extension to P24 target; 9% nominal'),
 dict(name='P25_L95_scanned_12A',L_nh=1.3933333333333333,J_a=12.,
      source='same previous profile; only J scan 11.25 to 12A'),
 dict(name='L98_first_handoff_window_midpoint',L_nh=1.4373333333333334,J_a=11.9,
      source='diagnostic midpoint inside first-handoff fixed-slot window; not paper data'),
 dict(name='L95_first_handoff_window_midpoint',L_nh=1.3933333333333333,J_a=13.0,
      source='diagnostic midpoint inside first-handoff fixed-slot window; not paper data')]

def seed():
    line=next(x for x in SEED_LOG.read_text().splitlines() if x.startswith('retained state '))
    return np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))

def main():
    z=seed()
    for case in PROFILES:
        model.L=case['L_nh']*1e-9
        metrics={}
        hist,end,start=ring(z,di3=0.,origin=50e-9,max_handoffs=4,metrics=metrics,
                            negative_target=case['J_a'],ton=TON,
                            tolerances=dict(rtol=1e-9,atol=1e-9))
        complete=len(hist)==4 and not any('failure' in r for r in hist)
        row=dict(case,topology='P24 four phase single module',sequence='P25 all inactive lows on supplement',
                 fixed_spacing_ns=50.,ton_ns=TON*1e9,preselected_seed='N4; not reoptimized for changed L',
                 completed_handoffs=sum('failure' not in r for r in hist),complete_ring=complete,
                 earliest_failure=next((r for r in hist if 'failure' in r),None),history=hist)
        if complete:
            row.update(period_ns=metrics['elapsed_s']*1e9,
                       converter_power_at_ideal_1v_w=float(metrics['charge_a_s'].sum()/metrics['elapsed_s']),
                       node_return_v=(end-start)[:7].tolist(),current_return_a=(end-start)[7:].tolist())
        print(json.dumps(row),flush=True)
    print('Profiles are separate source-labelled diagnostics; none is a zero-start or full-system claim.')

if __name__=='__main__':main()
