import unittest

from scb_ivr.feasibility_envelope import (
    OperatingPoint,
    corrected_peak_current_a,
    envelope_point,
    evaluate_commutation_admission,
    maximum_commutation_charge_c,
)


class FeasibilityEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.p25 = OperatingPoint(12.0, 1.0, 200.0, 3, 3, 0.5e6)

    def test_zero_valley_recovers_paper_peak_formula(self):
        self.assertAlmostEqual(corrected_peak_current_a(self.p25, 0), 44.4444444444)

    def test_five_percent_negative_valley_correction(self):
        point = envelope_point(self.p25, 22e-9, 0.05)
        self.assertAlmostEqual(point.corrected_peak_current_a, 46.783625731, places=8)
        self.assertAlmostEqual(point.negative_current_a, 2.339181287, places=8)

    def test_p25_ramp_closure_keeps_both_peak_conventions_visible(self):
        point = envelope_point(self.p25, 22e-9, 0.05)
        self.assertAlmostEqual(
            point.required_ramp_inductance_paper_peak_h * 1e9,
            32.1428571,
            places=6,
        )
        self.assertAlmostEqual(
            point.required_ramp_inductance_corrected_peak_h * 1e9,
            30.5357143,
            places=6,
        )
        self.assertLess(point.selected_over_required_corrected_inductance, 0.8)

    def test_unknown_device_data_cannot_false_pass(self):
        result = evaluate_commutation_admission(
            inductance_h=22e-9,
            available_negative_current_a=2.3,
        )
        self.assertIsNone(result.admitted)
        self.assertIsNone(result.energy_gate)
        self.assertIsNone(result.charge_time_gate)

    def test_energy_and_charge_gates_are_both_required(self):
        result = evaluate_commutation_admission(
            inductance_h=10e-9,
            available_negative_current_a=2.0,
            commutation_energy_j=10e-9,
            commutation_charge_c=3e-9,
            available_time_s=1e-9,
        )
        self.assertTrue(result.energy_gate)
        self.assertFalse(result.charge_time_gate)
        self.assertFalse(result.admitted)

    def test_charge_ceiling_is_linear_in_time(self):
        self.assertEqual(maximum_commutation_charge_c(2.0, 3e-9), 6e-9)


if __name__ == "__main__":
    unittest.main()
