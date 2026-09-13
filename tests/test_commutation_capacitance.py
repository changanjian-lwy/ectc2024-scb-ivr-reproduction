import unittest

from commutation_capacitance import from_device_population
from device_library import GS61008T


class CommutationCapacitanceTests(unittest.TestCase):
    def test_device_and_snubber_remain_separate(self):
        caps = from_device_population(
            GS61008T,
            high_parallel=1,
            low_parallel=2,
            high_snubber_f=1e-9,
            low_snubber_f=2e-9,
        )
        self.assertEqual(caps.high_device_f, 385e-12)
        self.assertEqual(caps.low_device_f, 770e-12)
        self.assertEqual(caps.high_total_f, 1.385e-9)
        self.assertEqual(caps.low_total_f, 2.770e-9)

    def test_zero_snubber_keeps_device_coss(self):
        caps = from_device_population(GS61008T, high_parallel=1, low_parallel=2)
        self.assertEqual(caps.high_total_f, 385e-12)
        self.assertEqual(caps.low_total_f, 770e-12)

    def test_negative_snubber_is_rejected(self):
        with self.assertRaises(ValueError):
            from_device_population(
                GS61008T,
                high_parallel=1,
                low_parallel=2,
                high_snubber_f=-1e-12,
            )


if __name__ == "__main__":
    unittest.main()
