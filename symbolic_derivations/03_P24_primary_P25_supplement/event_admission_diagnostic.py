"""Separate variable-period event-admission diagnostic, not native P24/P25.

P25 Table IV motivates timing freedom; the concrete state machine remains
our implementation. No fixed-slot benchmark is changed. All states advance
continuously; each handoff requires actual Vds zero and next-current order.
"""
import argparse,ast,json
from pathlib import Path
import numpy as np
from scipy.integrate import quad_vec
from joint_predecessor_event_ring import NP,J,ALL_LOW,event,vhigh
from continuous_h2_to_h3 import advance
from finite_resistance_interval import TON

def main():
    p=argparse.ArgumentParser();p.add_argument('candidate_log',type=Path,nargs='?')
    p.add_argument('--seed-json')
    p.add_argument('--handoffs',type=int,default=40)
    p.add_argument('--tolerance',type=float,default=1e-9)
    p.add_argument('--trace-next-zero',action='store_true')
    p.add_argument('--ton-ns',type=float)
    p.add_argument('--negative-target-a',type=float)
    p.add_argument('--inductance-nh',type=float)
    p.add_argument('--strict-all-other-positive',action='store_true');args=p.parse_args()
    if args.seed_json:
        if args.candidate_log:p.error('choose a log or JSON seed, not both')
        z=np.array(json.loads(args.seed_json),dtype=float)
    else:
        if args.candidate_log is None:p.error('candidate log or JSON seed required')
        line=next(x for x in args.candidate_log.read_text().splitlines() if x.startswith('retained state '))
        z=np.array(ast.literal_eval(line.split('retained state ')[1].split(' physical residual')[0]))
    if z.shape!=(11,) or not np.all(np.isfinite(z)) or vhigh(z,1)>0:
        raise ValueError('invalid original-guard seed')
    ton=TON if args.ton_ns is None else args.ton_ns*1e-9
    target=J if args.negative_target_a is None else args.negative_target_a
    if not 0<ton<50e-9 or target<=0:p.error('invalid diagnostic timing/current target')
    if args.inductance_nh is not None:
        if args.inductance_nh<=0:p.error('inductance must be positive')
        # Process-local parameter plug-in; both rhs and jac use this module
        # global. No source constant or old fixture is overwritten.
        import finite_resistance_interval as model
        model.L=args.inductance_nh*1e-9
    print('case Ton ns',ton*1e9,'negative target A',target,
          'inductance override nH',args.inductance_nh,flush=True)
    now=50e-9;k=1;cycle_start=now;cycle_state=z.copy();charge=np.zeros(4)
    def prop(end,active,ev=None):
        nonlocal now,z,charge
        s=advance(now,end,z,active,ev,rtol=args.tolerance,atol=args.tolerance)
        q,_=quad_vec(lambda ns:s.sol(ns)[7:],s.t[0],s.t[-1],epsabs=1e-7,epsrel=1e-9)
        charge+=q*1e-9;now=s.t[-1]*1e-9;z=s.y[:,-1]
        return s
    for handoff in range(args.handoffs):
        active=ALL_LOW.copy();active[k]=True;active[NP+k]=False
        prop(now+ton,active)
        row=dict(handoff=handoff,active_phase=k+1,high_off_ns=now*1e9,peak_a=float(z[7+k]))
        row['J_to_active_peak_pct']=100*target/row['peak_a']
        row['all_currents_high_off_a']=z[7:].tolist()
        nxt=(k+1)%NP
        active[k]=False
        ev=event(3+k,0,-1)
        if args.trace_next_zero:ev=[ev,event(7+nxt,0,-1,False)]
        s=prop(now+1e-9,active,ev)
        if args.trace_next_zero:
            row['next_zero_during_high_off_commutation_ns']=s.t_events[1].tolist()
        if not len(s.t_events[0]):
            row['failure']='low-side zero absent within 1ns diagnostic horizon';print(json.dumps(row));break
        row.update(low_on_ns=now*1e9,next_phase=nxt+1,next_entry_a=float(z[7+nxt]))
        row['all_currents_m3_a']=z[7:].tolist()
        if z[7+nxt]<0:
            row['failure']='next-current already negative at M3 entry';print(json.dumps(row));break
        s=prop(now+200e-9,ALL_LOW,event(7+nxt,-target,-1))
        if not len(s.t_events[0]):
            row['failure']='negative target absent within 200ns diagnostic horizon';print(json.dumps(row));break
        row['release_ns']=now*1e9
        row['all_currents_release_a']=z[7:].tolist()
        if args.strict_all_other_positive and any(z[7+j]<0 for j in range(NP) if j!=nxt):
            row['failure']='another phase current negative at next-low release (four-phase extension contract)'
            print(json.dumps(row),flush=True);break
        active=ALL_LOW.copy();active[NP+nxt]=False
        def hz(ns,q):return vhigh(q,nxt)
        hz.direction=-1;hz.terminal=True
        s=prop(now+5e-9,active,hz)
        if not len(s.t_events[0]):
            row['failure']='high-side zero absent within 5ns diagnostic horizon';print(json.dumps(row));break
        if abs(vhigh(z,nxt))>1e-8:
            raise RuntimeError('root residual exceeds numerical diagnostic threshold')
        row.update(next_high_on_ns=now*1e9,next_vds_v=float(vhigh(z,nxt)),
                   next_current_a=float(z[7+nxt]))
        print(json.dumps(row),flush=True);k=nxt
        if (handoff+1)%NP==0:
            duration=now-cycle_start
            print(json.dumps(dict(completed_ring=(handoff+1)//NP,period_ns=duration*1e9,
                                  end_state=z.tolist(),
                                  frequency_mhz=1e-6/duration,node_return_v=(z-cycle_state)[:7].tolist(),
                                  current_return_a=(z-cycle_state)[7:].tolist(),
                                  converter_power_at_ideal_1v_w=float(charge.sum()/duration))),flush=True)
            cycle_start=now;cycle_state=z.copy();charge=np.zeros(4)
    print('No fixed 5MHz, equal phase spacing, 250W, native-paper control, or startup success is claimed.')

if __name__=='__main__':main()
