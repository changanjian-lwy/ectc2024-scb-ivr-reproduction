import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
P25 = ROOT / "symbolic_derivations/02_P25_native"
sys.path.insert(0, str(P25))

import p25_native_fixed_slot_ring as model


class P25NativeRingTests(unittest.TestCase):
    def test_paper_equation_timing_is_not_silently_changed(self):
        self.assertEqual(model.NP, 3)
        self.assertAlmostEqual(model.TON, 500e-9, places=15)
        self.assertAlmostEqual(model.SLOT, 2e-6 / 3, places=15)
        self.assertAlmostEqual(model.LPHASE, 22e-9, places=18)

    def test_capacitance_matrix_is_positive_definite(self):
        self.assertGreater(np.min(np.linalg.eigvalsh(model.C)), 0.0)

    def test_documented_five_percent_fixed_slot_is_not_false_pass(self):
        result = model.ring(model.documented_seed())
        self.assertFalse(result.passed)
        self.assertEqual(result.history[0]["failure"],
                         "next high-side Vds positive at fixed slot")
        self.assertGreater(result.history[0]["next_vds_slot_v"], 0.05)

    def test_literal_event_chain_pass_is_not_nominal_period(self):
        result = model.event_ring(model.documented_seed())
        self.assertTrue(result.passed)
        self.assertEqual(result.charge_a_ns.shape, (3,))
        self.assertTrue(np.all(np.isfinite(result.charge_a_ns)))
        period_ns = result.history[-1]["next_high_on_ns"]
        self.assertGreater(abs(period_ns - 2000.0), 100.0)

    def test_equal_per_phase_ton_matches_scalar_ton(self):
        seed = model.documented_seed()
        scalar = model.event_ring(seed, ton=model.TON)
        vector = model.event_ring(seed, ton=np.full(3, model.TON))
        self.assertTrue(scalar.passed and vector.passed)
        self.assertAlmostEqual(
            scalar.history[-1]["next_high_on_ns"],
            vector.history[-1]["next_high_on_ns"], places=8)


if __name__ == "__main__":
    unittest.main()
