"""Retained, NOT converged candidate; numerical tolerance sensitivity."""
import numpy as np
from joint_predecessor_event_ring import ring

Z=np.array([35.95746978579451,35.95802088771017,11.989840171273501,
            -.076869220327159,11.953293433886074,-.007156970538510967,
            -.03877298543452277,92.83286066739684,-2.353795341839387,
            21.141938966542003,56.55712035522852])

def main():
    residuals=[]
    for tol in [1e-9,1e-10]:
        metrics={}
        h,end,_=ring(Z,di1=0,di2=0,di3=0,di4=0,origin=50e-9,
                     metrics=metrics,tolerances=dict(rtol=tol,atol=tol))
        print('tol',tol,'history',h)
        if len(h)<4 or 'failure' in h[-1]:
            print('retained candidate loses feasibility under tolerance check');return
        residuals.append(end-Z)
        avg=metrics['charge_a_s']/metrics['elapsed_s']
        print('physical residual',(end-Z).tolist(),'output-port W',float(sum(avg)))
    print('tolerance residual difference max V/A',float(np.max(abs(residuals[0][:7]-residuals[1][:7]))),
          float(np.max(abs(residuals[0][7:]-residuals[1][7:]))))
    assert np.max(abs(residuals[1][7:]))>2., 'periodic failure must not disappear with tighter tolerance'
    print('retained periodic failure robust to tested ODE tolerances; no global impossibility proof')

if __name__=='__main__':main()
