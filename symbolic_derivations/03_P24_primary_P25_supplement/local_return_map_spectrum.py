"""Local, finite-difference conditioning diagnostic; not stability proof."""
import argparse,ast,json
from pathlib import Path
import numpy as np
from solve_fixed_point_feasible_newton import evaluate,SCALE

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path);args=p.parse_args()
    line=next(x for x in args.candidate_log.read_text().splitlines() if x.startswith('retained state '))
    z=np.array(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
    f,m=evaluate(z)
    if f is None:raise ValueError('candidate outside original event domain')
    for factor in [1.,.5]:
        cols=[];used=[]
        for k in range(11):
            eps=factor*(1e-6 if k<7 else 1e-4)
            plus=z.copy();plus[k]+=eps;minus=z.copy();minus[k]-=eps
            fp,mp=evaluate(plus);fm,mm=evaluate(minus)
            if fp is not None and fm is not None:
                col=(fp-fm)/(2*eps/SCALE[k]);scheme='central'
            elif fp is not None:col=(fp-f)/(eps/SCALE[k]);scheme='forward'
            elif fm is not None:col=(f-fm)/(eps/SCALE[k]);scheme='backward'
            else:raise ValueError(f'no valid derivative at coordinate {k}')
            cols.append(col);used.append(scheme)
        j=np.column_stack(cols);u,s,v=np.linalg.svd(j)
        d=np.linalg.lstsq(j,-f,rcond=1e-10)[0]
        print(json.dumps(dict(step_factor=factor,schemes=used,singular_values=s.tolist(),
                              condition=float(s[0]/s[-1]),linear_unconstrained_step_physical=(d*SCALE).tolist(),
                              linear_residual_norm=float(np.linalg.norm(f+j@d)),
                              normalized_residual_left_singular_components=(u.T@f).tolist())),flush=True)
    print('No unconstrained step is applied; local linear solve is not a feasible periodic solution or stability proof.')

if __name__=='__main__':main()
