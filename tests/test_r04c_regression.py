import unittest

from validation.r04c_regression import validate_existing_result


class R04CRegressionTests(unittest.TestCase):
    def test_four_phase_local_boundary_replay(self):
        result = validate_existing_result()
        self.assertTrue(result["passed"], result)
        self.assertIn("local analytical", result["claim_boundary"])
        self.assertIn("no flying-capacitor", result["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
