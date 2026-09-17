"""Finite flying-capacitance ideal DAE propagation within a fixed mode.

No SPICE, no diode continuation past a clamp, no full-period claim.
"""
from pathlib import Path
import numpy as np
from scipy.linalg import null_space, expm
from scipy.optimize import brentq
from spicelib import RawRead
from audit_four_positions_existing_cases import A,BF,D

C=np.block([[A,-BF],[-BF.T,np.diag(D)]])
B=np.vstack([np.zeros((3,4)),np.eye(4)])
L=1.466666666666667e-9
VO=1.
VIN=48.
NP=4
NM_INSTANCE=1
ROOT=Path(__file__).resolve().parents[2]

class Interval:
    def __init__(self,y0,i0,high=None,free_low=1):
        if not 0<=free_low<NP: raise ValueError('explicit phase outside NP=4')
        rows=[]; rhs=[]
        for k in range(NP):
            if k!=free_low:
                row=np.zeros(7);row[3+k]=1;rows.append(row);rhs.append(0.)
        if high is not None:
            row=np.zeros(7)
            if high==0: row[0]=1; val=VIN
            elif high in [1,2]: row[high-1]=1;row[high]=-1;val=0.
            elif high==3: row[2]=1;row[6]=-1;val=0.
            else: raise ValueError('invalid high phase')
            rows.append(row);rhs.append(val)
        self.g=np.array(rows);self.b=np.array(rhs)
        self.n=null_space(self.g)
        self.yp=np.linalg.lstsq(self.g,self.b,rcond=None)[0]
        m=self.n.T@C@self.n
        q0=np.linalg.solve(m,self.n.T@C@(y0-self.yp))
        # C-metric projection is only an ideal boundary initialization; report
        # any jump. It is NOT physical hard-switching/charge loss simulation.
        self.jump=self.yp+self.n@q0-y0
        d=self.n.shape[1]
        self.k=np.zeros((d+5,d+5))
        self.k[:d,d:d+4]=-np.linalg.solve(m,self.n.T@B)
        self.k[d:d+4,:d]=B.T@self.n/L
        self.k[d:d+4,-1]=(B.T@self.yp-VO)/L
        self.z0=np.r_[q0,i0,1.]
        self.d=d
    def at(self,dt):
        z=expm(self.k*dt)@self.z0
        return self.yp+self.n@z[:self.d],z[self.d:self.d+4]
    def check(self,dt):
        z=expm(self.k*dt)@self.z0; dz=self.k@z
        y=self.yp+self.n@z[:self.d];i=z[self.d:self.d+4]
        projected=self.n.T@(C@self.n@dz[:self.d]+B@i)
        assert np.max(abs(projected))<1e-6, 'KCL residual'
        assert np.max(abs(self.g@y-self.b))<1e-8,'gate constraint residual'

def main():
    r=RawRead(str(ROOT/'experiments/track_A_periodic_steady_state/A37_solver_work/iter_001.raw'))
    t=np.real(r.get_trace('time').get_wave(0))
    def w(n): return np.real(r.get_trace(n).get_wave(0))
    def sample(when):
        yy=np.array([np.interp(when,t,w(f'V(xmod:{n})')) for n in ['a1','a2','a3','x1','x2','x3','x4']])
        ii=np.array([np.interp(when,t,w(f'I(XMOD:LIND{k})')) for k in range(1,5)])
        return yy,ii
    start=50.000746466e-9
    ton=NP*VO/VIN*200e-9
    y0,i0=sample(start)
    on=Interval(y0,i0,high=1,free_low=1)
    y1,i1=on.at(ton);ys,isaved=sample(start+ton)
    print('start/stop ns',start*1e9,(start+ton)*1e9)
    print('ideal initialization node projection V',on.jump.tolist())
    print('initial currents A',i0.tolist())
    print('full-matrix end currents A',i1.tolist(),'saved',isaved.tolist())
    print('end current differences A',(i1-isaved).tolist())
    print('flying delta V',((y1[:3]-y1[3:6])-(y0[:3]-y0[3:6])).tolist())
    print('ideal/saved final X2 V',y1[4],ys[4])
    print('saved flying delta V',((ys[:3]-ys[3:6])-(y0[:3]-y0[3:6])).tolist())
    # Saved node voltage explains saved current slope independently of our
    # ideal switch reduction. Include interpolated interval endpoints.
    mask=(t>start)&(t<start+ton)
    tt=np.r_[start,t[mask],start+ton]
    xx=np.r_[y0[4],w('V(xmod:x2)')[mask],ys[4]]
    ii=np.r_[i0[1],w('I(XMOD:LIND2)')[mask],isaved[1]]
    predicted=np.trapezoid(xx-VO-1e-6*ii,tt)/L
    print('saved mean X2 V',np.trapezoid(xx,tt)/ton,
          'saved delta I2 A',isaved[1]-i0[1],'KVL prediction A',predicted)
    assert abs(predicted-(isaved[1]-i0[1]))<.005,'saved interval KVL mismatch'
    on.check(ton)
    off=Interval(y1,i1,high=None,free_low=1)
    # Stop at the first X2=0 crossing; no extrapolation into reverse clamp.
    td=brentq(lambda dt:off.at(dt)[0][4],0.,1e-9,xtol=1e-20)
    y2,i2=off.at(td)
    off.check(td)
    print('ideal subsequent low-side zero delay ns',td*1e9,'current A',i2.tolist())
    print('off initialization jump V',off.jump.tolist())
    print('low-side event X2 V',y2[4])
    assert np.max(abs(off.jump))<1e-6,'opening switch must not create artificial voltage jump'
    # Deliberate wrong-state trap: removing a flying cross-term must fail
    # the ORIGINAL complete KCL, not just its own internally consistent model.
    z=expm(on.k*ton)@on.z0;dz=on.k@z
    wrong=C.copy();wrong[1,4]=wrong[4,1]=0
    bad=on.n.T@(wrong@on.n@dz[:on.d]+B@z[on.d:on.d+4])
    assert np.max(abs(bad))>1.,'missing flying cross-term trap not detected'
    print('full KCL/constraints/opening continuity/missing-coupling trap checks passed')

if __name__=='__main__':main()
