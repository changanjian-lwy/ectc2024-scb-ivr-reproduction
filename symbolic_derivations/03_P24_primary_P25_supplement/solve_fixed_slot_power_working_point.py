"""Joint fixed-slot state/J/power working-point diagnostic.

Unknowns are 11 section states plus one common negative-current target J.
Equations are 11 full-state returns plus P=250 W at the ideal 1 V sink.
Ton and 50 ns interleaving stay locked to P24. J must remain 5-10% of
every measured active-phase peak. This is a numerical diagnostic, not paper
firmware, zero-start, stability, or a manufacturer-device validation.
"""
import argparse,ast,json
from pathlib import Path
import numpy as np
import finite_resistance_interval as model
from joint_predecessor_event_ring import ring,vhigh

SCALE=np.r_[np.full(7,12.),np.full(4,125.),250.]
def load_state(path):
    line=[x for x in path.read_text().splitlines() if x.startswith('retained state ')][-1]
    return np.asarray(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))

def evaluate(q,Lnh):
    z=q[:11];J=q[11]
    if J<=0 or vhigh(z,1)>0:return None,{'failure':'bounds/initial H2 ZVS'}
    model.L=Lnh*1e-9;metrics={}
    h,end,start=ring(z,di3=0.,origin=50e-9,max_handoffs=4,negative_target=J,metrics=metrics,
                     tolerances=dict(rtol=1e-9,atol=1e-9))
    if len(h)!=4 or any('failure' in r for r in h):return None,next(r for r in h if 'failure' in r)
    fractions=np.asarray([J/r['peak_a'] for r in h])
    if np.any(fractions<.05) or np.any(fractions>.10):return None,{'failure':'actual J/peak outside 5-10%','range':fractions.tolist()}
    power=float(metrics['charge_a_s'].sum()/metrics['elapsed_s'])
    f=np.r_[(end-z)/SCALE[:11],(power-250.)/250.]
    return f,dict(history=h,end=end,power_w=power,fraction_range=fractions.tolist())

def main():
    p=argparse.ArgumentParser();p.add_argument('seed_log',type=Path);p.add_argument('--inductance-nh',type=float,required=True)
    p.add_argument('--initial-j-a',type=float,required=True);p.add_argument('--iterations',type=int,default=10);args=p.parse_args()
    q=np.r_[load_state(args.seed_log),args.initial_j_a];f,m=evaluate(q,args.inductance_nh)
    if f is None:raise ValueError(str(m))
    ridge=1e-7;print('initial norm',np.linalg.norm(f),'power W',m['power_w'],'fraction range',m['fraction_range'],flush=True)
    for it in range(args.iterations):
        cols=[]
        for k in range(12):
            eps=1e-6 if k<7 else 1e-4
            qp=q.copy();qm=q.copy();qp[k]+=eps;qm[k]-=eps
            fp,mp=evaluate(qp,args.inductance_nh);fm,mm=evaluate(qm,args.inductance_nh)
            if fp is not None and fm is not None:col=(fp-fm)/(2*eps/SCALE[k])
            elif fp is not None:col=(fp-f)/(eps/SCALE[k])
            elif fm is not None:col=(f-fm)/(eps/SCALE[k])
            else:raise RuntimeError(f'no feasible derivative coordinate {k}')
            cols.append(col)
        jac=np.column_stack(cols);d=np.linalg.solve(jac.T@jac+ridge*np.eye(12),-jac.T@f)*SCALE
        ratio=max(1.,np.max(abs(d[:7]))/.02,np.max(abs(d[7:11]))/1.,abs(d[11])/.1);d/=ratio
        accepted=False
        for pwr in range(11):
            damping=2.**(-pwr);ft,mt=evaluate(q+damping*d,args.inductance_nh)
            if ft is None:
                print('iteration',it,'damping',damping,'failure',mt['failure'],flush=True);continue
            if np.linalg.norm(ft)<np.linalg.norm(f):
                q,f,m=q+damping*d,ft,mt;ridge=max(1e-14,ridge/3);accepted=True
                print('iteration',it,'norm',np.linalg.norm(f),'J A',q[11],'power W',m['power_w'],
                      'fraction pct',[100*x for x in m['fraction_range']],flush=True);break
        if not accepted:
            ridge*=10;print('STOP no accepted step; ridge',ridge,flush=True);break
    print(json.dumps(dict(fixed_slot_power_candidate=True,state=q[:11].tolist(),negative_target_a=float(q[11]),
      inductance_nh=args.inductance_nh,normalized_residual=f.tolist(),power_w=m['power_w'],
      fraction_range=m['fraction_range'],events=m['history'])),flush=True)
    print('No periodic/stability/startup/paper reproduction is certified.',flush=True)

if __name__=='__main__':main()
