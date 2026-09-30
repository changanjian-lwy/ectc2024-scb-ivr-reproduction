"""Tests of the D46 reverse-drop event map (src/scb_ivr/p24_drop_event_map.py)."""
import unittest

import numpy as np

from scb_ivr.p24_exact_event_map import Circuit, Control, section_free, section_full
from scb_ivr.p24_nonlinear_event_map import NonlinearEventMap
from scb_ivr.p24_drop_event_map import DropEventMap

S_STAR = np.array([12.242053249, 23.885358378, 12.004905455, 0.999981176,
                   0.005900928, 24.132355716, 58.914910342, 95.97538723])
CTL = Control(ton=18.0344198276292e-9, i_target=-9.375,
              d_high=(8.200000011686706e-9, 8.260000011487177e-9, 8.310000011558438e-9, 7.040000009748423e-9))


class DropTests(unittest.TestCase):
    def test_small_drop_approaches_the_ideal_diode(self):
        v, i = section_full(S_STAR)
        v1, i1, _ = NonlinearEventMap(Circuit(), CTL).run_cycle(v, i)
        v2, i2, log = DropEventMap(Circuit(), CTL, vf=0.01, r_dev=1e-4).run_cycle(v, i)
        np.testing.assert_allclose(section_free(v2, i2), section_free(v1, i1), atol=2e-3)
        kinds = [e[1] for e in log["events"]]
        self.assertEqual(kinds.count("zvs"), 4)                  # one comparator decision per phase, then the diode
        self.assertEqual(kinds.count("diode_on"), 4)

    def test_reverse_conduction_equilibrium(self):
        m = DropEventMap(Circuit(), CTL)
        chan = (False,) * 4 + (True, True, True, False)
        diode = (False,) * 7 + (True,)
        tp = m.topo2(chan, diode)
        v, i = section_full(S_STAR)
        v = v.copy(); i = np.array([0.0, 0.0, 0.0, 160.0])
        names = Circuit().nodes
        v[names.index("a1")] = 36.0; v[names.index("x1")] = 0.0; v[names.index("out")] = 1.0
        v[names.index("x4")] = -(m.vf + m.r_dev * 160.0 / 3)          # SL4's three devices carry 160 A in reverse
        z = tp.to_z(v, i)
        ids = tp.diode_ids(z[:tp.m])
        self.assertAlmostEqual(float(ids[0]), -160.0, places=6)
        x4 = tp.free[tp.root["x4"]]
        self.assertLess(abs(tp.rhs(0.0, z)[x4]), 1e3)                  # V/s: the node is at its equilibrium


if __name__ == "__main__":
    unittest.main()
