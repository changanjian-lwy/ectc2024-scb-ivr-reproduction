import unittest

from scb_ivr.phase_local_timeline import (
    assert_event_not_replaced_by_global_clock,
    build_phase_frames,
    phase_local_time,
)


class PhaseLocalTimelineTests(unittest.TestCase):
    def test_four_phase_coordinates_at_global_zero(self):
        frames = build_phase_frames(0.0, phases=4, period_s=200e-9)
        self.assertEqual(
            [round(f.local_cycle_time_s / 1e-9, 9) for f in frames],
            [0.0, 150.0, 100.0, 50.0],
        )

    def test_next_origins_are_interleaved_by_50ns(self):
        frames = build_phase_frames(1e-15, phases=4, period_s=200e-9)
        values = [round(f.time_to_next_origin_s / 1e-9, 6) for f in frames]
        self.assertEqual(values, [199.999999, 49.999999, 99.999999, 149.999999])

    def test_time_coordinate_does_not_claim_a_mode(self):
        frames = build_phase_frames(0.0, phases=4, period_s=200e-9)
        self.assertTrue(all(f.mode is None for f in frames))
        self.assertTrue(all(f.mode_status == "REQUIRES_EVENT_HISTORY" for f in frames))

    def test_phase_count_cannot_be_omitted_as_zero(self):
        with self.assertRaises(ValueError):
            phase_local_time(0.0, phase_index=1, phases=0, period_s=200e-9)

    def test_planted_global_clock_substitution_is_detected(self):
        # Deliberate mine: a nominal 50 ns origin is present but Vds-zero is not.
        with self.assertRaisesRegex(RuntimeError, "global clock edge cannot replace"):
            assert_event_not_replaced_by_global_clock(
                event_name="PHASE2_HIGH_SIDE_VDS_ZERO", event_observed=False
            )


if __name__ == "__main__":
    unittest.main()
