"""Constrained-search retained candidate, no convergence/power success claim."""
import numpy as np
from joint_predecessor_event_ring import ring

ZQP=np.array([35.97210566844632,35.975978047075756,12.0101526712735,
              -.07749235197367701,11.949129609397826,-.014519966068721723,
              -.03967664747751208,92.85754870086635,-2.2662688787881247,
              21.158058237305646,56.598092542198025])

def main():
    for tol in [1e-9,1e-10,1e-11]:
        metrics={}
        h,end,_=ring(ZQP,di1=0,di2=0,di3=0,di4=0,origin=50e-9,
                     tolerances=dict(rtol=tol,atol=tol),metrics=metrics)
        print('tol',tol,'last event',h[-1])
        print('ring numerically admitted?',len(h)==4 and 'failure' not in h[-1],
              'physical current residual',(end[7:]-ZQP[7:]).tolist(),
              'output-port W',float(sum(metrics['charge_a_s']/metrics['elapsed_s'])))
        assert np.max(abs(end[7:]-ZQP[7:]))>2., 'must not mistake numerical ZVS for periodic closure'
    print('periodic failure persists; near-zero gate signs must be tolerance-audited')

if __name__=='__main__':main()
