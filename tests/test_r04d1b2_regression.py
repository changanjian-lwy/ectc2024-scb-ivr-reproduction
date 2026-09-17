import unittest

from validation.r04d1b2_regression import validate_existing_result


class R04D1B2RegressionTests(unittest.TestCase):
    def test_gs61008t_device_only_branch(self):
        result = validate_existing_result()
        self.assertTrue(result["passed"], result)
        self.assertIn("device-only", result["claim_boundary"])
        self.assertIn("excludes", result["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
