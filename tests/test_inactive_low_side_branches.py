import unittest

from evidence import Evidence
from inactive_low_side_branches import (
    P24_MINIMAL_PHASE1,
    P25_EXPANDED_TO_FOUR_PHASE,
)
from r04d0e_regression import validate_existing_result


class InactiveLowSideBranchTests(unittest.TestCase):
    def test_p24_omission_does_not_become_off_command(self):
        self.assertEqual(P24_MINIMAL_PHASE1.commanded_on, ("QH1", "QS2"))
        self.assertIn("remaining low-side switches", P24_MINIMAL_PHASE1.unspecified)

    def test_p25_four_phase_branch_is_extension(self):
        self.assertEqual(
            P25_EXPANDED_TO_FOUR_PHASE.evidence, Evidence.CROSS_PAPER_EXTENSION
        )
        self.assertEqual(
            P25_EXPANDED_TO_FOUR_PHASE.commanded_on,
            ("SH1", "SL2", "SL3", "SL4"),
        )

    def test_p25_expanded_first_interval_result(self):
        result = validate_existing_result()
        self.assertTrue(result["passed"], result)
        self.assertIn("not an explicit P24", result["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
