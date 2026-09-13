import unittest

from r04d1b_regression import validate_existing_result


class R04D1BRegressionTests(unittest.TestCase):
    def test_bounded_capacitance_sensitivity(self):
        result = validate_existing_result()
        self.assertTrue(result["passed"], result)
        self.assertIn("not P24 device data", result["claim_boundary"])
        self.assertIn("post-zero overshoot is invalid", result["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
