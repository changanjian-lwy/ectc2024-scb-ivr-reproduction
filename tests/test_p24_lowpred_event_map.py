"""Tests of the D47 timed low-side event map (src/scb_ivr/p24_lowpred_event_map.py)."""
import unittest

import numpy as np

from scb_ivr.p24_exact_event_map import Circuit, section_full
from scb_ivr.p24_lowpred_event_map import ControlLP, LowPredEventMap

S_STAR = np.array([12.242053249, 23.885358378, 12.004905455, 0.999981176,
                   0.005900928, 24.132355716, 58.914910342, 95.97538723])
BASE = dict(ton=18.0344198276292e-9, i_target=-9.375,
            d_high=(8.200000011686706e-9, 8.260000011487177e-9, 8.310000011558438e-9, 7.040000009748423e-9))


class LowPredTests(unittest.TestCase):
    def test_late_edge_sees_the_crossing_and_reverse_conduction(self):
        m = LowPredEventMap(Circuit(), ControlLP(**BASE, d_low=(3e-9,) * 4))
        _, _, log = m.run_cycle(*section_full(S_STAR))
        for k in range(4):
            self.assertIsNotNone(log["low_cross_rel"][k])
            self.assertLess(log["low_cross_rel"][k], 3e-9)
            self.assertLess(log["low_on_vds"][k], -m.vf)                 # the node sits beyond -Vf: reverse conduction
            self.assertGreater(log["rev_energy_j"][4 + k], 0.0)

    def test_early_edge_is_a_hard_turn_on(self):
        m = LowPredEventMap(Circuit(), ControlLP(**BASE, d_low=(0.3e-9,) * 4))
        _, _, log = m.run_cycle(*section_full(S_STAR))
        for k in range(4):
            self.assertIsNone(log["low_cross_rel"][k])
            self.assertGreater(log["low_on_vds"][k], 0.0)
            self.assertEqual(log["rev_energy_j"][4 + k], 0.0)


if __name__ == "__main__":
    unittest.main()
