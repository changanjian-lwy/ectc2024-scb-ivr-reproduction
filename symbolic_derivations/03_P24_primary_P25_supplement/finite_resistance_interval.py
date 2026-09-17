"""Full node KCL with the EXISTING fixture's linear switches/reverse paths.

Not manufacturer GaN physics: reverse path Vf=0/Ron=1m is a numerical
idealization from the old library. No new SPICE or netlist edits.
"""
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from spicelib import RawRead
from full_matrix_interval_propagator import C,B,L,VO,NP

ROOT=Path(__file__).resolve().parents[2]
RH=.007
RL=.0035
RD=.001
RIND=1e-6
ROFF=1e12
VIN=48.
START=50.000746466e-9
TON=NP*VO/VIN*200e-9
# A row's positive voltage is D-S; reverse current is negative.
G=np.zeros((8,7));offset=np.zeros(8)
G[0,0]=-1;offset[0]=VIN
G[1,0]=1;G[1,1]=-1
G[2,1]=1;G[2,2]=-1
G[3,2]=1;G[3,6]=-1
G[4:,3:]=np.eye(4)
on=np.array([False,True,False,False,True,False,True,True])
RON=np.array([RH]*4+[RL]*4)
CI=np.linalg.solve(C,np.eye(7))

def branch(z,reverse,active=on):
    v=G@z[:7]+offset
    conduct=np.where(active,1/RON,1/ROFF)
    if reverse: conduct=conduct+np.where(v<0,1/RD,1/ROFF)
    return conduct*v,conduct

def rhs(ns,z,reverse,active=on):
    currents,_=branch(z,reverse,active)
    return 1e-9*np.r_[CI@(-B@z[7:]-G.T@currents),
                       (B.T@z[:7]-VO-RIND*z[7:])/L]

def jac(ns,z,reverse,active=on):
    _,conduct=branch(z,reverse,active)
    return 1e-9*np.block([[-CI@G.T@np.diag(conduct)@G,-CI@B],
                          [B.T/L,-np.eye(4)*RIND/L]])

def main():
    raw=RawRead(str(ROOT/'experiments/track_A_periodic_steady_state/A37_solver_work/iter_001.raw'))
    t=np.real(raw.get_trace('time').get_wave(0))
    names=[f'V(xmod:{n})' for n in ['a1','a2','a3','x1','x2','x3','x4']]
    names += [f'I(XMOD:LIND{k})' for k in range(1,5)]
    waves=np.array([np.real(raw.get_trace(n).get_wave(0)) for n in names])
    def sample(when):return np.array([np.interp(when,t,w) for w in waves])
    z0=sample(START); saved_end=sample(START+TON)
    for reverse,label in [(False,'Ron-only diagnostic; reverse branches omitted'),
                          (True,'Ron + original numerical reverse branches')]:
        sol=solve_ivp(lambda s,z:rhs(s,z,reverse),(0.,TON*1e9),z0,
                      method='Radau',jac=lambda s,z:jac(s,z,reverse),
                      rtol=1e-9,atol=1e-9,dense_output=True)
        if not sol.success:raise RuntimeError(sol.message)
        end=sol.y[:,-1]
        points=np.linspace(0.,TON*1e9,501)
        pred=sol.sol(points)
        saved=np.column_stack([sample(START+p*1e-9) for p in points])
        print(label,'solver points',len(sol.t))
        print('end currents A',end[7:].tolist(),'saved',saved_end[7:].tolist())
        print('end current errors A',(end[7:]-saved_end[7:]).tolist())
        print('end X2 V',end[4],'saved',saved_end[4])
        if reverse:
            f1=end[0]-end[3];f2=end[1]-end[4];vh2=end[0]-end[1]
            print('end X2 voltage budget: F1-F2',f1-f2,'X1',end[3],
                  'minus VdsH2',vh2,'sum',(f1-f2)+end[3]-vh2)
        print('sampled max node error V',np.max(abs(pred[:7]-saved[:7])),
              'max current error A',np.max(abs(pred[7:]-saved[7:])))
        print('fly voltage changes V',((end[:3]-end[3:6])-(z0[:3]-z0[3:6])).tolist())
        dz=rhs(TON*1e9,end,reverse)/1e-9
        currents,_=branch(end,reverse)
        residual=C@dz[:7]+B@end[7:]+G.T@currents
        print('KCL residual max A',np.max(abs(residual)))
        assert np.max(abs(residual))<1e-5
        if reverse:
            assert np.max(abs(end[7:]-saved_end[7:]))<.05, 'old waveform endpoint mismatch'
    # Polarity trap: negative Vds must yield negative reverse current.
    z=z0.copy();z[3]=-.1
    current,_=branch(z,True)
    assert current[4]<-100.,'reverse-polarity trap'
    # Separately audit H2 OFF until first low-side zero; no low-gate advance.
    gh=np.real(raw.get_trace('V(xmod:gh2)').get_wave(0))
    js=np.flatnonzero((gh[:-1]>=2.5)&(gh[1:]<2.5));k=int(js[0])
    off_start=t[k]+(2.5-gh[k])/(gh[k+1]-gh[k])*(t[k+1]-t[k])
    active=on.copy();active[1]=False
    def zero(ns,z):return z[4]
    zero.terminal=True;zero.direction=-1
    off=solve_ivp(lambda s,z:rhs(s,z,True,active),(0.,1.),sample(off_start),
                  method='Radau',jac=lambda s,z:jac(s,z,True,active),
                  events=zero,rtol=1e-9,atol=1e-9)
    if not off.success or not len(off.t_events[0]):raise RuntimeError('low-side zero not reached')
    ns=float(off.t_events[0][0]); end=off.y_events[0][0]
    x2=waves[4];idx=np.flatnonzero((t[:-1]>=off_start)&(x2[:-1]>0)&(x2[1:]<=0));k=int(idx[0])
    saved_zero=t[k]+(0-x2[k])/(x2[k+1]-x2[k])*(t[k+1]-t[k])
    print('H2 OFF first X2=0: calculated absolute ns',(off_start+ns*1e-9)*1e9,
          'saved ns',saved_zero*1e9,'error ps',(off_start+ns*1e-9-saved_zero)*1e12)
    print('OFF event currents A',end[7:].tolist(),'saved',sample(saved_zero)[7:].tolist())
    assert abs(off_start+ns*1e-9-saved_zero)<5e-12,'OFF zero event time mismatch'
    print('KCL, old endpoint agreement, reverse-polarity tests passed')

if __name__=='__main__':main()
