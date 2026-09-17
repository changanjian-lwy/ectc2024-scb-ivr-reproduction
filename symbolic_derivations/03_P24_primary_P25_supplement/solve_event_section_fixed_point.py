"""Shoot the event-only diagnostic on the H2 Vds=0 section.

Ten independent initial coordinates; a2=a1 is the event section, not a
prescribed flying-cap level. Same tested CLI controller used for every
evaluation. No new on-time, J, component, or fixed-frequency claim.
"""
import argparse,ast,json,subprocess,sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
MASK=np.array([0,2,3,4,5,6,7,8,9,10])
SCALE=np.r_[np.full(6,12.),np.full(4,125.)]
CALLS=0

def expand(q):
    z=np.zeros(11);z[MASK]=q;z[1]=z[0];return z

def evaluate(q):
    global CALLS
    CALLS+=1
    z=expand(q)
    out=subprocess.check_output([sys.executable,str(HERE/'event_admission_diagnostic.py'),
                                 '--seed-json',json.dumps(z.tolist()),'--handoffs','4',
                                 '--strict-all-other-positive'],text=True)
    rows=[json.loads(x) for x in out.splitlines() if x.startswith('{')]
    failure=next((r for r in rows if 'failure' in r),None)
    if failure:return None,failure
    end=next(r for r in rows if 'completed_ring' in r)
    return (np.array(end['end_state'])[MASK]-q)/SCALE,end

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path)
    p.add_argument('--iterations',type=int,default=12);args=p.parse_args()
    line=next(x for x in args.candidate_log.read_text().splitlines() if x.startswith('retained state '))
    z=np.array(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
    # First reach the section with an actual full event cycle, not projection
    # of arbitrary a1/a2 values. Subsequent expansion removes roundoff only.
    out=subprocess.check_output([sys.executable,str(HERE/'event_admission_diagnostic.py'),
                                 '--seed-json',json.dumps(z.tolist()),'--handoffs','4',
                                 '--strict-all-other-positive'],text=True)
    first=next(json.loads(x) for x in out.splitlines() if x.startswith('{') and 'completed_ring' in json.loads(x))
    reached=np.array(first['end_state'])
    print('actual section reach a1-a2 V',reached[0]-reached[1],flush=True)
    q=reached[MASK];f,m=evaluate(q)
    if f is None:raise ValueError(str(m))
    print('initial norm',np.linalg.norm(f),flush=True)
    for iteration in range(args.iterations):
        if np.max(abs(f[:6]*SCALE[:6]))<1e-7 and np.max(abs(f[6:]*SCALE[6:]))<1e-4:
            print('numerical shooting tolerance reached (not paper tolerance)',flush=True);break
        cols=[]
        for k in range(10):
            eps=1e-6 if k<6 else 1e-4
            qp=q.copy();qm=q.copy();qp[k]+=eps;qm[k]-=eps
            fp,mp=evaluate(qp);fm,mm=evaluate(qm)
            if fp is not None and fm is not None:col=(fp-fm)/(2*eps/SCALE[k])
            elif fp is not None:col=(fp-f)/(eps/SCALE[k])
            elif fm is not None:col=(f-fm)/(eps/SCALE[k])
            else:raise ValueError(f'derivative infeasible at {k}')
            cols.append(col)
        j=np.column_stack(cols)
        sol,_,rank,singular=np.linalg.lstsq(j,-f,rcond=1e-10)
        d=sol*SCALE
        ratio=max(1.,np.max(abs(d[:6]))/.02,np.max(abs(d[6:]))/.25);d/=ratio
        print('iteration',iteration,'linear rank',rank,'singular values',singular.tolist(),
              'trust ratio',ratio,'unscaled physical step',(sol*SCALE).tolist(),flush=True)
        accepted=False
        for power in range(9):
            damping=2.**(-power);fk,mk=evaluate(q+damping*d)
            if fk is None:
                print('iteration',iteration,'damping',damping,'guard failure',mk['failure'],flush=True);continue
            if np.linalg.norm(fk)<np.linalg.norm(f):
                q,f,m=q+damping*d,fk,mk;accepted=True
                print('iteration',iteration,'accepted damping',damping,'norm',np.linalg.norm(f),
                      'period ns',m['period_ns'],'power W',m['converter_power_at_ideal_1v_w'],flush=True);break
        if not accepted:
            print('STOP no verified residual descent in tested direction',flush=True);break
    z=expand(q);res=np.array(m['end_state'])-z
    print('retained state',z.tolist(),'physical residual',res.tolist(),'norm',np.linalg.norm(f),flush=True)
    print('evaluation count',CALLS,'period ns',m['period_ns'],'power W',m['converter_power_at_ideal_1v_w'],flush=True)
    print('Event-only diagnostic; no fixed-frequency, nominal power, stability, or startup certification.')

if __name__=='__main__':main()
