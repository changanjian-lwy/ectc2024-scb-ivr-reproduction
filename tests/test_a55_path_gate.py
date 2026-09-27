import json
import unittest
from pathlib import Path

from scb_ivr.conduction_loss import PathI2Integrals, path_resolved_conduction_loss
from scb_ivr.device_library import EPC2067, P24_EPC2067_POPULATION


ROOT = Path(__file__).resolve().parents[1]
A55 = (
    ROOT
    / "experiments"
    / "track_A_periodic_steady_state"
    / "A55_joint_lphase_deadtime_total_loss_optimization"
)


class A55PathGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((A55 / "path_gate_smoke.json").read_text())

    def test_smoke_is_explicitly_not_an_optimization_or_total_loss(self):
        self.assertEqual(
            self.payload["classification"], "IMPLEMENTATION_GATE_SMOKE_ONLY"
        )
        self.assertTrue(self.payload["not_an_optimization"])
        self.assertFalse(self.payload["complete_total_loss"])

    def test_dead_time_current_is_exposed(self):
        self.assertTrue(self.payload["unmodelled_dead_time_current_present"])
        self.assertTrue(
            any(value > 0 for value in self.payload["dead_time_i2_average_a2_per_phase"])
        )

    def test_saved_partial_loss_recomputes_from_saved_integrals(self):
        integrals = PathI2Integrals(
            period_s=self.payload["period_s"],
            high_side_a2s=tuple(self.payload["high_side_i2dt_a2s"]),
            low_side_a2s=tuple(self.payload["low_side_i2dt_a2s"]),
            dead_time_a2s=tuple(self.payload["dead_time_i2dt_a2s"]),
        )
        result = path_resolved_conduction_loss(
            EPC2067, P24_EPC2067_POPULATION, integrals
        )
        self.assertAlmostEqual(
            result.modeled_loss_w,
            self.payload["partial_channel_conduction_loss_w"],
        )


if __name__ == "__main__":
    unittest.main()
