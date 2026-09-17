"""Independent initial-state candidates, NOT edits to old model or a periodic solve.

Only perturb i3 at H2 admission. Same 9% control/device constants. All later
states continuous. A candidate passing H3 remains unproven reachable from H1.
"""
import numpy as np
from spicelib import RawRead
from continuous_h2_to_h3 import advance
from finite_resistance_interval import ROOT,START,TON,on

J=11.25
ALL_LOW=np.array([False]*4+[True]*4)

def event(component,level,direction,terminal=True):
    def f(ns,z):return z[component]-level
    f.direction=direction;f.terminal=terminal
    return f

def trial(seed,delta):
    z=seed.copy();z[9]+=delta
    s=advance(START,START+TON,z,on)
    peak=s.y[8,-1];now=s.t[-1]*1e-9;z=s.y[:,-1]
    active=on.copy();active[1]=False
    s=advance(now,now+1e-9,z,active,event(4,0,-1))
    now=s.t[-1]*1e-9;z=s.y[:,-1];entry=z[9]
    s=advance(now,105e-9,z,ALL_LOW,event(9,-J,-1))
    if not len(s.t_events[0]):return dict(delta=delta,status='negative target absent')
    release=s.t[-1]*1e-9;z=s.y[:,-1]
    if release>=100e-9:return dict(delta=delta,status='release after deadline',release_ns=release*1e9,entry=entry)
    active=ALL_LOW.copy();active[6]=False
    def hz(ns,q):return q[1]-q[2]
    hz.direction=-1;hz.terminal=False
    s=advance(release,100e-9,z,active,hz)
    z100=s.y[:,-1];vds=z100[1]-z100[2]
    first=s.t_events[0][0] if len(s.t_events[0]) else None
    return dict(delta=delta,entry=float(entry),peak_h2=float(peak),release_ns=release*1e9,
                first_h3zero_ns=first,vds100=float(vds),i3at100=float(z100[9]),
                status='candidate H3 pass' if entry>=0 and vds<=0 else 'H3 fail',state100=z100)

def main():
    raw=RawRead(str(ROOT/'experiments/track_A_periodic_steady_state/A37_solver_work/iter_001.raw'))
    t=np.real(raw.get_trace('time').get_wave(0))
    names=[f'V(xmod:{n})' for n in ['a1','a2','a3','x1','x2','x3','x4']]
    names += [f'I(XMOD:LIND{k})' for k in range(1,5)]
    seed=np.array([np.interp(START,t,np.real(raw.get_trace(n).get_wave(0))) for n in names])
    results=[]
    for d in np.arange(12.,15.001,.25):
        ans=trial(seed,float(d));results.append(ans)
        print({k:v for k,v in ans.items() if k!='state100'})
    passed=[r for r in results if r['status']=='candidate H3 pass']
    if not passed:
        print('No sampled candidate passes; do not force gate or reset nodes.');return
    ans=passed[len(passed)//2]
    print('Continue middle sampled candidate delta i3 A',ans['delta'],'not periodic/reachable proof')
    active=ALL_LOW.copy();active[2]=True;active[6]=False
    s=advance(100e-9,100e-9+TON,ans['state100'],active)
    print('H3 turn-off current A',s.y[9,-1])
    now=s.t[-1]*1e-9;z=s.y[:,-1];active[2]=False
    s=advance(now,now+1e-9,z,active,event(5,0,-1))
    now=s.t[-1]*1e-9;z=s.y[:,-1]
    print('H3 low ZVS ns',now*1e9,'phase4 entry current A',z[10])
    s=advance(now,150e-9,z,ALL_LOW,event(10,-J,-1))
    if not len(s.t_events[0]):print('phase4 negative target absent before150');return
    now=s.t[-1]*1e-9;z=s.y[:,-1];active=ALL_LOW.copy();active[7]=False
    def h4zero(ns,q):return q[2]-q[6]
    h4zero.direction=-1;h4zero.terminal=False
    s=advance(now,150e-9,z,active,h4zero)
    print('H4 natural zero events ns',s.t_events[0].tolist(),
          'H4 Vds at150 V',s.y[2,-1]-s.y[6,-1])
    assert ans['entry']>0 and ans['vds100']<=0
    print('H3 partial feasibility exists; whole-ring/peak/charge constraints NOT passed')

if __name__=='__main__':main()
