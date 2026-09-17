"""Continuous old-fixture ODE replay, only initial state from saved RAW.

Reproduces the old fixed-slot controller, flags sequence violations rather
than silently calling it a valid P25 cycle. No SPICE or parameter changes.
"""
import numpy as np
from scipy.integrate import solve_ivp
from spicelib import RawRead
from finite_resistance_interval import ROOT,START,TON,rhs,jac,on

J=.09*125

def advance(start,end,z,active,events=None,rtol=1e-9,atol=1e-9):
    sol=solve_ivp(lambda ns,q:rhs(ns,q,True,active),
                  (start*1e9,end*1e9),z,method='Radau',
                  jac=lambda ns,q:jac(ns,q,True,active),events=events,
                  rtol=rtol,atol=atol,dense_output=True)
    if not sol.success:raise RuntimeError(sol.message)
    return sol

def main():
    raw=RawRead(str(ROOT/'experiments/track_A_periodic_steady_state/A37_solver_work/iter_001.raw'))
    t=np.real(raw.get_trace('time').get_wave(0))
    names=[f'V(xmod:{n})' for n in ['a1','a2','a3','x1','x2','x3','x4']]
    names += [f'I(XMOD:LIND{k})' for k in range(1,5)]
    w=np.array([np.real(raw.get_trace(n).get_wave(0)) for n in names])
    def sample(ns):return np.array([np.interp(ns*1e-9,t,a) for a in w])
    z=sample(START*1e9)
    def i3zero(ns,q):return q[9]
    i3zero.direction=-1;i3zero.terminal=False
    s1=advance(START,START+TON,z,on,events=i3zero)
    now=s1.t[-1]*1e-9;z=s1.y[:,-1]
    print('continuous H2 ON end ns',now*1e9,'i2/i3 A',z[8],z[9])
    print('i3 zero during H2 ON ns',s1.t_events[0].tolist())
    active=on.copy();active[1]=False
    def x2zero(ns,q):return q[4]
    x2zero.direction=-1;x2zero.terminal=True
    s2=advance(now,now+1e-9,z,active,events=x2zero)
    if not len(s2.t_events[0]):raise RuntimeError('H2 low-side zero event missing')
    now=s2.t[-1]*1e-9;z=s2.y[:,-1]
    print('low2 ZVS admission ns',now*1e9,'i3 at entry A',z[9])
    entry_valid=bool(z[9]>=0)
    print('P25 next-current positive/zero-cross order entry valid?',entry_valid)
    # Old level-based rule enters M4 immediately if already below zero.
    # Continue only as a tagged diagnostic, not strict paper-sequence success.
    all_low=np.array([False]*4+[True]*4)
    def neg_target(ns,q):return q[9]+J
    neg_target.direction=-1;neg_target.terminal=True
    s3=advance(now,100e-9,z,all_low,events=neg_target)
    if not len(s3.t_events[0]):raise RuntimeError('negative target not reached')
    now=s3.t[-1]*1e-9;z=s3.y[:,-1]
    print('low3 release ns',now*1e9,'i3 A',z[9])
    active=all_low.copy();active[6]=False
    def h3zero(ns,q):return q[1]-q[2]
    h3zero.direction=-1;h3zero.terminal=False
    def i3_upzero(ns,q):return q[9]
    i3_upzero.direction=1;i3_upzero.terminal=False
    s4=advance(now,100e-9,z,active,events=[h3zero,i3_upzero])
    print('H3 downward Vds zero events ns',s4.t_events[0].tolist())
    print('subsequent i3 upward zero events ns',s4.t_events[1].tolist())
    z100=s4.y[:,-1];saved100=sample(100.)
    print('100ns VdsH3 calculated/saved V',z100[1]-z100[2],saved100[1]-saved100[2])
    print('100ns currents calculated A',z100[7:].tolist(),'saved',saved100[7:].tolist())
    print('100ns max node/current errors',np.max(abs(z100[:7]-saved100[:7])),np.max(abs(z100[7:]-saved100[7:])))
    print('100ns gate admissible?',bool(z100[1]-z100[2]<=0))
    assert not entry_valid,'regression: must flag already-negative M3 entry'
    assert len(s4.t_events[0])>0,'natural H3 zero must be reached'
    assert z100[1]-z100[2]>0,'regression: fixed-slot admission should fail'
    assert abs((z100[1]-z100[2])-(saved100[1]-saved100[2]))<.05
    print('sequence-violation/natural-zero/fixed-slot-failure checks passed')

if __name__=='__main__':main()
