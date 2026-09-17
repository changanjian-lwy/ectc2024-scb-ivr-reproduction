import unittest

from validation.r04d0_regression import validate_existing_result


class R04D0RegressionTests(unittest.TestCase):
    def test_p24_first_interval_shared_ladder(self):
        result = validate_existing_result()
        self.assertTrue(result["passed"], result)
        self.assertIn("not a self-balance", result["claim_boundary"])
        self.assertIn("ZVS claim", result["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
