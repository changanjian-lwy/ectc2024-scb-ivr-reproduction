import unittest

from scb_ivr.evidence import Evidence
from scb_ivr.startup_pulse_strategy import PredictivePulseRequest, calculate_predictive_pulse


class StartupPulseStrategyTests(unittest.TestCase):
    def test_zero_state_phase1_pulse_is_calculated_not_fitted(self):
        pulse = calculate_predictive_pulse(
            PredictivePulseRequest(1.4666666666666667e-9, 48.0, 0.0, 10.0, 2e-9, 4)
        )
        self.assertTrue(pulse.enabled)
        self.assertAlmostEqual(pulse.pulse_width_s, 0.3055555555555556e-9)
        self.assertAlmostEqual(pulse.predicted_delta_current_a, 10.0)
        self.assertEqual(pulse.evidence, Evidence.EXPLORATORY_ASSUMPTION)

    def test_phase_without_positive_voltage_is_not_pulsed(self):
        pulse = calculate_predictive_pulse(
            PredictivePulseRequest(1.4666666666666667e-9, 0.0, 1.0, 10.0, 2e-9, 4)
        )
        self.assertFalse(pulse.enabled)
        self.assertEqual(pulse.pulse_width_s, 0.0)

    def test_maximum_width_is_a_real_boundary(self):
        pulse = calculate_predictive_pulse(
            PredictivePulseRequest(1.4666666666666667e-9, 12.0, 1.0, 100.0, 1e-9, 4)
        )
        self.assertEqual(pulse.pulse_width_s, 1e-9)
        self.assertAlmostEqual(pulse.predicted_delta_current_a, 7.5)

    def test_n_p_cannot_be_omitted_semantically(self):
        with self.assertRaises(ValueError):
            calculate_predictive_pulse(
                PredictivePulseRequest(1e-9, 12.0, 1.0, 10.0, 1e-9, 0)
            )


if __name__ == "__main__":
    unittest.main()
