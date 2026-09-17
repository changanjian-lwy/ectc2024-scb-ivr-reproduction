import unittest

from scb_ivr.gate_truth_tables import (
    Gate,
    assert_no_commanded_shoot_through,
    p24_minimal_rows,
    p25_extended_rows,
    require_compile_ready,
)


class GateTruthTableTests(unittest.TestCase):
    def test_p24_preserves_unreported_gates(self):
        rows = p24_minimal_rows(active=1)
        self.assertEqual(rows[0].low, (Gate.OFF, Gate.ON, Gate.UNKNOWN, Gate.UNKNOWN))
        with self.assertRaisesRegex(RuntimeError, "NOT_REPORTED"):
            require_compile_ready(rows)

    def test_p25_extension_commands_all_inactive_lows(self):
        row = p25_extended_rows(active=1)[0]
        self.assertEqual(row.high, (Gate.ON, Gate.OFF, Gate.OFF, Gate.OFF))
        self.assertEqual(row.low, (Gate.OFF, Gate.ON, Gate.ON, Gate.ON))

    def test_p25_rotation_wraps_phase4_to_phase1(self):
        rows = p25_extended_rows(active=4)
        self.assertEqual(rows[-1].high, (Gate.ON, Gate.OFF, Gate.OFF, Gate.OFF))
        self.assertEqual(rows[-1].low, (Gate.OFF, Gate.ON, Gate.ON, Gate.ON))

    def test_neither_branch_commands_same_leg_high_and_low(self):
        for active in range(1, 5):
            assert_no_commanded_shoot_through(p24_minimal_rows(active))
            assert_no_commanded_shoot_through(p25_extended_rows(active))

    def test_p25_extension_is_fully_specified(self):
        require_compile_ready(p25_extended_rows(active=2))


if __name__ == "__main__":
    unittest.main()
