import unittest

from modular_smoke_test import run_smoke_test


class ModularSmokeTests(unittest.TestCase):
    def test_valid_case_passes(self):
        result = run_smoke_test()
        self.assertTrue(result["valid_case"]["ready"])
        self.assertEqual(result["valid_case"]["conflicts"], [])

    def test_deliberate_landmine_is_detected(self):
        result = run_smoke_test()
        self.assertFalse(result["landmine_case"]["ready"])
        self.assertTrue(result["landmine_case"]["detected"])
        self.assertTrue(
            any(
                item.startswith("self-conflict:")
                for item in result["landmine_case"]["conflicts"]
            )
        )


if __name__ == "__main__":
    unittest.main()
