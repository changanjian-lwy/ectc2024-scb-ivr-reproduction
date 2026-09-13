import unittest

from two_branch_revalidation import revalidate


class TwoBranchRevalidationTests(unittest.TestCase):
    def test_regressions_pass_but_overall_chains_are_not_overclaimed(self):
        result = revalidate()
        self.assertTrue(result["regressions_pass"])
        c = result["conclusions"]
        self.assertFalse(c["p24_source_native_complete"])
        self.assertTrue(c["p24_model_calibrated_local_chain"])
        self.assertFalse(c["p25_to_np4_continuous_chain"])
        self.assertFalse(c["p25_native_modes4_to6_continuous_from_mode3"])
        self.assertTrue(c["p25_native_mode4_local"])
        self.assertTrue(c["p25_native_mode5_local"])
        self.assertTrue(c["p25_native_mode6_qualitative"])
        self.assertFalse(c["p25_native_mode6_quantitative"])


if __name__ == "__main__":
    unittest.main()
