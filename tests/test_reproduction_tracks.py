import unittest

from scb_ivr.evidence import Evidence
from scb_ivr.periodic_state_contract import (
    FourPhasePeriodicState,
    p24_voltage_guess,
    phase1_origin_fast_seed,
    residual,
)
from scb_ivr.reproduction_tracks import TRACK_A, TRACK_B, assert_tracks_do_not_merge


class ReproductionTrackTests(unittest.TestCase):
    def test_tracks_are_separate(self):
        assert_tracks_do_not_merge()
        self.assertTrue(TRACK_A.required_for_p24_reproduction)
        self.assertFalse(TRACK_B.required_for_p24_reproduction)
        self.assertEqual(TRACK_B.evidence, Evidence.EXPLORATORY_ASSUMPTION)

    def test_36_24_12_is_only_a_seed(self):
        self.assertEqual(p24_voltage_guess(48.0, 4), (36.0, 24.0, 12.0))
        self.assertIn("initial guess", TRACK_A.allowed_initialization)

    def test_full_state_residual_detects_planted_current_error(self):
        initial = FourPhasePeriodicState((36, 24, 12), (0, 0, 0, 0), 1)
        final = FourPhasePeriodicState((36, 24, 12), (0, 0, 3, 0), 1)
        result = residual(initial, final)
        self.assertEqual(result.inductor_delta_a, (0, 0, 3, 0))
        self.assertEqual(result.max_abs, 3)

    def test_fast_coss_seed_is_consistent_with_phase1_origin(self):
        fast = phase1_origin_fast_seed(48.0, 4)
        self.assertEqual(fast.high_side_nodes_v, (48.0, 24.0, 12.0))
        self.assertEqual(fast.switching_nodes_v, (12.0, 0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
