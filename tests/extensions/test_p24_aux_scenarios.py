"""D57 (src/scb_ivr/extensions/p24_aux_scenarios.py; an extension): the scenario helpers on D56's model."""
import unittest
from dataclasses import replace

import numpy as np

from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit, Model
from scb_ivr.extensions.p24_aux_scenarios import area, hard_on, linear_floor, node_model, r_lr, required_i_neg, zcs_residual


class AuxScenarios(unittest.TestCase):
    def test_required_current_matches_d56_validation_and_linear_floor(self):
        ckt = EdgeCircuit()
        i = required_i_neg(ckt)
        self.assertTrue(31.25 < i < 37.5)                    # D56's validation table crosses zero in between
        m = node_model(ckt)
        xs = np.linspace(0, ckt.v_rail, 400)
        ceq = float(np.trapezoid(m.cnode(xs), xs)) / ckt.v_rail
        self.assertLess(abs(linear_floor(ckt.lf, ceq, ckt.v_rail, ckt.vo) / i - 1), 0.05)

    def test_high_side_alone_needs_less_and_larger_lf_needs_less(self):
        ckt = EdgeCircuit()
        alone = required_i_neg(replace(ckt, n_l=0, n_next=0))
        big_l = required_i_neg(replace(ckt, lf=13.44e-9))
        full = required_i_neg(ckt)
        self.assertLess(alone, full); self.assertLess(big_l, full)
        self.assertGreater(min(alone, big_l), 0.02 * 125.0)  # neither reaches P24's 2%

    def test_hard_on_models_are_ordered(self):
        m = Model()
        for v in (2.0, 9.0):
            lo, c, hi = (hard_on(m, v, k) for k in ("a91_lower", "d56_central", "a91_upper"))
            self.assertLess(lo, c); self.assertLess(c, hi)
        self.assertEqual(hard_on(m, 0.0, "d56_central"), 0.0)

    def test_resistance_and_area_scale_as_stated(self):
        self.assertAlmostEqual(r_lr("p24_t2_substrate_air", 1.2e-9), 7e-3)
        self.assertEqual(r_lr("a101_fixed_0p2mohm", 3e-9), 0.2e-3)
        a = area(1e-9, 30.0, 6.0, 1.4666667e-9, 135.0, 76.0, 0.25, 1e-6, [9.0] * 4, 3e-6, [36.0, 24.0, 12.0])
        self.assertAlmostEqual(a["bds_vs_main_dies"], 0.1)
        self.assertAlmostEqual(a["lr_vs_lf_by_peak_energy"], 1e-9 * 30.0 ** 2 / (1.4666667e-9 * 135.0 ** 2))
        self.assertAlmostEqual(a["cm_vs_series_caps"], 4 * 81.0 / (3 * (36.0 ** 2 + 24.0 ** 2 + 12.0 ** 2)))

    def test_zcs_residual_energy(self):
        z = zcs_residual(Model(), 1e-9, 0.25, 9.0, 4.0)
        self.assertAlmostEqual(z["energy_j"], 8e-9)
        self.assertGreater(z["overshoot_v"], 0.0)


if __name__ == "__main__":
    unittest.main()
