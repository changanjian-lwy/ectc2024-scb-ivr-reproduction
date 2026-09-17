"""Read-only A37 joint diagnostics; no optimizer, netlist edit, or SPICE.

Physical residuals keep their units. Diagnostic scales are explicit, not
paper tolerances or a new weighted replacement for the old A37 objective.
"""
from pathlib import Path
import numpy as np
from spicelib import RawRead

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'experiments/track_A_periodic_steady_state/A37_solver_work/iter_001.raw'
T=200e-9
EPS=2e-12
NP=4
FLY=53.8e-6

def classify(admitted,closure_ok):
    if len(admitted)!=NP: raise ValueError('explicit four-phase branch requires four flags')
    return all(admitted) and closure_ok

def main():
    r=RawRead(str(RAW))
    t=np.real(r.get_trace('time').get_wave(0))
    def w(name): return np.real(r.get_trace(name).get_wave(0))
    def at(y,when):
        if not t[1]<=when<=t[-1]: raise ValueError('sample outside positive-time saved data')
        return float(np.interp(when,t,y))
    def delta(y): return at(y,T+EPS)-at(y,EPS)
    a=[w(f'V(xmod:a{k})') for k in range(1,4)]
    x=[w(f'V(xmod:x{k})') for k in range(1,5)]
    vh=[w('V(vin)')-a[0],a[0]-a[1],a[1]-a[2],a[2]-x[3]]
    admitted=[True] # H1 is the initial active phase, not a measured ZVS admission.
    print('scope: P24 stage/P25 extension, GS constant Coss, fixed 5MHz, candidate IC, 1V output boundary')
    for k in range(4):
        gate=w(f'V(xmod:gh{k+1})')
        rises=np.flatnonzero((gate[:-1]<2.5)&(gate[1:]>=2.5))
        falls=np.flatnonzero((gate[:-1]>=2.5)&(gate[1:]<2.5))
        current=w(f'I(XMOD:LIND{k+1})')
        if k:
            valid=[j for j in rises if t[j+1]<T]
            admitted.append(bool(valid))
        peak=None
        if len(falls):
            j=falls[0]
            tf=t[j]+(2.5-gate[j])/(gate[j+1]-gate[j])*(t[j+1]-t[j])
            peak=at(current,tf)
        print('H',k+1,'initial-active' if k==0 else 'admitted='+str(admitted[-1]),
              'turn-off current A',peak,'peak error A',None if peak is None else peak-125,
              'Vds at slot V',at(vh[k],(k*T/NP if k else T)+EPS))
    print('closure samples ns',EPS*1e9,(T+EPS)*1e9)
    for k in range(4):
        di=delta(w(f'I(XMOD:LIND{k+1})'))
        print('L',k+1,'delta A',di,'diagnostic /125A',di/125,
              'switch-node delta V',delta(x[k]))
    for k in range(3):
        dv=delta(a[k]-x[k])
        print('F',k+1,'delta V',dv,'charge delta uC',FLY*dv*1e6,
              'high-node delta V',delta(a[k]))
    print('controller-state delta',delta(w('V(xmod:sequence_state)')))
    print('first missed scheduled admission:',next((f'H{k+1}' for k in range(1,4) if not admitted[k]),None))
    print('NOT a periodic success; output regulation and hardware loss are not assessed')
    assert not classify([True,True,False,False],True), 'trap: local H2 pass cannot imply whole-module pass'
    assert not classify([True]*4,False), 'trap: all gates pass cannot replace closure'
    assert classify([True]*4,True)
    try: classify([True],True)
    except ValueError: pass
    else: raise AssertionError('must reject omitted phases')
    print('4 classifier tests passed')

if __name__=='__main__': main()
