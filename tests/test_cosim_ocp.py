"""A253: the peak-current limit's crossing time (bridge.ocp_cross), its state at the start (ModuleSim.start with cfg
"ocp"), a pending limit turn-off in run_window; A256: the count that suspends it. The bridge imports cocotb, so these
skip without it (CI)."""
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


class _Module:
    def module(self, first_high, **ocp):
        from scb_ivr.cosim import bridge as B
        cfg = json.loads(PRESET.read_text()) | {"ocp": {"i_a": 130.0, "t_ns": 1.0} | ocp}
        ref = json.loads((B.PROJECT / cfg["init_run"]).read_text())
        m = B.ModuleSim(cfg, B.make_params(cfg, ref), None, first_high=first_high)
        m.start()
        return m


@unittest.skipUnless(HAVE, "cocotb not installed")
class OcpStart(_Module, unittest.TestCase):
    def test_master_starts_with_phase1_high(self):
        m = self.module(True)
        self.assertEqual(m.hs_on, [True, False, False, False])
        self.assertEqual(m.ocp_armed, m.hs_on)
        self.assertEqual((m.ocp_thr, m.ocp_t), (130.0, 1e-9))

    def test_slave_starts_low(self):
        self.assertEqual(self.module(False).hs_on, [False] * 4)

    def window(self, on, susp=False):
        """One limit turn-off pending at 1 ns on phase 1 (high side on or not); the plant's steps recorded."""
        import heapq
        m = self.module(True)
        m.ocp_susp = susp
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

    def test_suspended_turn_off_is_only_counted(self):
        m, steps = self.window(True, susp=True)
        self.assertEqual(steps, [2e-9])
        self.assertEqual((m.ocp_log, m.hs_on[0], m.ocp_probe[0]), ([], True, 1e-9))


@unittest.skipUnless(HAVE, "cocotb not installed")
class OcpSuspend(_Module, unittest.TestCase):
    """A256: the up/down count of limited pulses suspends the limit at n_susp and re-arms it at 0 on every phase."""

    def test_off_by_default(self):
        m = self.module(True)
        for _ in range(10):
            m.ocp_count(0, True)
        self.assertEqual((m.ocp_cnt, m.ocp_susp), ([0] * 4, False))

    def test_run_suspends_and_clean_pulses_rearm(self):
        m = self.module(True, n_susp=3)
        for hit in (True, False, True, True):
            m.ocp_count(1, hit)
        self.assertEqual((m.ocp_cnt[1], m.ocp_susp), (2, False))
        m.ocp_count(1, True)
        self.assertTrue(m.ocp_susp)
        m.ocp_count(2, True)
        for _ in range(3):
            m.ocp_count(1, False)
        self.assertTrue(m.ocp_susp)                       # phase 3 still counts 1
        m.ocp_count(2, False)
        self.assertEqual((m.ocp_cnt, m.ocp_susp), ([0] * 4, False))
        self.assertEqual([x["on"] for x in m.ocp_susp_log], [1, 0])


if __name__ == "__main__":
    unittest.main()
