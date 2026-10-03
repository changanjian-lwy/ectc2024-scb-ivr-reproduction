"""D64: the filter inductor from first principles, and the switching frequency it implies.

The open lever of the trade-off map (T14): whether a lower frequency pays depends on the inductor's resistance per
henry, R/L. D62 carried it as an assumed technology constant. D64 derives it for the simplest buildable inductor - a
parallel-plate (stripline) air-core loop, P24 Table 2's "stripline" and "substrate air core" class - and puts it into
the converter model at every frequency.

Inductor (one phase): two copper plates of width w, length l, thickness t, gap h, carrying the current out and back.
- L = mu0 l h / w (w >> h; the field between the plates);
- the DC current fills the plates: R_dc = 2 rho l / (w t), so R_dc / L = 2 rho / (mu0 h t);
- the ripple current flows on the facing surfaces within the skin depth delta = sqrt(rho / (pi f mu0)) (the plates'
  proximity effect): R_ac = 2 rho l / (w min(t, delta)), so R_ac / L = 2 rho / (mu0 h min(t, delta)).
  The ripple's spectrum is taken at its fundamental (the switching frequency); its harmonics see more resistance
  (R ~ sqrt(n)), so the AC loss here is a lower bound.
- Loss per phase: I_dc^2 R_dc + I_ac,rms^2 R_ac, I_ac,rms = (peak - valley) / sqrt(12) (a triangle).
The footprint l w sets nothing in R / L: only the height h and the copper t (or delta) do. It sets l / w = L / (mu0 h).

Converter side at each frequency f: Eq. (4)'s L = 7.333 nH x (1 MHz / f) (1.4667 nH at 5 MHz); for each negative-
current target, D57's high-side turn-on, the charge-balance orbit and D62's middle-case losses with an ideal
inductor (a115_predict.row), and D57's threshold (the valley margin).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MU0 = 4e-7 * math.pi
RHO_CU = 1.72e-8          # ohm m, 20 C (25 C: 1.74e-8; the difference is ~1%)
I_DC = 62.5               # A per phase at 250 W, 1 V


def skin_depth(f, rho=RHO_CU):
    return math.sqrt(rho / (math.pi * f * MU0))


@dataclass(frozen=True)
class Stripline:
    h: float              # plate gap, m
    t: float              # copper thickness, m
    rho: float = RHO_CU

    def r_per_l_dc(self):
        return 2 * self.rho / (MU0 * self.h * self.t)

    def r_per_l_ac(self, f):
        return 2 * self.rho / (MU0 * self.h * min(self.t, skin_depth(f, self.rho)))

    def loss(self, lf, f, ripple_pp, n=4, i_dc=I_DC):
        """Copper loss of n phases (W): I_dc^2 R_dc + (ripple / sqrt 12)^2 R_ac."""
        i_ac = ripple_pp / math.sqrt(12)
        return n * lf * (i_dc ** 2 * self.r_per_l_dc() + i_ac ** 2 * self.r_per_l_ac(f))

    def aspect(self, lf):
        """l / w for inductance lf."""
        return lf / (MU0 * self.h)


def effective_r_per_l(s: Stripline, f, ripple_pp, i_dc=I_DC):
    """The single R / L (ohm per henry) that gives the same loss on the phase's total mean square, D62's form."""
    i_ac = ripple_pp / math.sqrt(12)
    return (i_dc ** 2 * s.r_per_l_dc() + i_ac ** 2 * s.r_per_l_ac(f)) / (i_dc ** 2 + i_ac ** 2)
