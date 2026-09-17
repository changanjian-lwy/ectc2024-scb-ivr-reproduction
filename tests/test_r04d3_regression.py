import unittest

from validation.r04d3_regression import validate_existing_results


class R04D3RegressionTests(unittest.TestCase):
    def test_recorded_branch_outcomes_remain_separate_and_reproducible(self):
        result = validate_existing_results()
        self.assertTrue(result["passed"], result)


if __name__ == "__main__":
    unittest.main()
