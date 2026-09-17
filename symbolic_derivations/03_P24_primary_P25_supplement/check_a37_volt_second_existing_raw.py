"""KVL integral cross-check on saved A37; no SPICE invocation."""
from pathlib import Path
import numpy as np
from spicelib import RawRead

ROOT=Path(__file__).resolve().parents[2]
r=RawRead(str(ROOT/'experiments/track_A_periodic_steady_state/A37_solver_work/iter_001.raw'))
t=np.real(r.get_trace('time').get_wave(0))
# Saved t=0 row contains zero currents, unlike the nonzero .ic seed.
# Exclude it explicitly; do not interpret that row as physical zero startup.
q=(t>0)&(t<=200e-9)
for k in [2,3]:
    x=np.real(r.get_trace(f'V(xmod:x{k})').get_wave(0))[q]
    i=np.real(r.get_trace(f'I(XMOD:LIND{k})').get_wave(0))[q]
    observed=float(i[-1]-i[0])
    predicted=float(np.trapezoid(x-1-1e-6*i,t[q])/1.466666666666667e-9)
    print(k, 'start/end A',float(i[0]),float(i[-1]),'delta A',observed,
          'integral prediction A',predicted,'residual A',observed-predicted)
    assert abs(observed-predicted)<.005, 'saved KVL integral inconsistency'
print('cross-check passed; endpoint near 199.997 ns, not an exact periodic closure test')
