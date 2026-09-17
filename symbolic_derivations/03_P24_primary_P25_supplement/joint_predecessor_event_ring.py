"""Tagged candidate-state diagnostic with hard event/slot checks.

P24 stage/P25 sequence extension; original constant-Coss numerical reverse
fixture. No SPICE or edits to old experiments. Start at H2 from saved RAW,
so altered states are not proven reachable from previous H1 or periodic.
"""
import numpy as np
from scipy.integrate import quad_vec
from spicelib import RawRead
from continuous_h2_to_h3 import advance
from finite_resistance_interval import ROOT,START,TON

NP=4
J=11.25
ALL_LOW=np.array([False]*NP+[True]*NP)

def event(component,level,direction,terminal=True):
    def f(ns,z):return z[component]-level
    f.direction=direction;f.terminal=terminal
    return f

def vhigh(z,k):
    return [48-z[0],z[0]-z[1],z[1]-z[2],z[2]-z[6]][k]

def seed_from_raw():
    raw=RawRead(str(ROOT/'experiments/track_A_periodic_steady_state/A37_solver_work/iter_001.raw'))
    t=np.real(raw.get_trace('time').get_wave(0))
    names=[f'V(xmod:{n})' for n in ['a1','a2','a3','x1','x2','x3','x4']]
    names += [f'I(XMOD:LIND{k})' for k in range(1,NP+1)]
    return np.array([np.interp(START,t,np.real(raw.get_trace(n).get_wave(0))) for n in names])

def ring(seed,di3=14.25,di4=0.,max_handoffs=4,di1=0.,di2=0.,metrics=None,origin=START,tolerances=None,window_extension_ns=None,
         negative_target=J,ton=TON,low_policy='p25_all_inactive'):
    if low_policy not in ['p25_all_inactive','p24_adjacent_literal']:
        raise ValueError('unknown low-side policy')
    z=seed.copy();z[7]+=di1;z[8]+=di2;z[9]+=di3;z[10]+=di4
    initial=z.copy();now=origin;k=1;history=[]
    def propagate(*args,segment=None):
        sol=advance(*args,**(tolerances or {}))
        if metrics is not None:
            charge,_=quad_vec(lambda ns:sol.sol(ns)[7:],sol.t[0],sol.t[-1],epsabs=1e-7,epsrel=1e-9)
            metrics['charge_a_s']=metrics.get('charge_a_s',np.zeros(4))+charge*1e-9
            metrics['elapsed_s']=metrics.get('elapsed_s',0.)+(sol.t[-1]-sol.t[0])*1e-9
            if segment is not None:
                metrics.setdefault('segments',[]).append(dict(name=segment,
                    start_ns=float(sol.t[0]),end_ns=float(sol.t[-1]),
                    duration_ns=float(sol.t[-1]-sol.t[0]),charge_a_ns=charge.tolist(),
                    start_state=np.asarray(args[2]).tolist(),end_state=sol.y[:,-1].tolist()))
        return sol
    for handoff in range(max_handoffs):
        nxt=(k+1)%NP
        if low_policy=='p25_all_inactive':
            active=ALL_LOW.copy();active[k]=True;active[NP+k]=False
        else:
            active=np.zeros(2*NP,dtype=bool);active[k]=True;active[NP+nxt]=True
        s=propagate(now,now+ton,z,active,segment=f'H{k+1}_on')
        now=s.t[-1]*1e-9;z=s.y[:,-1]
        record=dict(active_phase=k+1,high_off_ns=now*1e9,peak_a=float(z[7+k]))
        active[k]=False
        s=propagate(now,now+1e-9,z,active,event(3+k,0,-1),segment=f'H{k+1}_off_commutation')
        if not len(s.t_events[0]):
            record['failure']='low-side zero absent';history.append(record);return history,z,initial
        now=s.t[-1]*1e-9;z=s.y[:,-1]
        record.update(low_on_ns=now*1e9,next_phase=nxt+1,next_entry_a=float(z[7+nxt]))
        # Preserve hard paper-event entrance contract, unlike old level skip.
        if z[7+nxt]<0:
            record['failure']='next-current already negative at M3 entry';history.append(record);return history,z,initial
        slot=(100+50*handoff)*1e-9
        if low_policy=='p25_all_inactive':freewheel=ALL_LOW
        else:
            freewheel=np.zeros(2*NP,dtype=bool);freewheel[NP+k]=True;freewheel[NP+nxt]=True
        s=propagate(now,slot,z,freewheel,event(7+nxt,-negative_target,-1),segment=f'L{nxt+1}_freewheel_to_target')
        if not len(s.t_events[0]):
            record['failure']='negative target absent before slot';history.append(record);return history,s.y[:,-1],initial
        now=s.t[-1]*1e-9;z=s.y[:,-1]
        record['release_ns']=now*1e9
        active=freewheel.copy();active[NP+nxt]=False
        def hz(ns,q):return vhigh(q,nxt)
        hz.direction=-1;hz.terminal=False
        release_state=z.copy();release_time=now
        s=propagate(now,slot,z,active,hz,segment=f'L{nxt+1}_off_to_fixed_slot')
        z=s.y[:,-1];now=slot
        zeros=s.t_events[0].tolist()
        record.update(slot_ns=slot*1e9,vds_slot_v=float(vhigh(z,nxt)),
                      natural_zero_ns=zeros,next_current_slot_a=float(z[7+nxt]))
        if window_extension_ns is not None:
            # Independent counterfactual hold-off audit. Never used to advance
            # the real ring, integrate its charge, or alter a gate decision.
            def exit_zero(ns,q):return vhigh(q,nxt)
            exit_zero.direction=1;exit_zero.terminal=False
            probe=advance(release_time,slot+window_extension_ns*1e-9,
                          release_state,active,
                          [exit_zero,event(7+nxt,0,1,False)],**(tolerances or {}))
            record['hold_off_probe']=dict(
                extension_ns=float(window_extension_ns),
                positive_vds_crossings_ns=probe.t_events[0].tolist(),
                current_up_zero_ns=probe.t_events[1].tolist())
        history.append(record)
        if vhigh(z,nxt)>0:
            record['failure']='high-side Vds positive at fixed slot';return history,z,initial
        k=nxt
    return history,z,initial

def main():
    seed=seed_from_raw();passed=[]
    for d4 in np.arange(7.,10.001,.25):
        hist,z,initial=ring(seed,di4=float(d4))
        print('delta i4 A',d4,'history',hist,flush=True)
        if len(hist)>=3 and 'failure' not in hist[1]:passed.append((d4,hist,z,initial))
    print('sampled H3/H4 passing delta i4 A',[float(p[0]) for p in passed])
    for d4,hist,z,initial in passed:
        print('partial candidate',d4,'last reached phase',hist[-1]['active_phase'],
              'failure',hist[-1].get('failure'),'all handoffs passed?',len(hist)==4 and 'failure' not in hist[-1],flush=True)
    assert not any(len(h)==4 and 'failure' not in h[-1] for _,h,_,_ in passed), 'investigate any unexpected complete local ring success'
    print('hard sequence/actual voltage checks retained; no periodic success declared')

if __name__=='__main__':main()
