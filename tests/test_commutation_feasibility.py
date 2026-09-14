import unittest

from commutation_feasibility import (
    ideal_current_endpoint_a,
    isolated_lc_minimum_current_a,
    maximum_capacitance_for_time_f,
    p25_mode5_commutation_time_s,
    rl_current_endpoint_a,
)


class A40AnalyticalFeasibilityTests(unittest.TestCase):
    L = 1.466666666666667e-9
    TON = 16.6666666666667e-9

    def test_p24_lossless_zero_admission_reaches_125a(self):
        self.assertAlmostEqual(
            ideal_current_endpoint_a(0.0, 11.0, self.L, self.TON), 125.0
        )

    def test_device_augmented_zero_admission_is_not_125a(self):
        endpoint = rl_current_endpoint_a(0.0, 11.0, self.L, 7e-3, self.TON)
        self.assertAlmostEqual(endpoint, 120.1576512658)

    def test_p25_time_ceiling_requires_explicit_available_time(self):
        ceiling = maximum_capacitance_for_time_f(2.5, 12.0, 3.696e-9)
        self.assertAlmostEqual(ceiling, 385e-12)

    def test_isolated_lc_envelope_is_separate_from_p25_time_law(self):
        minimum = isolated_lc_minimum_current_a(self.L, 385e-12, 12.0)
        self.assertAlmostEqual(minimum / 125.0, 0.04918536368)

    def test_p25_commutation_time_for_385pf_at_two_percent(self):
        tcomm = p25_mode5_commutation_time_s(385e-12, 12.0, 2.5)
        self.assertAlmostEqual(tcomm, 3.696e-9)

    def test_rl_zero_resistance_has_lossless_limit(self):
        self.assertEqual(
            rl_current_endpoint_a(1.0, 11.0, self.L, 0.0, self.TON),
            ideal_current_endpoint_a(1.0, 11.0, self.L, self.TON),
        )


if __name__ == "__main__":
    unittest.main()
