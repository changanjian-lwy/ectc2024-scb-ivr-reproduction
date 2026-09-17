"""Necessary first-window initial-state constraints, not a periodic solver.

P24 power stage + P25 next-phase control extension. Frozen flying voltages,
constant GS Coss, ideal low-node clamp, ideal 1 V output. No SPICE invoked.
"""
import math
from audit_four_positions_existing_cases import geometry

L=1.466666666666667e-9
VO=1.
IPK=125.
TON=200e-9*4/48
CASES=[
    dict(phase=2,slot=50e-9,x=.0394609943,vh=11.901668549,actual_i0=21.205095337),
    dict(phase=3,slot=100e-9,x=.0395339765,vh=11.891896248,actual_i0=41.5782701063),
]

def necessary(case,alpha):
    c,g=geometry(case['phase']-1)
    xc=case['x']+case['vh']/g
    j=alpha*IPK
    z=math.sqrt(L/c)
    r=math.hypot(VO,j*z)
    target=xc-VO
    if r<target: return None
    theta=math.atan2(j*z,-VO)-math.acos(target/r)
    flight=theta*math.sqrt(L*c)
    ia=-j*math.cos(theta)-VO/z*math.sin(theta)
    hold=max(0.,-L*ia/target)
    # slot in [tz+LJ/Vo+flight, same +hold]
    tz_hi=case['slot']-L*j/VO-flight
    tz_lo=tz_hi-hold
    return dict(tz_ns=(tz_lo*1e9,tz_hi*1e9),i0_a=(VO*tz_lo/L,VO*tz_hi/L),
                residual_at_upper_clamp_a=ia,window_ns=hold*1e9)

def main():
    for alpha in [.05,.09,.10]:
        print('alpha',alpha)
        for case in CASES:
            print('H',case['phase'],necessary(case,alpha),'old initial',case['actual_i0'])
    # Conditional volt-second constraint; use theoretical balanced 12 V plateau.
    rect=12*TON
    demand=VO*200e-9
    print('theoretical rectangular node area V*ns',rect*1e9,'period demand',demand*1e9,
          'remaining signed commutation area budget',(demand-rect)*1e9)
    assert necessary(CASES[1],.05) is None, 'insufficient-energy trap must fail'
    for case in CASES:
        ans=necessary(case,.10)
        assert ans['i0_a'][0]<ans['i0_a'][1]
        assert ans['window_ns']>0
    # Trap: declaring old H3 candidate compatible must be rejected.
    a=necessary(CASES[1],.10)['i0_a']
    assert not a[0]<=CASES[1]['actual_i0']<=a[1]
    assert abs(demand-rect)<1e-20
    print('checks passed; ideal intervals are necessary, not sufficient')

if __name__=='__main__': main()
