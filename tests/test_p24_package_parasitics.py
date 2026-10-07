"""D65 package parasitics: closed-form checks of the via field, the lateral segments, the SCB branch currents and the
loop energy bound."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scb_ivr import p24_package_parasitics as P  # noqa: E402


def test_via_field_matches_vpd_table_iii():
    # VPD framework Table III: Cu TSV d 30 um, h 300 um, pitch 60 um -> 7.1 mOhm per via
    per_via, area_per_via = 7.1e-3, (60e-6) ** 2
    assert abs(P.via_field_r(300e-6, 1.0) / (per_via * area_per_via) - 1) < 0.03


def test_lateral_loss_dc():
    i = np.full((4, 8), 10.0)                     # 10 A dc per phase
    w, seg = P.lateral_loss(i, 35e-6)
    r = P.RHO_CU * 2.5e-3 / (35e-6 * 10e-3)
    assert np.allclose(seg[:, 0], [40, 30, 20, 10])
    assert abs(w - r * (40 ** 2 + 30 ** 2 + 20 ** 2 + 10 ** 2)) < 1e-12


def test_branch_currents_return_the_output():
    t, i, hs, lo = P.phase_waveforms(500e-9, 38e-9, 143.0, -15.6, 0.3, 10e-9)
    br = P.branch_currents(i, hs, lo)
    res = ~(hs | lo)                                             # resonant intervals: no channel
    assert np.allclose(br["ls"].sum(axis=0) + br["in"], (i * ~res).sum(axis=0))
    assert np.allclose(br["cs"][0], br["hs"][0] + br["hs"][1])


class _ConstC:
    def __init__(self, c):
        self.v = c

    def c(self, v):
        return np.full_like(np.asarray(v, dtype=float), self.v)


def test_overshoot_linear_c():
    l, i, vr, c, n = 100e-12, 100.0, 12.0, 1e-9, 2
    exact = np.sqrt(vr ** 2 + l * i ** 2 / (n * c))       # 0.5 L I^2 = n C (V^2 - Vr^2) / 2
    assert abs(P.overshoot(l, i, vr, _ConstC(c), n) - exact) < 1e-3


def load_tests(loader, tests, pattern):
    """The portable suite collects with unittest; wrap the module's test functions so they run there too."""
    import unittest
    suite = unittest.TestSuite()
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            suite.addTest(unittest.FunctionTestCase(fn, description=name))
    return suite
