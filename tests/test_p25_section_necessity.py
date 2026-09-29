"""D33: do not present a positive-i1 diagnostic seed as a periodic candidate."""
from dataclasses import replace
import unittest
import test_p25_seed_evaluation as fixtures
from scb_ivr.p25_section_necessity import section_return_necessity


class SectionNecessityTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.SeedEvaluationTests(); self.f.setUp()

    def check(self, current):
        seed = replace(self.f.seed, current_a=(current,2.,3.))
        memory = self.f.contract.make_candidate(seed)
        return section_return_necessity(memory, current_margin_a=1e-8)

    def test_baseline_and_its_i1_neighborhood_cannot_be_periodic(self):
        for i in (18.,20.,22.):
            r = self.check(i)
            self.assertEqual(r.status, "EXCLUDED_FROM_EXACT_PERIODIC_RETURN")
            self.assertEqual(r.distance_to_nonpositive_domain_a, i)

    def test_negative_current_is_only_necessary_not_success(self):
        r = self.check(-1.)
        self.assertEqual(r.status, "NECESSARY_DIRECTION_PASSED_NOT_SUFFICIENT")

    def test_zero_boundary_and_small_positive_residual_are_unresolved(self):
        for i in (0., 1e-9, -1e-9):
            self.assertEqual(self.check(i).status, "ZERO_CURRENT_BOUNDARY_UNRESOLVED")

    def test_missing_margin_is_not_invented(self):
        memory = self.f.contract.make_candidate(self.f.seed)
        with self.assertRaises(ValueError):
            section_return_necessity(memory, current_margin_a=-1.)


if __name__ == "__main__":
    unittest.main()
