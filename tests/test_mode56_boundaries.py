import unittest

from scb_ivr.mode56_boundaries import P25_MODE5, P25_MODE6
from scb_ivr.physical_events import EventId, event_for_label


class Mode56BoundaryTests(unittest.TestCase):
    def test_mode5_t5_and_t6_are_physical_events(self):
        self.assertEqual(P25_MODE5.start_events, (EventId.PHASE2_LOW_SIDE_OFF,))
        self.assertIn(EventId.PHASE2_HIGH_SIDE_ON, P25_MODE5.end_events)
        self.assertEqual(event_for_label("P25", "t5"), (EventId.PHASE2_LOW_SIDE_OFF,))

    def test_mode6_starts_at_mode5_high_side_on(self):
        self.assertEqual(P25_MODE6.start_events, (EventId.PHASE2_HIGH_SIDE_ON,))
        self.assertEqual(P25_MODE6.end_events, (EventId.PHASE2_INDUCTOR_CURRENT_PEAK,))

    def test_mode6_end_does_not_invent_a_paper_label(self):
        self.assertIn("printed", P25_MODE6.source_time_span)


if __name__ == "__main__":
    unittest.main()
