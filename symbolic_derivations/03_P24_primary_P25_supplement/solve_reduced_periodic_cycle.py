"""Piecewise local periodic-cycle diagnostic, not the full four-phase DAE.

Freeze balanced flying voltages (U=12 V), ideal other low clamps, constant
Coss. Include rising LC, upper reverse clamp, high ON, falling LC, low ON.
Explicit NP=4/NM_SYSTEM=4/NM_INSTANCE=1; per-phase symmetry is an additional
approximation. No SPICE execution or alteration of historic netlists.
"""
import math
from audit_four_positions_existing_cases import geometry

NP=4
NM_SYSTEM=4
NM_INSTANCE=1
VIN=48.
VO=1.
T=200e-9
TON=NP*VO/VIN*T
L=1.466666666666667e-9
REFPEAK=125.
U=VIN/NP

def cycle(c,j,h,ton=TON):
    z=math.sqrt(L/c); tau=math.sqrt(L*c)
    radius=math.hypot(VO,j*z)
    if radius<U-VO: return None
    th=math.atan2(j*z,-VO)-math.acos((U-VO)/radius)
    up=th*tau
    ia=-j*math.cos(th)-VO/z*math.sin(th)
    hmax=-ia*L/(U-VO)
    if h<0 or h>hmax+1e-18: raise ValueError('outside upper reverse-clamp window')
    ion=ia+(U-VO)*h/L
    peak=ion+(U-VO)*ton/L
    if peak<=0: return None
    # Falling LC starts at X=U and i=peak, before next clamp.
    def xx(theta): return VO+(U-VO)*math.cos(theta)-peak*z*math.sin(theta)
    lo,hi=0.,math.pi
    for _ in range(80):
        mid=(lo+hi)/2
        if xx(mid)>0: lo=mid
        else: hi=mid
    td=(lo+hi)/2
    iend=peak*math.cos(td)+(U-VO)/z*math.sin(td)
    down=td*tau
    low=(iend+j)*L/VO
    duration=up+h+ton+down+low
    # Integrate X analytically over rising/falling portions.
    area_up=VO*up-VO*tau*math.sin(th)+j*z*tau*(1-math.cos(th))
    area_down=VO*down+(U-VO)*tau*math.sin(td)+peak*z*tau*(math.cos(td)-1)
    area=area_up+U*(h+ton)+area_down
    # Rising/falling capacitor-current integrals -C*U and +C*U cancel.
    charge_hold=(ia+ion)*h/2
    charge_on=(ion+peak)*ton/2
    charge_low=(iend-j)*low/2
    avg=(charge_hold+charge_on+charge_low)/duration
    assert abs(area-VO*duration)<1e-18, 'periodic KVL integral check'
    return dict(period=duration,peak=peak,hmax=hmax,hold=h,up=up,down=down,low=low,
                comm_area=area_up+U*h+area_down,avg_current=avg)

def solve(c,j):
    z=math.sqrt(L/c)
    req=math.sqrt(c/L*((U-VO)**2-VO**2))
    if j<req: return {'status':'insufficient energy','required_pct':req/REFPEAK*100}
    a=cycle(c,j,0.)
    b=cycle(c,j,a['hmax'])
    if not a['period']<=T<=b['period']:
        return {'status':'no 200ns root in first clamp window','period_bounds_ns':[a['period']*1e9,b['period']*1e9],
                'peak125_period_ns':b['period']*1e9}
    lo,hi=0.,a['hmax']
    for _ in range(80):
        h=(lo+hi)/2
        if cycle(c,j,h)['period']<T: lo=h
        else: hi=h
    ans=cycle(c,j,(lo+hi)/2)
    assert abs(ans['period']-T)<1e-18
    return {'status':'local 200ns root','peak_a':ans['peak'],'peak_error_a':ans['peak']-REFPEAK,
            'hold_ns':ans['hold']*1e9,'available_hold_ns':ans['hmax']*1e9,
            'comm_area_v_ns':ans['comm_area']*1e9,'peak125_period_ns':b['period']*1e9}

def main():
    print('fixed local boundary:',NP,NM_SYSTEM,NM_INSTANCE,'Ton ns',TON*1e9)
    for phase in [1,2,3,4]:
        c=geometry(phase-1)[0]
        for pct in [5,9,9.5,10]: print('phase',phase,'percent',pct,solve(c,pct/100*REFPEAK))
    # Diagnostic only: solve Ton required if we release then immediately take
    # the first ZVS crossing. These Ton values are NOT inserted in any model.
    c=geometry(1)[0]
    for pct in [9,10]:
        j=pct/100*REFPEAK
        lo,hi=5e-9,TON
        for _ in range(80):
            mid=(lo+hi)/2
            if cycle(c,j,0.,mid)['period']<T: lo=mid
            else: hi=mid
        ton=(lo+hi)/2; ans=cycle(c,j,0.,ton)
        assert abs(ans['period']-T)<1e-18
        print('hypothetical variable Ton, phase2, percent',pct,'Ton ns',ton*1e9,
              'peak A',ans['peak'],'avg current A',ans['avg_current'],'NOT a fixed-Ton success')
    assert solve(geometry(1)[0],.05*REFPEAK)['status']=='insufficient energy'
    print('piecewise continuity/KVL/root checks passed; no full-module closure claim')

if __name__=='__main__': main()
