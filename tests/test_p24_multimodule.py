"""D61 (src/scb_ivr/p24_multimodule.py): sharing, interleaving and the negative current on a shared output."""
import unittest

from scb_ivr.p24_multimodule import drift_time_us, i_neg_for_equal_current, module_current, simulate
from scb_ivr.p24_startup_averaged import Module


class MultiModule(unittest.TestCase):
    def test_negative_current_equalises_the_current(self):
        m = Module()
        for eps in (-0.1, 0.05):
            i = module_current(m, 568.0, 1.0, eps=eps, i_neg=i_neg_for_equal_current(m, eps))
            self.assertAlmostEqual(i, module_current(m, 568.0, 1.0), places=9)

    def test_one_lsb_of_ton_slips_a_slot_within_ten_us(self):
        self.assertLess(drift_time_us(Module(), 1), 10.0)

    def test_independent_integrators_diverge_and_a_shared_loop_does_not(self):
        off = (0.5e-3, 0.0, 0.0, -0.5e-3)
        t, vo, I, N = simulate("independent", adc_offset_v=off, t_end=200e-6)
        s1 = I[len(t) // 2].max() - I[len(t) // 2].min(); s2 = I[-1].max() - I[-1].min()
        self.assertGreater(s2, s1 + 5.0)
        t, vo, I, N = simulate("shared", eps=(0.05, 0.0, 0.0, -0.05), t_end=200e-6)
        self.assertLess(abs((I[-1].max() - I[-1].min()) - (I[len(t) // 2].max() - I[len(t) // 2].min())), 0.5)


if __name__ == "__main__":
    unittest.main()
