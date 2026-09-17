"""Independent hold-off window probes; no changes to ring gate decisions."""
import ast
import argparse
import json
from pathlib import Path
import numpy as np
from joint_predecessor_event_ring import ring
from check_newton_retained_candidate import Z
from check_constrained_retained_candidate import ZQP

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate-log',type=Path)
    args=parser.parse_args()
    log=Path(__file__).with_name('constrained_margin_half_run.txt').read_text()
    line=next(x for x in log.splitlines() if x.startswith('retained state '))
    zm=np.array(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
    candidates=[('Newton retained',Z),('QP edge',ZQP),('half-margin descent',zm)]
    if args.candidate_log:
        line=next(x for x in args.candidate_log.read_text().splitlines()
                  if x.startswith('retained state '))
        state=np.array(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
        if state.shape!=(11,) or not np.all(np.isfinite(state)):
            raise ValueError('invalid retained candidate')
        candidates=[(str(args.candidate_log),state)]
    for name,z in candidates:
        for tol in [1e-9,1e-10]:
            h,end,start=ring(z,di3=0,origin=50e-9,
                             tolerances=dict(rtol=tol,atol=tol),window_extension_ns=5.)
            for row in h:
                if 'hold_off_probe' not in row:continue
                zeros=row['natural_zero_ns'];exits=row['hold_off_probe']['positive_vds_crossings_ns']
                if zeros:
                    later=[x for x in exits if x>zeros[0]]
                    row['first_zero_lead_ps']=(row['slot_ns']-zeros[0])*1000
                    row['hold_off_exit_lag_ps']=((later[0]-row['slot_ns'])*1000 if later else None)
                    row['hold_off_window_width_ps']=((later[0]-zeros[0])*1000 if later else None)
            print(json.dumps(dict(candidate=name,tolerance=tol,
                                  current_return_error_a=(end-start)[7:].tolist(),events=h)),flush=True)
    print('Windows are counterfactual gate-held-off probes, not actual driver-delay allowances.')

if __name__=='__main__':main()
