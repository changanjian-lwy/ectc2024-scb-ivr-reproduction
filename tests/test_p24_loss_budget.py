"""D62 (src/scb_ivr/p24_loss_budget.py): the loss budget's terms."""
import unittest

from scb_ivr.p24_loss_budget import RON_MAX, budget, hard_on_energy, ms, phase_ms


class LossBudget(unittest.TestCase):
    def test_mean_square_of_a_segment(self):
        self.assertAlmostEqual(ms(0.0, 3.0), 3.0)                 # (0 + 0 + 9) / 3
        self.assertAlmostEqual(ms(-1.0, 1.0), 1.0 / 3.0)

    def test_conduction_matches_the_plants_duty_weighted_resistance(self):
        # the plant's 0.54 mOhm per phase is RDS(on) max duty-weighted at D = 1/12 (A72): the same order as the split form
        hs, ls, _ = phase_ms(-6.25, 134.0, 17.75e-9, 232.0e-9)
        split = hs * RON_MAX / 2 + ls * RON_MAX / 3
        lumped = (hs + ls) * 0.54e-3
        self.assertLess(abs(split / lumped - 1), 0.03)

    def test_hard_turn_on_matches_the_extensions_d56(self):
        from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit, Model
        k = EdgeCircuit()
        e = Model(k).hard_on_energy(k.v_rail - 8.98)
        self.assertAlmostEqual(hard_on_energy(8.98, k.v_rail, k.dv_cs) / e, 1.0, places=6)

    def test_budget_adds_up(self):
        ph = [{"valley": -6.3, "peak": 134.0, "vds_on": 9.0}] * 4
        sc = dict(ron=RON_MAX, l_tech="ideal", esr_cs=1e-3, q_gate=17.1e-9, t_f=0.75e-9)
        b = budget(ph, 17.75e-9, 232e-9, 1.4666667e-9, sc, [12.0] * 4, [12.0, 12.0, 12.0, 0.0])
        parts = sum(v for k, v in b.items() if k not in ("total", "efficiency"))
        self.assertAlmostEqual(parts, b["total"])
        self.assertAlmostEqual(b["efficiency"], 250.0 / (250.0 + b["total"]))


if __name__ == "__main__":
    unittest.main()
