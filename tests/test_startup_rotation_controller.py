import unittest

from scb_ivr.evidence import Evidence
from scb_ivr.startup_rotation_controller import (
    RotationBranch,
    RotationController,
    StartupEvent,
    StartupState,
    assert_gate_interlock,
)


class StartupRotationControllerTests(unittest.TestCase):
    def test_p24_stops_before_unpublished_phase_handoff(self):
        c = RotationController(4, RotationBranch.P24_MINIMAL)
        for event in (
            StartupEvent.ACTIVE_CURRENT_LIMIT,
            StartupEvent.ACTIVE_LOW_SIDE_VDS_ZERO,
            StartupEvent.ACTIVE_CURRENT_ZERO,
            StartupEvent.ACTIVE_NEGATIVE_TARGET,
            StartupEvent.ACTIVE_HIGH_SIDE_VDS_ZERO,
        ):
            c = c.transition(event)
            assert_gate_interlock(c)
        self.assertEqual(c.state, StartupState.BLOCKED_P24_HANDOFF_UNPUBLISHED)
        self.assertEqual(c.active_phase, 1)
        self.assertEqual(c.evidence, Evidence.P24_EXPLICIT)

    def test_p25_extension_rotates_four_to_one(self):
        c = RotationController(
            4,
            RotationBranch.P25_TO_P24_FOUR_PHASE_EXTENSION,
            active_phase=4,
        )
        for event in (
            StartupEvent.ACTIVE_CURRENT_LIMIT,
            StartupEvent.ACTIVE_LOW_SIDE_VDS_ZERO,
            StartupEvent.NEXT_CURRENT_ZERO,
            StartupEvent.NEXT_NEGATIVE_TARGET,
            StartupEvent.NEXT_HIGH_SIDE_VDS_ZERO,
        ):
            c = c.transition(event)
            assert_gate_interlock(c)
        self.assertEqual(c.active_phase, 1)
        self.assertEqual(c.cycles_completed, 1)
        self.assertEqual(c.evidence, Evidence.CROSS_PAPER_EXTENSION)

    def test_extension_completes_four_handoffs(self):
        c = RotationController(4, RotationBranch.P25_TO_P24_FOUR_PHASE_EXTENSION)
        events = (
            StartupEvent.ACTIVE_CURRENT_LIMIT,
            StartupEvent.ACTIVE_LOW_SIDE_VDS_ZERO,
            StartupEvent.NEXT_CURRENT_ZERO,
            StartupEvent.NEXT_NEGATIVE_TARGET,
            StartupEvent.NEXT_HIGH_SIDE_VDS_ZERO,
        )
        for _ in range(4):
            for event in events:
                c = c.transition(event)
                assert_gate_interlock(c)
        self.assertEqual(c.active_phase, 1)
        self.assertEqual(c.cycles_completed, 4)

    def test_planted_out_of_order_event_is_detected(self):
        c = RotationController(4, RotationBranch.P25_TO_P24_FOUR_PHASE_EXTENSION)
        with self.assertRaisesRegex(ValueError, "illegal event"):
            c.transition(StartupEvent.NEXT_HIGH_SIDE_VDS_ZERO)

    def test_p25_energy_gate_vector_is_four_phase_extension(self):
        c = RotationController(4, RotationBranch.P25_TO_P24_FOUR_PHASE_EXTENSION)
        self.assertEqual(c.commanded_on(), ("S1a", "S2b", "S3b", "S4b"))
        assert_gate_interlock(c)


if __name__ == "__main__":
    unittest.main()
