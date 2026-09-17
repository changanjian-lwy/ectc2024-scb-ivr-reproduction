import unittest

from scb_ivr.interval2_branches import P24_INTERVAL2, P25_INTERVAL2_EXTENDED_TO_FOUR_PHASE
from scb_ivr.physical_events import EventId, aliases_for_event, event_for_label


class PhysicalEventMappingTests(unittest.TestCase):
    def test_branches_share_physical_start(self):
        self.assertEqual(P24_INTERVAL2.start_event_id, P25_INTERVAL2_EXTENDED_TO_FOUR_PHASE.start_event_id)
        self.assertEqual(P24_INTERVAL2.start_event_id, EventId.PHASE1_HIGH_SIDE_OFF)

    def test_paper_t2_labels_map_to_different_events(self):
        self.assertEqual(event_for_label("P24", "t2"), (EventId.PHASE1_INDUCTOR_CURRENT_ZERO,))
        self.assertEqual(event_for_label("P25", "t2"), (EventId.PHASE1_LOW_SIDE_VDS_ZERO, EventId.PHASE1_LOW_SIDE_ON))

    def test_same_low_vds_event_has_paper_specific_aliases(self):
        aliases = aliases_for_event(EventId.PHASE1_LOW_SIDE_VDS_ZERO)
        by_paper = {alias.paper: alias.paper_label for alias in aliases}
        self.assertIsNone(by_paper["P24"])
        self.assertEqual(by_paper["P25"], "t2")

    def test_p25_t3_is_phase2_not_phase1_zero_crossing(self):
        self.assertEqual(event_for_label("P25", "t3"), (EventId.PHASE2_INDUCTOR_CURRENT_ZERO,))
        self.assertNotIn(EventId.PHASE1_INDUCTOR_CURRENT_ZERO, event_for_label("P25", "t3"))


if __name__ == "__main__":
    unittest.main()
