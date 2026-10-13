"""A206: the plant's switch resistances (CircuitParams.r_sw), the turn-on at V_DS <= 0 as an edge (gate_zvs_edge), the
low sides' own turn-on resistance (gate_r_on_ls) and the off gate that follows its drain (gate_miller), on A206's
single-edge harness (a206_edge.py: one high-side turn-off at 136.4 A, its low side commanded on 3.03 ns later).
Reference numbers: LTspice with EPC's model on the same edge (A205's replays of the settled N0 record, 40 ns after
the turn-off command). The gate tests need the vendor library and skip without it (CI); the r_sw tests do not."""
import sys
import unittest
from pathlib import Path

import numpy as np

from scb_ivr.cosim.circuit import TRACK_A, CircuitParams, Sim
from scb_ivr.cosim.plant import FastPlant
from scb_ivr.p24_gate_model import available

sys.path.insert(0, str(TRACK_A / "A206_p24_low_side_zvs_turn_on"))
import a206_edge as E  # noqa: E402

HAVE = available()
LT_REV_NVS = {3.0: (11.69, 11.94), 1.0: (6.02, 6.18), 0.3: (3.99, 4.16)}     # A205 replays k7, four phases


class SwitchResistance(unittest.TestCase):
    def test_default_is_g_on(self):
        p = CircuitParams()
        self.assertEqual(Sim(p).g_sw, [p.g_on] * (2 * p.n))

    def test_conducting_switches_drop_i_r(self):
        r_hs, r_ls = 0.64e-3, 0.43e-3
        p = CircuitParams(L=E.L0, cs=E.CS, R=0.0, t_ramp=0.0, load_kind="cc", i_load=250.0, t_load=0.0,
                          r_sw=(r_hs, r_ls))
        y0 = np.zeros(12)
        y0[:3] = [48.0, 24.0, 12.0]; y0[3] = 12.0; y0[7] = 1.0
        y0[8:12] = [136.4, 100.3, 9.8, 55.1]
        pl = FastPlant(p, y0, [True, False, False, False], [False, True, True, True])
        pl.integrate_to(0.2e-9, lambda: None)
        i = pl.y[pl.nv:pl.nv + 4]
        self.assertAlmostEqual(pl.vds(0) / (i[0] * r_hs), 1.0, delta=0.01)          # SH1 carries phase 1
        self.assertAlmostEqual(pl.vds(5) / (-i[1] * r_ls), 1.0, delta=0.01)         # SL2 carries phase 2 in reverse
        self.assertAlmostEqual(pl.vds(7) / (-i[3] * r_ls), 1.0, delta=0.01)


@unittest.skipUnless(HAVE, "EPC library not present (SCB_EPC_LIB / vendor_models)")
class ZeroVoltageTurnOn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sw = (E.R_TYP / 2, E.R_TYP / 3)
        cls.off = E.edge(E.params(False))
        cls.zvs = {r: E.edge(E.params(True, r_on_ls=r)) for r in (3.0, 0.3)}
        cls.full = {r: E.edge(E.params(True, r_on_ls=r, r_sw=sw, r=0.0, miller=True)) for r in (3.0, 1.0, 0.3)}

    def test_off_conducts_at_once(self):
        self.assertLessEqual(self.off["t_on_ns"], 0.02)
        self.assertEqual(self.off["e_edge_uj"], 0.0)

    def test_edge_takes_the_gate_time(self):
        self.assertTrue(4.0 < self.zvs[3.0]["t_on_ns"] < 8.0, self.zvs[3.0]["t_on_ns"])
        self.assertTrue(0.5 < self.zvs[0.3]["t_on_ns"] < 2.0, self.zvs[0.3]["t_on_ns"])
        self.assertGreater(self.zvs[3.0]["rev_nvs"], self.zvs[0.3]["rev_nvs"] + 3.0)
        self.assertGreater(self.zvs[0.3]["rev_nvs"], self.off["rev_nvs"] + 0.5)
        self.assertLess(self.zvs[3.0]["i_end"], self.off["i_end"] - 1.0)             # the lost volt-seconds

    def test_low_side_resistance_leaves_the_high_side_alone(self):
        self.assertEqual(self.zvs[3.0]["e_hs_uj"], self.zvs[0.3]["e_hs_uj"])

    def test_against_ltspice(self):
        """With all three parts the 40 ns reverse volt-seconds are within 10 % of LTspice's at every resistance, and
        the gate's dip puts the reverse drop near LTspice's 3.16 V."""
        for r, (lo, hi) in LT_REV_NVS.items():
            v = self.full[r]["rev_nvs"]
            self.assertTrue(0.9 * lo <= v <= 1.1 * hi, (r, v))
        self.assertTrue(-3.4 < self.full[3.0]["v_min"] < -2.9, self.full[3.0]["v_min"])


if __name__ == "__main__":
    unittest.main()
