"""D39: whole-window affine change envelope evaluated in floating point.

The comparison theorem is analytic. scipy.expm evaluation is NOT outward-
rounded interval arithmetic. This does not certify first-event coverage.
"""
from dataclasses import dataclass
from math import isfinite
import numpy as np
from scipy.linalg import expm


@dataclass(frozen=True)
class AffineEnvelope:
    start_s: float
    end_s: float
    coordinates: tuple[str,...]
    units: tuple[str,...]
    lower: tuple[float,...]
    upper: tuple[float,...]
    change_bound: tuple[float,...]
    scope: str = "ANALYTICAL_COMPARISON_NUMERICALLY_EVALUATED; not rigorous floating-point enclosure or event certification"


def affine_envelope(flow, end_s):
    """For y'=G y, |y(t)-y0| <= integral exp(|G|s)|G y0| ds, 0<=t<=T.

The homogeneous coordinate is included in construction, excluded from the
returned nine electrical coordinates. Bound is per coordinate, not a mixed-
unit norm, and retains actual entry residuals.
"""
    if not isfinite(end_s) or end_s < flow.start.time_s:
        raise ValueError("finite forward absolute endpoint required")
    g = flow.generator
    y0 = np.r_[flow.start.voltage_v,flow.start.current_a,1.]
    if g.shape != (10,10) or not np.all(np.isfinite(g)):
        raise ValueError("finite full-node affine generator required")
    augmented = np.zeros((11,11))
    augmented[:10,:10] = np.abs(g)
    augmented[:10,10] = np.abs(g@y0)
    radius = expm(augmented*(end_s-flow.start.time_s))[:9,10]
    if not np.all(np.isfinite(radius)) or np.any(radius<0):
        raise ArithmeticError("nonfinite or negative envelope; no clipping")
    return AffineEnvelope(flow.start.time_s,end_s,
        ("a1","a2","x1","x2","x3","out","iL1","iL2","iL3"),
        ("V",)*6+("A",)*3,tuple(y0[:9]-radius),tuple(y0[:9]+radius),tuple(radius))
