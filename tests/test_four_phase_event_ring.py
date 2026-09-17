import unittest

from scb_ivr.four_phase_event_ring import (
    LocalEvent,
    P24_LOCAL_EVENT_ORDER,
    build_p24_event_rings,
    validate_observed_prefix,
)


class FourPhaseEventRingTests(unittest.TestCase):
    def test_four_phase_rotation_wraps(self):
        rings = build_p24_event_rings(4)
        self.assertEqual([r.next_phase_index for r in rings], [2, 3, 4, 1])
        self.assertEqual(
            [r.adjacent_support_low_side for r in rings],
            ["L2", "L3", "L4", "L1"],
        )

    def test_every_phase_uses_identical_local_event_order(self):
        rings = build_p24_event_rings(4)
        self.assertTrue(all(r.events == P24_LOCAL_EVENT_ORDER for r in rings))

    def test_zvs_cannot_precede_negative_target_and_low_off(self):
        ring = build_p24_event_rings(4)[1]
        bad = (
            LocalEvent.HIGH_SIDE_ON,
            LocalEvent.HIGH_SIDE_OFF,
            LocalEvent.HIGH_SIDE_VDS_ZERO,
        )
        with self.assertRaisesRegex(RuntimeError, "event order mismatch"):
            validate_observed_prefix(ring, bad)

    def test_valid_partial_prefix_is_accepted(self):
        ring = build_p24_event_rings(4)[0]
        validate_observed_prefix(ring, P24_LOCAL_EVENT_ORDER[:4])

    def test_phase_count_is_never_implicit(self):
        with self.assertRaises(ValueError):
            build_p24_event_rings(1)


if __name__ == "__main__":
    unittest.main()
