"""A253: the peak-current limit's crossing time (bridge.ocp_cross), its state at the start (ModuleSim.start with cfg
"ocp") and a pending limit turn-off in run_window. The bridge imports cocotb, so these skip without it (CI)."""
import importlib.util
import json
import unittest
from pathlib import Path

HAVE = importlib.util.find_spec("cocotb") is not None
PRESET = Path(__file__).resolve().parents[1] / "src" / "scb_ivr" / "cosim" / "presets" / "p24_5pct_adopted.json"


@unittest.skipUnless(HAVE, "cocotb not installed")
class OcpCross(unittest.TestCase):
    def setUp(self):
        from scb_ivr.cosim.bridge import ocp_cross
        self.f = ocp_cross

    def test_linear_crossing(self):
        self.assertAlmostEqual(self.f(0.0, 120.0, 4e-9, 140.0, 135.0), 3e-9, delta=1e-18)

    def test_already_above(self):
        self.assertEqual(self.f(1e-9, 150.0, 5e-9, 160.0, 135.0), 1e-9)

    def test_not_rising(self):
        self.assertEqual(self.f(1e-9, 136.0, 5e-9, 136.0, 135.0), 1e-9)


@unittest.skipUnless(HAVE, "cocotb not installed")
class OcpStart(unittest.TestCase):
    def module(self, first_high):
        from scb_ivr.cosim import bridge as B
        cfg = json.loads(PRESET.read_text()) | {"ocp": {"i_a": 130.0, "t_ns": 1.0}}
        ref = json.loads((B.PROJECT / cfg["init_run"]).read_text())
        m = B.ModuleSim(cfg, B.make_params(cfg, ref), None, first_high=first_high)
        m.start()
        return m

    def test_master_starts_with_phase1_high(self):
        m = self.module(True)
        self.assertEqual(m.hs_on, [True, False, False, False])
        self.assertEqual(m.ocp_armed, m.hs_on)
        self.assertEqual((m.ocp_thr, m.ocp_t), (130.0, 1e-9))

    def test_slave_starts_low(self):
        self.assertEqual(self.module(False).hs_on, [False] * 4)

    def window(self, on):
        """One limit turn-off pending at 1 ns on phase 1 (high side on or not); the plant's steps recorded."""
        import heapq
        m = self.module(True)
        steps = []
        m.integrate_to = steps.append
        m.hs_on[0] = on
        heapq.heappush(m.pend, (1e-9, 0, 0, 0, {"how": None, "bind": False, "ocp": True}))
        m.run_window(2e-9)
        return m, steps

    def test_stale_turn_off_leaves_the_steps_alone(self):
        m, steps = self.window(False)
        self.assertEqual(steps, [2e-9])
        self.assertEqual(m.ocp_log, [])

    def test_live_turn_off_acts(self):
        m, steps = self.window(True)
        self.assertEqual(steps, [1e-9, 2e-9])
        self.assertEqual((len(m.ocp_log), m.hs_on[0], m.ocp_done[0]), (1, False, True))


if __name__ == "__main__":
    unittest.main()
