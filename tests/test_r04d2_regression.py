import unittest

from validation.r04d2_regression import validate_existing_results


class R04D2RegressionTests(unittest.TestCase):
    def test_separate_interval2_endpoints(self):
        result = validate_existing_results()
        self.assertTrue(result["passed"], result)
        self.assertIn("separate published t2 labels", result["claim_boundary"])
        self.assertIn("nP=4 extension", result["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
