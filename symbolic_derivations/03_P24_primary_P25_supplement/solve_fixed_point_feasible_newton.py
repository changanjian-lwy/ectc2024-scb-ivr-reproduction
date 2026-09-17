"""Bounded feasible Newton diagnostic for the full 11-state return map.

No gate override, no relaxation of current-order/ZVS, no old file edits.
Mathematical phase origin is exactly 50ns -> 250ns (200ns). The old RAW
is a seed only; its 50.000746ns sampling timestamp is not the map origin.
State variables are all 7 node voltages + 4 currents, not forced fly levels.
Scales 12V/125A describe a numerical norm, not paper acceptance limits.
"""
import numpy as np
import argparse
from joint_predecessor_event_ring import ring,seed_from_raw,vhigh,J
import finite_resistance_interval as interval_model

SCALE=np.r_[np.full(7,12.),np.full(4,125.)]
CALLS=0

def evaluate(z,inductance_nh=None,negative_target=None):
    global CALLS
    CALLS+=1
    if vhigh(z,1)>0:
        return None,{'failure':'initial H2 voltage not compatible with zero-voltage admission'}
    old_l=interval_model.L
    try:
        if inductance_nh is not None:interval_model.L=inductance_nh*1e-9
        h,end,_=ring(z,di1=0.,di2=0.,di3=0.,di4=0.,origin=50e-9,
                     negative_target=(J if negative_target is None else negative_target))
    finally:
        interval_model.L=old_l
    if len(h)!=4 or 'failure' in h[-1]:return None,h[-1]
    return (end-z)/SCALE,dict(history=h,end=end)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--iterations',type=int,default=3)
    parser.add_argument('--damping-powers',type=int,default=5)
    parser.add_argument('--adaptive-jacobian',action='store_true')
    args=parser.parse_args()
    z=seed_from_raw();z[7:]+=np.array([-8.,-1.,14.25,8.25])
    f,meta=evaluate(z)
    if f is None:raise RuntimeError(str(meta))
    print('exact200ns initial norm',float(np.linalg.norm(f)),'physical residual',(f*SCALE).tolist(),flush=True)
    for iteration in range(args.iterations):
        cols=[]
        for k in range(11):
            eps=1e-6 if k<7 else 1e-4
            options=[eps] if not args.adaptive_jacobian else [eps,-eps,eps*.1,-eps*.1,eps*.01,-eps*.01]
            derivative=None
            for perturb in options:
                trial=z.copy();trial[k]+=perturb
                fk,m=evaluate(trial)
                if fk is not None:
                    derivative=(fk-f)/(perturb/SCALE[k]);break
            if derivative is None:
                print('Jacobian perturbation infeasible',k,m,'retained norm',float(np.linalg.norm(f)),
                      'retained physical residual',(f*SCALE).tolist(),flush=True);return
            if perturb!=eps:print('feasible one-sided derivative coordinate',k,'step',perturb,flush=True)
            cols.append(derivative)
        jac=np.column_stack(cols)
        step,_,rank,s=np.linalg.lstsq(jac,-f,rcond=1e-10)
        step=step*SCALE
        # Limit full step length, not physics/variable values. Do not clamp
        # individual states to create an artificial solution.
        ratio=max(np.max(abs(step[:7]))/.25,np.max(abs(step[7:]))/1.,1.)
        step/=ratio
        print('iteration',iteration,'rank',rank,'singular range',float(s[0]),float(s[-1]),
              'trust-scaled physical Newton step',step.tolist(),flush=True)
        accepted=False
        for damping in [2.**(-p) for p in range(args.damping_powers+1)]:
            trial=z+damping*step
            fk,m=evaluate(trial)
            if fk is None:
                print('damping',damping,'infeasible',m,flush=True);continue
            norm=float(np.linalg.norm(fk))
            print('damping',damping,'feasible norm',norm,flush=True)
            if norm<np.linalg.norm(f):
                z,f,meta=trial,fk,m;accepted=True;break
        if not accepted:
            print('STOP: no feasible residual-reducing Newton step; not a proof of no fixed point',flush=True);break
    print('evaluation count',CALLS,'final state',z.tolist(),'physical residual',(f*SCALE).tolist(),
          'final numerical norm',float(np.linalg.norm(f)),flush=True)
    print('NOT converged/periodic; no peak/power acceptance declared')

if __name__=='__main__':main()
