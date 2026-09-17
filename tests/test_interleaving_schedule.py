import unittest

from scb_ivr.interleaving_schedule import (
    audit_naive_two_level_interleaving,
    build_single_module_phase_schedule,
    ideal_total_event_spacing_cycles,
    paper_module_origin_shift_cycles,
)


class InterleavingScheduleTests(unittest.TestCase):
    def test_paper_module_shift_is_independent_of_phase_count(self):
        self.assertEqual(paper_module_origin_shift_cycles(4, 4), 1 / 4)

    def test_single_phase_is_explicit_not_omitted(self):
        self.assertEqual(paper_module_origin_shift_cycles(1, 4), 1 / 4)

    def test_single_module_four_phase_absolute_origins(self):
        schedule = build_single_module_phase_schedule(
            phases=4,
            modules=1,
            reference_time_s=1e-9,
            switching_period_s=200e-9,
            high_side_on_time_s=16.6666666667e-9,
        )
        self.assertEqual(schedule.phases_per_module, 4)
        self.assertEqual(schedule.modules, 1)
        self.assertAlmostEqual(schedule.phase_spacing_s, 50e-9)
        self.assertAlmostEqual(schedule.module_spacing_s, 200e-9)
        self.assertEqual(
            [round(event.phase_origin_s / 1e-9, 9) for event in schedule.events],
            [1.0, 51.0, 101.0, 151.0],
        )
        self.assertEqual(
            [round(event.high_side_off_s / 1e-9, 9) for event in schedule.events],
            [17.666666667, 67.666666667, 117.666666667, 167.666666667],
        )

    def test_single_module_builder_keeps_nM_explicit(self):
        with self.assertRaisesRegex(ValueError, "modules=1"):
            build_single_module_phase_schedule(
                phases=4,
                modules=2,
                reference_time_s=0,
                switching_period_s=200e-9,
                high_side_on_time_s=16.7e-9,
            )

    def test_phase_argument_is_mandatory_and_validated(self):
        with self.assertRaises(ValueError):
            paper_module_origin_shift_cycles(0, 4)

    def test_ideal_total_event_spacing_uses_both_counts(self):
        self.assertEqual(ideal_total_event_spacing_cycles(4, 4), 1 / 16)

    def test_p25_three_phase_two_module_example_has_no_collision(self):
        audit = audit_naive_two_level_interleaving(3, 2)
        self.assertFalse(audit.has_collisions)
        self.assertEqual(audit.unique_event_times, 6)

    def test_p24_four_phase_four_module_target_has_collisions_under_naive_rule(self):
        audit = audit_naive_two_level_interleaving(4, 4)
        self.assertTrue(audit.has_collisions)
        self.assertEqual(audit.total_nominal_events, 16)
        self.assertEqual(audit.unique_event_times, 4)
        self.assertEqual(audit.collision_multiplicity, 4)


if __name__ == "__main__":
    unittest.main()
