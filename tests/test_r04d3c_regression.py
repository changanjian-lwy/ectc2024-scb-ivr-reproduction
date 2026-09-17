import unittest

from validation.r04d3c_regression import validate_existing_result


class R04D3CFivePercentTests(unittest.TestCase):
    def test_five_percent_result_is_locked_as_partial_commutation_failure(self):
        result = validate_existing_result()
        self.assertTrue(result["passed"], result)


if __name__ == "__main__":
    unittest.main()
