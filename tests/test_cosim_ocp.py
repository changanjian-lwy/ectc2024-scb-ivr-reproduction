"""A253: the peak-current limit's crossing time (bridge.ocp_cross)."""
import unittest

from scb_ivr.cosim.bridge import ocp_cross


class OcpCross(unittest.TestCase):
    def test_linear_crossing(self):
        self.assertAlmostEqual(ocp_cross(0.0, 120.0, 4e-9, 140.0, 135.0), 3e-9, delta=1e-18)

    def test_already_above(self):
        self.assertEqual(ocp_cross(1e-9, 150.0, 5e-9, 160.0, 135.0), 1e-9)

    def test_not_rising(self):
        self.assertEqual(ocp_cross(1e-9, 136.0, 5e-9, 136.0, 135.0), 1e-9)


if __name__ == "__main__":
    unittest.main()
