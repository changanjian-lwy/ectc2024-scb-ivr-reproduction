import unittest

from validation.r04a_regression import validate_existing_result


class R04ARegressionTests(unittest.TestCase):
    def test_previously_successful_local_boundary_case(self):
        result = validate_existing_result()
        self.assertTrue(result["assembly_ready"])
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["selected_modules"],
            [
                "p24_equations_1_to_6",
                "ideal_switch_pair",
                "ltspice_latched_event_memory",
                "p24_three_interval_phase_local_sequence",
                "p24_derived_single_phase_stiff_boundary",
            ],
        )


if __name__ == "__main__":
    unittest.main()
