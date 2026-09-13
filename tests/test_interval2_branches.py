import unittest

from evidence import Evidence
from interval2_branches import (
    P24_INTERVAL2,
    P25_INTERVAL2_EXTENDED_TO_FOUR_PHASE,
)


class Interval2BranchTests(unittest.TestCase):
    def test_t2_definitions_are_not_shared(self):
        self.assertIn("iL1 reaches zero", P24_INTERVAL2.end_event)
        self.assertIn("SL1 turns on", P25_INTERVAL2_EXTENDED_TO_FOUR_PHASE.end_event)
        self.assertNotEqual(P24_INTERVAL2.end_event, P25_INTERVAL2_EXTENDED_TO_FOUR_PHASE.end_event)

    def test_p24_remaining_gates_stay_unspecified(self):
        self.assertIn("remaining gates unspecified", P24_INTERVAL2.commanded_context)
        self.assertEqual(P24_INTERVAL2.evidence, Evidence.P24_EXPLICIT)

    def test_p25_four_phase_mapping_stays_extension(self):
        self.assertIn("SL4=ON", P25_INTERVAL2_EXTENDED_TO_FOUR_PHASE.commanded_context[-1])
        self.assertEqual(
            P25_INTERVAL2_EXTENDED_TO_FOUR_PHASE.evidence,
            Evidence.CROSS_PAPER_EXTENSION,
        )


if __name__ == "__main__":
    unittest.main()
