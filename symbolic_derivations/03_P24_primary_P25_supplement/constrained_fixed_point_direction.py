"""Constrained local Gauss-Newton diagnostic; no physical-boundary relaxation.

QP uses original full return-map residual plus explicit timing/voltage/order
inequalities. Every trial is verified with the hard event simulator. This
does not imply global feasibility, stability, or target output power.
"""
import numpy as np
import argparse
import ast
from pathlib import Path
from scipy.optimize import minimize,LinearConstraint,Bounds
from solve_fixed_point_feasible_newton import evaluate,SCALE
from check_newton_retained_candidate import Z

def inequalities(z,meta):
    # All >=0. Timing scales are numerical only, not accepted paper margins.
    vals=[(z[1]-z[0])/12.]
    names=['initial H2 ZVS']
    for row in meta['history']:
        phase=row['next_phase']
        if not row['natural_zero_ns']:raise ValueError('no natural zero in an allegedly valid ring')
        vals.extend([row['next_entry_a']/125.,
                     (row['slot_ns']-row['natural_zero_ns'][0])/50.,
                     -row['vds_slot_v']/12.])
        names.extend([f'H{phase} previous M3 entry',f'H{phase} first-zero deadline',f'H{phase} actual ZVS'])
    return np.array(vals),names

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--iterations',type=int,default=4)
    parser.add_argument('--retain-margin-fraction',type=float,default=0.)
    parser.add_argument('--start-log',type=Path)
    parser.add_argument('--margin-reference-log',type=Path)
    parser.add_argument('--fixed-reference-margin',action='store_true')
    parser.add_argument('--minimum-zero-lead-ps',type=float,default=0.)
    parser.add_argument('--trust-scale',type=float,default=1.)
    parser.add_argument('--planning-margin-fraction',type=float,default=0.)
    parser.add_argument('--max-node-return-mv',type=float)
    parser.add_argument('--node-planning-safety-mv',type=float,default=0.)
    parser.add_argument('--central-jacobian',action='store_true')
    parser.add_argument('--inductance-nh',type=float)
    parser.add_argument('--negative-target-a',type=float)
    parser.add_argument('--ron-scale',type=float,default=1.)
    args=parser.parse_args()
    if not 0<=args.retain_margin_fraction<1:
        parser.error('margin fraction must be in [0,1)')
    if args.minimum_zero_lead_ps<0:
        parser.error('minimum zero lead must be nonnegative')
    if not 0<args.trust_scale<=1:
        parser.error('trust scale must be in (0,1]')
    if args.planning_margin_fraction<0:
        parser.error('planning margin must be nonnegative')
    if args.max_node_return_mv is not None and args.max_node_return_mv<=0:
        parser.error('node return cap must be positive')
    if args.node_planning_safety_mv<0 or (args.max_node_return_mv is not None and args.node_planning_safety_mv>=args.max_node_return_mv):
        parser.error('node planning safety must be nonnegative and smaller than cap')
    if args.inductance_nh is not None and args.inductance_nh<=0:parser.error('inductance must be positive')
    if args.negative_target_a is not None and args.negative_target_a<=0:parser.error('negative target must be positive')
    if args.ron_scale<=0:parser.error('Ron scale must be positive')
    import finite_resistance_interval as interval_model
    interval_model.RON=interval_model.RON*args.ron_scale
    def do_evaluate(q):return evaluate(q,inductance_nh=args.inductance_nh,
                                        negative_target=args.negative_target_a)
    z=Z.copy()
    if args.start_log:
        line=next(x for x in args.start_log.read_text().splitlines()
                  if x.startswith('retained state '))
        z=np.array(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
        if z.shape!=(11,) or not np.all(np.isfinite(z)):
            raise ValueError('invalid retained 11-state candidate')
        print('starting candidate source',str(args.start_log),flush=True)
    f,meta=do_evaluate(z)
    if f is None:raise RuntimeError(str(meta))
    print('start norm',np.linalg.norm(f),'physical residual',(f*SCALE).tolist(),flush=True)
    print('model profile inductance nH',args.inductance_nh,'negative target A',args.negative_target_a,
          'Ron scale',args.ron_scale,flush=True)
    print('algorithmic margin retention fraction',args.retain_margin_fraction,
          'not a paper driver-delay requirement',flush=True)
    reference_g,_=inequalities(z,meta)
    if args.margin_reference_log:
        line=next(x for x in args.margin_reference_log.read_text().splitlines()
                  if x.startswith('retained state '))
        zr=np.array(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
        if zr.shape!=(11,) or not np.all(np.isfinite(zr)):
            raise ValueError('invalid reference candidate')
        fr,mr=do_evaluate(zr)
        if fr is None:raise ValueError('reference violates original ring boundaries')
        reference_g,_=inequalities(zr,mr)
        print('fixed margin reference source',str(args.margin_reference_log),flush=True)
    fixed_floor=args.retain_margin_fraction*np.maximum(reference_g,0.)
    print('fixed reference margin',args.fixed_reference_margin,flush=True)
    print('algorithmic minimum first-zero lead ps',args.minimum_zero_lead_ps,
          'not an actual driver requirement or full-window constraint',flush=True)
    print('local trust-bound scale',args.trust_scale,flush=True)
    print('linear planning safety fraction',args.planning_margin_fraction,
          'actual acceptance floor unchanged',flush=True)
    print('algorithmic max-node-return mV',args.max_node_return_mv,
          'not a paper tolerance',flush=True)
    print('linear node planning safety mV',args.node_planning_safety_mv,flush=True)
    print('central finite differences when both probes valid',args.central_jacobian,flush=True)
    for iteration in range(args.iterations):
        g,names=inequalities(z,meta);cols=[];gcols=[]
        # Preserve a fraction of current slack, not an invented physical delay.
        floor=(fixed_floor if args.fixed_reference_margin else
               args.retain_margin_fraction*np.maximum(g,0.))
        floor=floor.copy()
        floor[2::3]=np.maximum(floor[2::3],args.minimum_zero_lead_ps/50000.)
        planned_floor=floor+args.planning_margin_fraction*np.maximum(floor,np.maximum(reference_g,0.))
        for k in range(11):
            eps=1e-6 if k<7 else 1e-4
            ok=False
            if args.central_jacobian:
                plus=z.copy();plus[k]+=eps;minus=z.copy();minus[k]-=eps
                fp,mp=do_evaluate(plus);fm,mm=do_evaluate(minus)
                if fp is not None and fm is not None:
                    gp,_=inequalities(plus,mp);gm,_=inequalities(minus,mm)
                    cols.append((fp-fm)/(2*eps/SCALE[k]))
                    gcols.append((gp-gm)/(2*eps/SCALE[k]));ok=True
            if ok:continue
            for delta in [eps,-eps,eps*.1,-eps*.1]:
                trial=z.copy();trial[k]+=delta
                fk,m=do_evaluate(trial)
                if fk is not None:
                    gi,_=inequalities(trial,m)
                    cols.append((fk-f)/(delta/SCALE[k]))
                    gcols.append((gi-g)/(delta/SCALE[k]));ok=True;break
            if not ok:
                print('STOP derivative unavailable inside feasible domain',k,flush=True);return
        jac=np.column_stack(cols);a=np.column_stack(gcols)
        bound=args.trust_scale*np.r_[np.full(7,.1/12),np.full(4,.5/125)]
        ridge=1e-7
        def obj(d):return .5*np.sum((f+jac@d)**2)+.5*ridge*np.sum(d*d)
        def grad(d):return jac.T@(f+jac@d)+ridge*d
        constraints=[LinearConstraint(a,planned_floor-g,np.inf)]
        if args.max_node_return_mv is not None:
            cap=(args.max_node_return_mv-args.node_planning_safety_mv)*1e-3/SCALE[:7]
            constraints.append(LinearConstraint(jac[:7],-cap-f[:7],cap-f[:7]))
        qp=minimize(obj,np.zeros(11),jac=grad,method='SLSQP',
                    bounds=Bounds(-bound,bound),constraints=constraints,
                    options=dict(ftol=1e-13,maxiter=300))
        if not qp.success:
            print('STOP local QP failed',qp.message,flush=True);break
        direction=qp.x
        print('iteration',iteration,'QP predicted norm',np.linalg.norm(f+jac@direction),
              'physical step',(direction*SCALE).tolist(),'active predicted constraints',
              [names[k] for k,v in enumerate(g+a@direction) if v<1e-7],flush=True)
        # A constrained direction is still only a local linear approximation.
        accepted=False
        for p in range(13):
            damping=2.**(-p);trial=z+damping*direction*SCALE
            fk,m=do_evaluate(trial)
            if fk is None:
                print('damping',damping,'hard failure',m.get('failure'),flush=True);continue
            gt,_=inequalities(trial,m)
            if args.max_node_return_mv is not None and np.max(abs(fk[:7]*SCALE[:7]))>args.max_node_return_mv*1e-3:
                print('damping',damping,'algorithmic node-return rejection',
                      'max mV',np.max(abs(fk[:7]*SCALE[:7]))*1e3,flush=True);continue
            if np.any(gt<floor-1e-14):
                print('damping',damping,'algorithmic retained-margin rejection',
                      'constraints',[names[k] for k in np.flatnonzero(gt<floor-1e-14)],
                      'actual first-zero leads ps',(gt[2::3]*50000).tolist(),flush=True);continue
            if np.linalg.norm(fk)<np.linalg.norm(f)-1e-10:
                print('damping',damping,'accepted norm',np.linalg.norm(fk),flush=True)
                z,f,meta=trial,fk,m;accepted=True;break
        if not accepted:
            print('STOP no verified feasible improvement in tested direction',flush=True);break
    print('retained state',z.tolist(),'physical residual',(f*SCALE).tolist(),'norm',np.linalg.norm(f),flush=True)
    print('events',meta['history'],flush=True)
    print('local diagnostic only; periodic/power/stability not declared')

if __name__=='__main__':main()
