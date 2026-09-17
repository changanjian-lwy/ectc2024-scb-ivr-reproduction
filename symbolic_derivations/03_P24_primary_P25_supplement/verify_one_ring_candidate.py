"""One sampled all-admissions candidate, checked for closure/second cycle.

Candidate changes ONLY the four currents at H2 origin relative to old A37;
zero startup, previous H1 reachability, and full periodic success unproven.
"""
import numpy as np
from joint_predecessor_event_ring import ring,seed_from_raw

def main():
    seed=seed_from_raw()
    kwargs=dict(di1=-8.,di2=-1.,di3=14.25,di4=8.25)
    metrics={}
    h,z,initial=ring(seed,**kwargs,max_handoffs=4,metrics=metrics)
    print('candidate current deltas A',kwargs)
    print('initial currents A',initial[7:].tolist())
    print('first ring history',h)
    passed=len(h)==4 and 'failure' not in h[-1]
    print('first ring admissions pass?',passed)
    print('closure delta currents A',(z[7:]-initial[7:]).tolist())
    print('closure delta node voltages V',(z[:7]-initial[:7]).tolist())
    print('closure delta flying voltages V',((z[:3]-z[3:6])-(initial[:3]-initial[3:6])).tolist())
    avg=metrics['charge_a_s']/metrics['elapsed_s']
    print('actual integration duration ns',metrics['elapsed_s']*1e9,
          'first-cycle phase mean currents A',avg.tolist(),'output-port transferred power at1V W',float(sum(avg)))
    h2,z2,_=ring(seed,**kwargs,max_handoffs=8)
    print('continuous second-cycle history',h2)
    print('last failure',h2[-1].get('failure'))
    # Regression traps: one ring admitting is NOT periodic or two-ring success.
    assert passed,'sampled first ring should admit'
    assert np.max(abs(z[7:]-initial[7:]))>1.,'must retain periodic current mismatch'
    assert len(h2)<8 and 'failure' in h2[-1],'must not report stable second cycle'
    print('admission/closure/second-cycle discrimination tests passed')

if __name__=='__main__':main()
