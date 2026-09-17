"""Separate P25-inspired control working-point diagnostic, not paper data.

Unknowns: 10 event-section states, uniform Ton and common negative target.
Equations: 10 state returns, period 200ns, converter power at ideal 1V=250W.
Measured per-phase peak fractions 5-10% are checked, not merely nominal.
No prior controller or component value is changed.
"""
import argparse,ast,json,subprocess,sys
from pathlib import Path
import numpy as np
from solve_event_section_fixed_point import HERE,MASK,expand,SCALE as STATE_SCALE

SCALE=np.r_[STATE_SCALE,20.,125.]

def evaluate(q,handoffs=4,tolerance=1e-9,inductance_nh=None):
    ton,target=q[-2:]
    if not 3.4<=ton<50. or target<=0:return None,{'failure':'diagnostic control bounds'}
    z=expand(q[:10])
    command=[sys.executable,str(HERE/'event_admission_diagnostic.py'),
                                 '--seed-json',json.dumps(z.tolist()),'--handoffs',str(handoffs),
                                 '--strict-all-other-positive','--ton-ns',str(ton),
                                 '--negative-target-a',str(target),'--tolerance',str(tolerance)]
    if inductance_nh is not None:command+=['--inductance-nh',str(inductance_nh)]
    out=subprocess.check_output(command,text=True)
    rows=[json.loads(x) for x in out.splitlines() if x.startswith('{')]
    failure=next((r for r in rows if 'failure' in r),None)
    if failure:
        return None,dict(failure,completed_rings=len([r for r in rows if 'completed_ring' in r]),
                         all_rings=[r for r in rows if 'completed_ring' in r])
    peaks=[r['peak_a'] for r in rows if 'handoff' in r]
    if any(not .05<=target/p<=.10 for p in peaks):
        return None,{'failure':'actual active-peak fraction outside 5-10%',
                     'fraction_range':[target/max(peaks),target/min(peaks)]}
    rings=[r for r in rows if 'completed_ring' in r]
    if len(rings)!=handoffs//4:return None,{'failure':'incomplete diagnostic rings'}
    if any(ton/r['period_ns']>1/4 for r in rings):return None,{'failure':'duty exceeds P25 no-overlap design bound'}
    m=rings[0]
    f=np.r_[(np.array(m['end_state'])[MASK]-q[:10])/STATE_SCALE,
             (m['period_ns']-200.)/200.,(m['converter_power_at_ideal_1v_w']-250.)/250.]
    return f,dict(first_ring=m,all_rings=rings,peaks_a=peaks)

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path,nargs='?')
    p.add_argument('--event-seed-log',type=Path)
    p.add_argument('--inductance-nh',type=float)
    p.add_argument('--initial-negative-target-a',type=float,default=11.25)
    p.add_argument('--iterations',type=int,default=8);args=p.parse_args()
    if args.event_seed_log:
        if args.candidate_log:p.error('choose an event log or a candidate log')
        rings=[json.loads(x) for x in args.event_seed_log.read_text().splitlines()
               if x.startswith('{') and 'completed_ring' in json.loads(x)]
        z=np.array(rings[-1]['end_state'])
        print('actual event-section seed from',str(args.event_seed_log),flush=True)
    else:
        if args.candidate_log is None:p.error('candidate log or event seed log required')
        line=next(x for x in args.candidate_log.read_text().splitlines() if x.startswith('retained state '))
        z=np.array(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
    if abs(z[0]-z[1])>1e-9:raise ValueError('seed must have actually reached H2 zero section')
    q=np.r_[z[MASK],16.666666666666668,args.initial_negative_target_a]
    def model_evaluate(q):return evaluate(q,inductance_nh=args.inductance_nh)
    f,m=model_evaluate(q)
    if f is None:raise ValueError(str(m))
    ridge=1e-8
    print('initial norm',np.linalg.norm(f),'separate adjustable-control diagnostic',flush=True)
    for iteration in range(args.iterations):
        cols=[]
        for k in range(12):
            eps=1e-6 if k<6 else 1e-4
            qp=q.copy();qm=q.copy();qp[k]+=eps;qm[k]-=eps
            fp,mp=model_evaluate(qp);fm,mm=model_evaluate(qm)
            if fp is not None and fm is not None:col=(fp-fm)/(2*eps/SCALE[k])
            elif fp is not None:col=(fp-f)/(eps/SCALE[k])
            elif fm is not None:col=(f-fm)/(eps/SCALE[k])
            else:raise ValueError(f'no valid derivative at {k}')
            cols.append(col)
        j=np.column_stack(cols)
        d=np.linalg.solve(j.T@j+ridge*np.eye(12),-j.T@f)*SCALE
        ratio=max(1.,np.max(abs(d[:6]))/.1,np.max(abs(d[6:10]))/1.,abs(d[-2])/1.,abs(d[-1])/.5)
        d/=ratio;accepted=False
        for power in range(9):
            damping=2.**(-power);fk,mk=model_evaluate(q+damping*d)
            if fk is None:
                print('iteration',iteration,'damping',damping,'failure',mk['failure'],flush=True);continue
            if np.linalg.norm(fk)<np.linalg.norm(f):
                q,f,m=q+damping*d,fk,mk;accepted=True;ridge=max(1e-14,ridge/3.)
                print('iteration',iteration,'norm',np.linalg.norm(f),'Ton ns',q[-2],'negative target A',q[-1],
                      'period ns',m['first_ring']['period_ns'],'power W',m['first_ring']['converter_power_at_ideal_1v_w'],flush=True);break
        if not accepted:ridge*=10.;print('no accepted step; regularization increased',ridge,flush=True)
    # Different marker prevents old fixed-control verifier silently reverting
    # these fitted controls to its defaults. Full provenance is explicit.
    print(json.dumps(dict(fitted_control_candidate=True,state=expand(q[:10]).tolist(),ton_ns=float(q[-2]),
                          inductance_nh=args.inductance_nh,model_profile='GS_constant_Coss_ideal_reverse_1V_sink',
                          negative_target_a=float(q[-1]),normalized_residual=f.tolist(),
                          first_ring=m['first_ring'],peaks_a=m['peaks_a'])),flush=True)
    print('Fitted controls are not paper-provided data; no reproduction or startup certification.')

if __name__=='__main__':main()
