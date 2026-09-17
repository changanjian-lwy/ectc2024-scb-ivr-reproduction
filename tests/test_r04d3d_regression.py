import unittest

from validation.r04d3d_regression import validate_existing_result


class R04D3DThresholdTests(unittest.TestCase):
    def test_refined_threshold_is_locked(self):
        result = validate_existing_result()
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["threshold_fraction"], 0.0777)


if __name__ == "__main__":
    unittest.main()
