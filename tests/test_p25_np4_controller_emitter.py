import unittest

from p25_np4_controller_emitter import emit_p25_np4_machine


class P25NP4ControllerEmitterTests(unittest.TestCase):
    def setUp(self):
        self.text = emit_p25_np4_machine(phases=4)

    def test_has_one_machine_and_twenty_states(self):
        self.assertEqual(self.text.count(".machine 1p"), 1)
        self.assertEqual(self.text.count(".state "), 20)

    def test_rotates_phase4_back_to_phase1(self):
        self.assertIn(".rule P4_M5 P1_M1 V(vin,a1)<=0", self.text)

    def test_uses_events_not_absolute_phase_time(self):
        self.assertNotIn("time>", self.text)
        self.assertNotIn("PHASE", self.text)
        self.assertIn("I(L2)<=-INEG", self.text)
        self.assertIn("V(a1,a2)<=0", self.text)

    def test_each_gate_is_emitted_once(self):
        for k in range(1, 5):
            self.assertEqual(self.text.count(f".output (gh{k})"), 1)
            self.assertEqual(self.text.count(f".output (gl{k})"), 1)

    def test_rejects_unvalidated_phase_count(self):
        with self.assertRaises(ValueError):
            emit_p25_np4_machine(phases=3)


if __name__ == "__main__":
    unittest.main()
