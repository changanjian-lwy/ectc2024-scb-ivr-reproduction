import unittest

from validation.r04d3e_regression import validate_existing_result


class R04D3EExitAcceptanceTests(unittest.TestCase):
    def test_calibrated_exit_has_correct_causal_order(self):
        result = validate_existing_result()
        self.assertTrue(result["passed"], result)
        self.assertLess(result["measurements"]["il_high_on_a"], 0)


if __name__ == "__main__":
    unittest.main()
