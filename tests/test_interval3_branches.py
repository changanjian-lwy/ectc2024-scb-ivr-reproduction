import unittest

from scb_ivr.interval3_branches import P24_INTERVAL3, P25_INTERVAL3_EXTENDED_TO_FOUR_PHASE
from scb_ivr.physical_events import EventId


class Interval3BranchTests(unittest.TestCase):
    def test_p24_starts_at_phase1_current_zero(self):
        self.assertEqual(P24_INTERVAL3.start_event_ids, (EventId.PHASE1_INDUCTOR_CURRENT_ZERO,))

    def test_p25_starts_at_phase1_low_side_zvs_boundary(self):
        self.assertEqual(
            P25_INTERVAL3_EXTENDED_TO_FOUR_PHASE.start_event_ids,
            (EventId.PHASE1_LOW_SIDE_VDS_ZERO, EventId.PHASE1_LOW_SIDE_ON),
        )

    def test_papers_end_on_different_physical_events(self):
        self.assertEqual(P25_INTERVAL3_EXTENDED_TO_FOUR_PHASE.end_event_ids, (EventId.PHASE2_INDUCTOR_CURRENT_ZERO,))
        self.assertNotEqual(P24_INTERVAL3.end_event_ids, P25_INTERVAL3_EXTENDED_TO_FOUR_PHASE.end_event_ids)

    def test_np4_extension_keeps_all_low_sides_explicit(self):
        self.assertEqual(P25_INTERVAL3_EXTENDED_TO_FOUR_PHASE.explicitly_on, ("SL1", "SL2", "SL3", "SL4"))


if __name__ == "__main__":
    unittest.main()
