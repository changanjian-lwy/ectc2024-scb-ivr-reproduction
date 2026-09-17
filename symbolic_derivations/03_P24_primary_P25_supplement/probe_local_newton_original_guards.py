"""Diagnostic of local Newton direction under original physical guards only.

Does not enforce extra 1 ps/5.23mV optimization limits. Candidates are
explicitly separate and never substitute for the constrained retained state.
"""
import argparse,ast,json
from pathlib import Path
import numpy as np
from solve_fixed_point_feasible_newton import evaluate,SCALE

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path)
    p.add_argument('spectrum_log',type=Path);args=p.parse_args()
    line=next(x for x in args.candidate_log.read_text().splitlines() if x.startswith('retained state '))
    z=np.array(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
    row=next(json.loads(x) for x in args.spectrum_log.read_text().splitlines() if x.startswith('{'))
    direction=np.array(row['linear_unconstrained_step_physical'])
    f,meta=evaluate(z);base=np.linalg.norm(f);best=None
    for power in range(13):
        damping=2.**(-power);trial=z+damping*direction
        fk,m=evaluate(trial)
        result=dict(damping=damping,original_guards_pass=fk is not None)
        if fk is None:result['failure']=m
        else:
            result.update(norm=float(np.linalg.norm(fk)),max_node_return_mv=float(np.max(abs(fk[:7]*SCALE[:7]))*1e3),
                          first_zero_leads_ps=[(r['slot_ns']-r['natural_zero_ns'][0])*1000 for r in m['history']])
            if np.linalg.norm(fk)<base and (best is None or np.linalg.norm(fk)<best[0]):
                best=(np.linalg.norm(fk),trial,fk)
        print(json.dumps(result),flush=True)
    if best:
        print('retained state',best[1].tolist(),'physical residual',(best[2]*SCALE).tolist(),'norm',best[0],flush=True)
    print('Original-guard diagnostic only; does not replace the auxiliary-margin-constrained branch.')

if __name__=='__main__':main()
