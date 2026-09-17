import unittest
from validation.r04d5a_regression import validate_existing_result as validate5
from validation.r04d6a_regression import validate_existing_result as validate6

class Mode56RunTests(unittest.TestCase):
    def test_mode5_zvs_exit(self): self.assertTrue(validate5()["passed"],validate5())
    def test_mode6_mismatch_is_detected_not_hidden(self): self.assertTrue(validate6()["passed"],validate6())

if __name__=="__main__":unittest.main()
