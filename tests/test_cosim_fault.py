"""A259: the fault trip (bridge cfg "fault"): the peak up/down count, the under-voltage and average-current
detectors, and the latched shutdown that blocks the driver from t_drv on. The bridge imports cocotb, so these skip
without it (CI)."""
import heapq
import importlib.util
import json
import unittest
from pathlib import Path

HAVE = importlib.util.find_spec("cocotb") is not None
PRESET = Path(__file__).resolve().parents[1] / "src" / "scb_ivr" / "cosim" / "presets" / "p24_5pct_adopted.json"
FAULT = {"i_a": 220.0, "n": 3, "uv_v": 0.9, "uv_ns": 100.0, "uv_mask_us": 10.0, "iavg_a": 340.0, "avg_us": 10.0}


def module(fault, ocp=True):
    from scb_ivr.cosim import bridge as B
    cfg = json.loads(PRESET.read_text()) | {"fault": fault}
    if ocp:
        cfg["ocp"] = {"i_a": 130.0, "t_ns": 1.0}
    ref = json.loads((B.PROJECT / cfg["init_run"]).read_text())
    m = B.ModuleSim(cfg, B.make_params(cfg, ref), None, first_high=True)
    m.start()
    return m


@unittest.skipUnless(HAVE, "cocotb not installed")
class FaultTrip(unittest.TestCase):
    def test_keys_checked(self):
        for fault, ocp in (({"i_a": 220.0, "n": 3, "x": 1}, True), ({"i_a": 220.0, "n": 3}, False)):
            with self.assertRaises(ValueError):
                module(fault, ocp)
        self.assertIsNone(module({"uv_v": 0.9, "uv_ns": 100.0, "uv_mask_us": 10.0}, ocp=False).flt["t"])

    def test_peak_count_is_up_down(self):
        m = module(FAULT)
        for hit in (True, True, False, True):
            m.flt["hit"][2] = hit
            m.fault_count(2)
        self.assertEqual((m.flt["cnt"][2], m.flt["t"]), (2, None))
        m.flt["hit"][2] = True
        m.fault_count(2)
        self.assertEqual((m.flt["rec"]["cause"], m.flt["rec"]["phase"]), ("peak", 3))
        self.assertEqual(m.pend[0][2], -2)
        self.assertAlmostEqual(m.flt["block"] - m.flt["t"], m.t_drv, delta=1e-18)

    def test_fault_level_cuts_while_suspended(self):
        m = module(FAULT)
        m.ocp_susp = True
        m.hs_on[0] = True
        m.ocp_prev = (0.0, [200.0] * 4)
        self.at(m, 4e-9, i=240.0)                              # crossed 220 A half way through the window
        ta, _, j, lvl, meta = m.pend[0]
        self.assertEqual((j, lvl, meta.get("flt")), (0, 0, True))
        self.assertAlmostEqual(ta, 2e-9 + m.ocp_t + m.t_drv, delta=1e-15)
        self.assertTrue(m.flt["hit"][0])
        steps = []
        m.integrate_to = steps.append
        m.run_window(ta + 1e-9)                                # not dropped although the limit is suspended
        self.assertEqual((m.hs_on[0], m.plant.gh[0], m.flt["cnt"][0]), (False, False, 1))

    def at(self, m, t, vo=None, i=None):
        p = m.plant
        p.t = t
        if vo is not None:
            p.y[m.i_out] = vo
        if i is not None:
            for k in range(4):
                p.y[m.nv + k] = i
        m.fault_check()

    def test_uv_waits_for_mode_p_mask_and_delay(self):
        m = module({"uv_v": 0.9, "uv_ns": 100.0, "uv_mask_us": 10.0})
        self.at(m, 1e-6, vo=0.5)
        self.assertIsNone(m.flt["uv_t0"])                      # before mode P
        m.st["t_mode_p"] = 0.0
        self.at(m, 5e-6, vo=0.5)
        self.assertIsNone(m.flt["uv_t0"])                      # inside the mask
        self.at(m, 20e-6, vo=0.5); self.at(m, 20.05e-6, vo=0.95); self.at(m, 20.1e-6, vo=0.5)
        self.assertIsNone(m.flt["t"])                          # the dip was interrupted
        self.at(m, 20.15e-6, vo=0.5); self.at(m, 20.25e-6, vo=0.5)
        self.assertEqual(m.flt["rec"]["cause"], "uv")

    def test_average_current(self):
        m = module({"iavg_a": 340.0, "avg_us": 10.0}, ocp=False)
        for q in range(41):                                    # 80 A per phase (320 A) for 10 us
            self.at(m, q * 0.25e-6, i=80.0)
        self.assertIsNone(m.flt["t"])
        for q in range(41, 81):                                # 90 A per phase (360 A): the mean passes 340 A
            self.at(m, q * 0.25e-6, i=90.0)
        self.assertEqual(m.flt["rec"]["cause"], "avg")
        self.assertGreater(m.flt["rec"]["value"], 340.0)

    def test_shutdown_blocks_the_driver(self):
        m = module(FAULT)
        steps = []
        m.integrate_to = steps.append
        m.fault_trip("uv", None, 0.5)
        t_block = m.flt["block"]
        heapq.heappush(m.pend, (t_block + 1e-9, m.seq[0], 1, 1, {"how": 0, "bind": False})); m.seq[0] += 1
        m.run_window(t_block + 4e-9)
        self.assertEqual(steps, [t_block, t_block + 4e-9])     # the blocked turn-on is never stepped to
        self.assertEqual((m.plant.gh, m.plant.gl), ([False] * 4, [False] * 4))
        self.assertEqual(m.flt["rec"]["t_off_s"], m.plant.t)


if __name__ == "__main__":
    unittest.main()
