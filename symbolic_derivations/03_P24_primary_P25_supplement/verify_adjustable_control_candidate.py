"""Verify the explicitly fitted controls; never silently use fixed defaults."""
import argparse,json,subprocess,sys
from pathlib import Path
import numpy as np
from solve_adjustable_control_diagnostic import evaluate,MASK,HERE

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path);args=p.parse_args()
    case=next(json.loads(x) for x in args.candidate_log.read_text().splitlines()
              if x.startswith('{') and json.loads(x).get('fitted_control_candidate'))
    z=np.array(case['state']);q=np.r_[z[MASK],case['ton_ns'],case['negative_target_a']]
    # Boundary trap: old fixed-control verifier MUST reject this different
    # record format, not verify under its original Ton/J by accident.
    old=subprocess.run([sys.executable,str(HERE/'verify_retained_candidate.py'),str(args.candidate_log)],
                       capture_output=True,text=True)
    assert old.returncode!=0,'fixed-control verifier silently accepted fitted-control record'
    print('PASS incompatible fixed-control record trap',flush=True)
    for tol in [1e-9,1e-10]:
        f,m=evaluate(q,handoffs=160,tolerance=tol,inductance_nh=case.get('inductance_nh'))
        result=dict(tolerance=tol,ton_ns=float(q[-2]),negative_target_a=float(q[-1]),
                    inductance_nh=case.get('inductance_nh'),
                    all_requested_handoffs_pass=f is not None,details=m)
        if f is not None:result['first_ring_normalized_residual']=f.tolist()
        print(json.dumps(result),flush=True)
    print('No fitted controls are substituted into fixed-slot/native-paper cases.')

if __name__=='__main__':main()
