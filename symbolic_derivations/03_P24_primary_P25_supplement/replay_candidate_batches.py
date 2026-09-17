"""Reproducible independent-state batches; outputs results, no SPICE/old edits."""
import argparse
import numpy as np
from joint_predecessor_event_ring import ring,seed_from_raw

def main():
    p=argparse.ArgumentParser()
    p.add_argument('batch',choices=['i4','i1','i2'])
    batch=p.parse_args().batch
    configs={
        'i4':('di4',np.arange(7.,10.001,.25),dict(di3=14.25)),
        'i1':('di1',np.arange(-10.,-3.999,.25),dict(di3=14.25,di4=8.25)),
        'i2':('di2',np.arange(-1.5,-.499,.1),dict(di3=14.25,di4=8.25,di1=-8.)),
    }
    name,values,base=configs[batch];seed=seed_from_raw()
    print('candidate batch',batch,'base',base,'count',len(values))
    for value in values:
        args=dict(base);args[name]=float(value)
        h,z,initial=ring(seed,**args)
        print('deltas',args,'history',h)
        if len(h)==4 and 'failure' not in h[-1]:
            print('all-admissions ONLY, current closure delta A',(z[7:]-initial[7:]).tolist(),
                  'node closure delta V',(z[:7]-initial[:7]).tolist())

if __name__=='__main__':main()
