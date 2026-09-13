import unittest

from periodic_current_seed import interleaved_initial_currents


class PeriodicCurrentSeedTests(unittest.TestCase):
    def test_p24_four_phase_seed(self):
        currents = interleaved_initial_currents(
            n_p=4,
            period_s=200e-9,
            on_time_s=200e-9 / 12,
            peak_a=125,
        )
        expected = (0.0, 34.0909090909, 68.1818181818, 102.2727272727)
        for actual, target in zip(currents, expected):
            self.assertAlmostEqual(actual, target, places=8)

    def test_phase_count_is_not_implicit(self):
        with self.assertRaises(ValueError):
            interleaved_initial_currents(
                n_p=0, period_s=200e-9, on_time_s=16.67e-9, peak_a=125
            )


if __name__ == "__main__":
    unittest.main()
