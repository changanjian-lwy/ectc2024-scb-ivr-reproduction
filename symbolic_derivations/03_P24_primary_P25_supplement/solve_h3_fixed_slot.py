"""Ideal first-swing timing feasibility; no SPICE or controller modification.

Freeze fly voltages from A37 H3 release; inactive nodes ideal 0 V.
Infer low-side zero crossing using ideal -Vo/L slope. This is a diagnostic
continuation, NOT an independently selectable release state or periodic orbit.
"""
import math

L=1.466666666666667e-9
C=1539.986224716e-12
VO=1.0
IPK=125.0
TR=76.847610293e-9
JR=11.251160622
X0_SAVED=.0395339765
VH0_SAVED=11.891896248
GAMMA=.999978532059
XC=X0_SAVED+VH0_SAVED/GAMMA
TZ=TR-L*JR/VO
Z=math.sqrt(L/C)
W=1/math.sqrt(L*C)
REQ=math.sqrt(C/L*((XC-VO)**2-VO**2))

def window(j):
    if j<REQ: return None
    # X(t)=Vo-Vo*cos(w*t)+j*Z*sin(w*t); x_release=0.
    phi=math.atan2(j*Z,-VO)
    radius=math.hypot(VO,j*Z)
    theta=phi-math.acos((XC-VO)/radius)
    arrival=TZ+L*j/VO+theta/W
    # Capacitive branch turns into upper reverse clamp, until current vanishes.
    i_at=-j*math.cos(theta)-VO/Z*math.sin(theta)
    hold=max(0.,-L*i_at/(XC-VO))
    return arrival,arrival+hold,i_at

def root(which):
    lo,hi=REQ,50.
    for _ in range(100):
        mid=(lo+hi)/2
        if window(mid)[which]<100e-9: lo=mid
        else: hi=mid
    return (lo+hi)/2

if __name__=='__main__':
    print(f'inferred zero crossing: {TZ*1e9:.6f} ns; frozen upper node: {XC:.6f} V')
    print(f'first-swing minimum: {REQ:.6f} A = {100*REQ/IPK:.6f}%')
    for pct in [9,10,15,20]:
        result=window(IPK*pct/100)
        print(pct, 'percent:', None if result is None else [round(result[0]*1e9,6),round(result[1]*1e9,6),round(result[2],6)])
    j_end=root(1); j_start=root(0)
    print(f'100 ns in ideal first window: J={j_end:.6f}..{j_start:.6f} A; alpha={100*j_end/IPK:.6f}..{100*j_start/IPK:.6f}%')
    # Regression + deliberately impossible low-energy input.
    assert window(1.) is None, 'must reject insufficient energy'
    assert window(12.5)[1]<100e-9, '5-10% cannot meet this frozen-state first-window slot'
    assert abs(window(j_start)[0]-100e-9)<1e-15
    assert abs(window(j_end)[1]-100e-9)<1e-15
    print('4 checks passed; no complete-circuit feasibility claim')
