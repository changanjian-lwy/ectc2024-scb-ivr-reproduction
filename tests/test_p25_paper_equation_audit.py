"""D09 synthetic algebra checks, not paper prototype simulations or fits."""
import unittest
import numpy as np
from scb_ivr.p25_native_events import NativeBoundary
from scb_ivr.p25_nodal_contract import Components, instantaneous_rates, reduced_commutation_coefficients


class PaperEquationAuditTests(unittest.TestCase):
    def setUp(self):
        self.boundary = NativeBoundary(3, 1, 1, "dynamic_Co_current_ports", .05)
        self.parts = Components((1.,)*6, (0.,)*6, (17.,19.), 23.,
                                (2.,3.,4.), (0.,)*3, "synthetic algebra fixture; not design data")

    def rates(self, mode, v, currents):
        return instantaneous_rates(self.boundary, self.parts, mode,
            voltage_v=v, current_a=currents, vin_v=15., dvin_v_s=0.,
            load_current_a=1., other_modules_current_a=0., constraint_tolerance_v=1e-12,
            reverse_path_regime="off_reverse_channels_excluded_until_admission")

    def test_m1_paper_zero_drop_slopes(self):
        # Cs1 voltage=15-5=10; instantaneous slope, NOT frozen Cs dynamics.
        r = self.rates("M1", [15.,6.,5.,0.,0.,2.], [0.,2.,3.])
        np.testing.assert_allclose(r.current_rate_a_s, [(15-10-2)/2,-2/3,-2/4])

    def test_m3_m4_same_kvl_even_after_current_zero(self):
        for mode, currents in (("M3", [3.,1.,2.]), ("M4", [3.,-.1,2.])):
            with self.subTest(mode=mode):
                r = self.rates(mode, [10.,6.,0.,0.,0.,2.], currents)
                np.testing.assert_allclose(r.current_rate_a_s, [-1.,-2/3,-.5])

    def test_m6_output_term_cannot_be_dropped(self):
        base = self.rates("M6", [10.,10.,0.,4.,0.,1.], [3.,-.2,2.])
        changed = self.rates("M6", [10.,10.,0.,4.,0.,2.], [3.,-.2,2.])
        self.assertAlmostEqual(base.current_rate_a_s[1], 1.)
        self.assertAlmostEqual(changed.current_rate_a_s[1]-base.current_rate_a_s[1], -1/3)
        self.assertNotAlmostEqual(base.current_rate_a_s[1], 4/3)  # planted missing-Vo formula

    def test_equal_switch_caps_large_flying_limit_is_three_not_two(self):
        # Limit evaluation only, not a finite-Cs paper operating point.
        parts = Components((1.,)*6, (0.,)*6, (1e8,1e8), 23.,
                           (2.,3.,4.), (0.,)*3, "synthetic dimensionless-ratio limit fixture")
        for mode in ("M2", "M5"):
            with self.subTest(mode=mode):
                reduction = reduced_commutation_coefficients(parts, mode)
                effective = reduction["ceff_f"] / abs(reduction["target_gain"])
                self.assertAlmostEqual(effective, 3., places=6)
                self.assertGreater(abs(effective-2.), .9)

    def test_eq13_root_requires_negative_interval_not_high_on_time(self):
        # Values purely algebraic; no claim that this tuple is a feasible orbit.
        L, C, U, V, tneg, ton = 3.,2.,4.,2.,.6,1.5
        slope = V*tneg/(2*L*C)
        derived_time = 2*L*C*U/(V*tneg)
        printed14_time = 2*L*C*U/(V*ton)
        self.assertAlmostEqual(U-slope*derived_time, 0.)
        self.assertNotAlmostEqual(U-slope*printed14_time, 0.)
        self.assertAlmostEqual(printed14_time/derived_time, tneg/ton)


if __name__ == "__main__":
    unittest.main()
