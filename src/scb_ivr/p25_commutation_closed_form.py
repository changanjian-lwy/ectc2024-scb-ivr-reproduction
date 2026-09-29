"""D24: exact linear-network elimination for P25 M5/M10/M15.

Constant Vin, the two other lows ideal ON, all highs OFF, unclamped reverse
paths, finite positive linear capacitor banks. Returns transfer-normalized
capacitance Cn in dVds(target)/dt=iq/Cn, not isolated device Coss.
"""
from .p25_cycle_modes import cycle_mode


def normalized_capacitance(boundary, parts, mode):
    if boundary.branch!="P25" or boundary.nP!=3 or boundary.nM!=1 or boundary.module!=1:
        raise ValueError("P25 native three-phase single module only")
    if cycle_mode(mode).slot!="up_comm":
        raise ValueError("only M5/M10/M15 unclamped upward commutations")
    h1,h2,h3,l1,l2,l3=parts.capacitances()[:6]
    s1,s2=parts.series_f
    a=h1+s1
    if mode=="M5":
        # Ground-referenced a1 branch A; eliminate a1, then a2, then x2.
        b=h3+h2*a/(a+h2)
        return (a+h2)/a*(l2+(1+l2/s2)*b)
    if mode=="M10":
        # a2-to-ground after a1 elimination; target is a2-x3, not -a2.
        k=s2+h2*a/(a+h2)
        return l3+h3+l3*h3/k
    # M15: a1-to-ground after a2 elimination; target is Vin-a1.
    k=h1+h2*(h3+s2)/(h2+h3+s2)
    return l1+(1+l1/s1)*k


def switch_node_gain(boundary, parts, mode):
    """gamma=-dxq/dVds(target)>0; same frozen topology as normalized_capacitance."""
    normalized_capacitance(boundary,parts,mode)  # validate branch and capacitor banks
    h1,h2,h3=parts.capacitances()[:3]
    s1,s2=parts.series_f
    a=h1+s1
    if mode=="M5":
        k=h3+h2*a/(a+h2)
        return (a+h2)/a*(1+k/s2)
    if mode=="M10":
        k=s2+h2*a/(a+h2)
        return 1+h3/k
    k=h1+h2*(h3+s2)/(h2+h3+s2)
    return 1+k/s1


def voltage_reconstruction_slopes(boundary, parts, mode):
    """d(a1,a2,x1,x2,x3)/dVtarget on the fixed-mode charge manifold.

    These are increments from the SAME entry state, not preset voltage levels.
    Output voltage remains an independent dynamic state.
    """
    gamma=switch_node_gain(boundary,parts,mode)
    h1,h2,h3=parts.capacitances()[:3]
    s1,s2=parts.series_f
    a=h1+s1
    if mode=="M5":
        return (-h2/a,-(a+h2)/a,0.,-gamma,0.)
    if mode=="M10":
        k=s2+h2*a/(a+h2)
        return (-h2/(a+h2)*h3/k,-h3/k,0.,0.,-gamma)
    return (-1.,-h2/(h2+h3+s2),-gamma,0.,0.)
