import unittest

from validation.r04d4a_regression import validate_existing_result


class R04D4AP25Mode4Tests(unittest.TestCase):
    def test_p25_native_five_percent_boundary(self):
        result = validate_existing_result()
        self.assertTrue(result["passed"], result)


if __name__ == "__main__":
    unittest.main()
