"""D79 / A163: the EPC2067 gate-level model (scb_ivr.p24_gate_model) against the datasheet, its scalar copy in the
plant (cosim/gate.py FastDev), and one gate-driven hard turn-on in the plant against LTspice with EPC's model
(reference numbers from scripts/p24_gate_edges.py, D79_gate_validation.json). The vendor library is not in the
repository: every test skips without it (CI)."""
import importlib.util
import math
import sys
import unittest
from pathlib import Path

from scb_ivr.p24_gate_model import available, load_device

HAVE = available()
ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(HAVE, "EPC library not present (SCB_EPC_LIB / vendor_models)")
class GateModelDatasheet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = load_device()

    def test_capacitances_at_20_v(self):
        d = self.d
        self.assertAlmostEqual(d.c_iss() / 2178e-12, 1.0, delta=0.01)
        self.assertAlmostEqual(d.c_rss() / 24e-12, 1.0, delta=0.05)
        self.assertAlmostEqual(d.c_oss() / 1071e-12, 1.0, delta=0.01)
        self.assertAlmostEqual(d.q_oss() / 37e-9, 1.0, delta=0.02)

    def test_on_resistance_and_transfer(self):
        d = self.d
        self.assertTrue(1.0e-3 < d.rds_on() <= 1.55e-3)
        self.assertTrue(0.7 <= d.vth() <= 2.5)                      # datasheet min / max
        self.assertAlmostEqual(float(d.i_ch(2.4, 3.0)), 58.3, delta=1.0)

    def test_gate_charge(self):
        g = self.d.gate_charge()
        for k, ref, tol in (("q_g", 17.1e-9, 0.03), ("q_gs", 5.3e-9, 0.03), ("q_gd", 2.0e-9, 0.15),
                            ("q_th", 4.2e-9, 0.10)):
            self.assertAlmostEqual(g[k] / ref, 1.0, delta=tol, msg=k)
        self.assertAlmostEqual(g["v_plateau"], 2.27, delta=0.05)

    def test_fast_copy_is_the_same_model(self):
        from scb_ivr.cosim.gate import FastDev
        f, d = FastDev(self.d), self.d
        for v, x in ((0.5, 12.0), (2.2, 3.0), (3.5, 0.1), (4.9, -0.3), (1.0, -2.0)):
            self.assertTrue(math.isclose(f.i_ch(v, x), float(d.i_ch(v, x)), rel_tol=1e-12, abs_tol=1e-15))
            self.assertTrue(math.isclose(f.q_gate(v, x), float(d.q_gate(v, x)), rel_tol=1e-12))
            self.assertTrue(math.isclose(f.cin(v, x), float(d.c_gs(v, -x) + d.c_gd(v - x)), rel_tol=1e-12))

    def test_spread_corner_meets_the_datasheet(self):
        # A164: a rigid threshold shift of the typical curve meets R_DS(on) max 1.55 mOhm and V_GS(TH) max 2.5 V up to
        # +1.0 V; A163's +1.5 V does not (1.81 mOhm, 2.99 V). Q_G max 22.3 nC bounds the charge scale at 1.29.
        hi, over = load_device(dk2=1.0), load_device(dk2=1.5)
        self.assertTrue(hi.rds_on() <= 1.55e-3 and hi.vth() <= 2.5)
        self.assertTrue(over.rds_on() > 1.55e-3 and over.vth() > 2.5)
        self.assertLessEqual(load_device(cg_scale=1.29).gate_charge()["q_g"], 22.3e-9)
        self.assertGreater(load_device(cg_scale=1.5).gate_charge()["q_g"], 22.3e-9)


@unittest.skipUnless(importlib.util.find_spec("cocotb"), "cocotb not installed (the bridge imports it)")
class DriverLead(unittest.TestCase):
    def test_high_side_turn_on_lead(self):
        from types import SimpleNamespace
        from scb_ivr.cosim.bridge import N, ModuleSim
        m = SimpleNamespace(drv={"hs_on_lead_ns": 4.0}, t_drv=10e-9, lead_k=[False] * N)
        lead = ModuleSim.lead_s(m, 0, 1, True)                      # a predictive turn-on moves
        self.assertAlmostEqual(ModuleSim.t_apply(m, 1e-6, 0, lead), 1e-6 + 6e-9, delta=1e-18)
        self.assertEqual(ModuleSim.lead_s(m, 0, 1, False), 0.0)      # timed / restart turn-ons do not
        self.assertEqual(ModuleSim.lead_s(m, 0, 0, False), 0.0)      # "on": the turn-off stays
        self.assertEqual(ModuleSim.lead_s(m, N, 1, False), 0.0)
        m.drv["lead_mode"] = "pulse"                                 # A165: the pulse and the low-side turn-on move
        self.assertAlmostEqual(ModuleSim.lead_s(m, 1, 1, True), 4e-9, delta=1e-18)
        self.assertAlmostEqual(ModuleSim.lead_s(m, 1, 0, False), 4e-9, delta=1e-18)
        self.assertEqual(ModuleSim.lead_s(m, N + 1, 0, False), 0.0)  # the low side's turn-off never
        self.assertAlmostEqual(ModuleSim.lead_s(m, N + 1, 1, False), 4e-9, delta=1e-18)
        self.assertEqual(ModuleSim.lead_s(m, N + 1, 1, False), 0.0)  # once per pulse
        m.drv = None
        self.assertAlmostEqual(ModuleSim.t_apply(m, 1e-6, 0), 1e-6 + 10e-9, delta=1e-18)


@unittest.skipUnless(HAVE, "EPC library not present (SCB_EPC_LIB / vendor_models)")
class GateEdgeInPlant(unittest.TestCase):
    def test_hard_turn_on_matches_ltspice(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import p24_gate_edges as G
        a, _ = G.edge_plant("on", 50, 4.5, dv=3.8)
        # LTspice with EPC's model on all 20 devices (D79): delay 3.39 ns, t50 8.35 ns, SH2 peak 24.82 V, 691 nJ
        self.assertAlmostEqual(a["delay_ns"], 3.39, delta=0.15)
        self.assertAlmostEqual(a["t50_ns"], 8.35, delta=0.2)
        self.assertAlmostEqual(a["vpk_v"], 24.82, delta=0.3)
        self.assertAlmostEqual(a["e_ch_nj"] / 691.4, 1.0, delta=0.03)


if __name__ == "__main__":
    unittest.main()
