import unittest

from scb_ivr.evidence import Evidence
from scb_ivr.startup_voltage_supervisor import (
    ReleaseReason,
    StartupBoundary,
    StartupObservation,
    evaluate_startup_readiness,
)


class StartupVoltageSupervisorTests(unittest.TestCase):
    def decide(self, nodes, currents=(0.0, 0.0, 0.0, 0.0)):
        return evaluate_startup_readiness(StartupObservation(48.0, nodes, currents))

    def test_exact_periodic_candidate_passes(self):
        result = self.decide((36.0, 24.0, 12.0))
        self.assertTrue(result.release)
        self.assertEqual(result.segment_voltages_v, (12.0, 12.0, 12.0, 12.0))

    def test_shifted_nodes_pass_when_adjacent_differences_are_safe(self):
        result = self.decide((37.0, 25.0, 13.0))
        self.assertTrue(result.release)
        self.assertEqual(result.segment_voltages_v, (11.0, 12.0, 12.0, 13.0))

    def test_planted_absolute_voltage_trap_is_rejected(self):
        # Every node is within +/-3 V of 36/24/12, yet the second segment is 18 V.
        result = self.decide((39.0, 21.0, 15.0))
        self.assertFalse(result.release)
        self.assertEqual(result.reason, ReleaseReason.SEGMENT_UNDERVOLTAGE)
        self.assertEqual(result.segment_voltages_v, (9.0, 18.0, 6.0, 15.0))

    def test_safe_voltage_does_not_override_unsafe_current(self):
        result = self.decide((36.0, 24.0, 12.0), (0.0, 0.0, 1.01, 0.0))
        self.assertFalse(result.release)
        self.assertEqual(result.reason, ReleaseReason.CURRENT_NOT_SAFE)

    def test_boundary_is_explicitly_exploratory(self):
        self.assertEqual(StartupBoundary().evidence, Evidence.EXPLORATORY_ASSUMPTION)


if __name__ == "__main__":
    unittest.main()
