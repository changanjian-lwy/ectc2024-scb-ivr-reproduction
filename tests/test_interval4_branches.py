import unittest

from scb_ivr.interval4_branches import P25_MODE4
from scb_ivr.physical_events import EventId, event_for_label


class P25Mode4BoundaryTests(unittest.TestCase):
    def test_mode4_is_phase2_zero_to_negative_target(self):
        self.assertEqual(P25_MODE4.start_event, EventId.PHASE2_INDUCTOR_CURRENT_ZERO)
        self.assertEqual(P25_MODE4.end_event, EventId.PHASE2_NEGATIVE_CURRENT_TARGET)
        self.assertEqual(
            event_for_label("P25", "t4"),
            (EventId.PHASE2_NEGATIVE_CURRENT_TARGET, EventId.PHASE2_LOW_SIDE_OFF_COMMAND),
        )

    def test_source_range_and_design_selection_remain_distinct(self):
        self.assertEqual(P25_MODE4.textual_range, (0.05, 0.10))
        self.assertEqual(P25_MODE4.design_negative_fraction, 0.05)

    def test_other_phase_values_are_sign_contracts_not_invented_numbers(self):
        self.assertEqual(P25_MODE4.other_phase_sign_contracts, ("iL1 > 0 and decreasing", "iL3 > 0 and decreasing"))


if __name__ == "__main__":
    unittest.main()
