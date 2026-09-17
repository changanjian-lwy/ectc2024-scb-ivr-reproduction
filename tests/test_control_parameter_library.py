import unittest

from scb_ivr.control_parameter_library import (
    P24_ONE_PERCENT,
    P25_FIVE_PERCENT,
    R04D3_GS61008T_SCALAR_MIN_ZVS,
    R04D3_IDEAL_OPERATING_EIGHT_PERCENT,
    current_model_default,
)
from scb_ivr.evidence import Evidence


class ControlParameterLibraryTests(unittest.TestCase):
    def test_paper_values_are_not_replaced_by_calibration(self):
        self.assertEqual(P24_ONE_PERCENT.fraction_of_phase_peak, 0.01)
        self.assertEqual(P25_FIVE_PERCENT.fraction_of_phase_peak, 0.05)
        self.assertEqual(P24_ONE_PERCENT.evidence, Evidence.P24_EXPLICIT)
        self.assertEqual(P25_FIVE_PERCENT.evidence, Evidence.P25_SUPPLEMENT)

    def test_current_model_default_is_scoped_calibration(self):
        target = current_model_default()
        self.assertIs(target, R04D3_IDEAL_OPERATING_EIGHT_PERCENT)
        self.assertEqual(target.fraction_of_phase_peak, 0.08)
        self.assertEqual(target.evidence, Evidence.MODEL_CALIBRATION)
        self.assertEqual(R04D3_GS61008T_SCALAR_MIN_ZVS.fraction_of_phase_peak, 0.0777)

    def test_current_target_has_negative_sign(self):
        self.assertAlmostEqual(current_model_default().current_a(125.0), -10.0)


if __name__ == "__main__":
    unittest.main()
