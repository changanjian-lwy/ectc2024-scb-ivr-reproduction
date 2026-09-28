"""A64 unit checks (no LTspice needed): schedule, PULSE strings, z* ordering, RRE, model hash."""
from __future__ import annotations

import hashlib
import re
import unittest

import numpy as np

import a64_netlist as A
import a64_solver as S


def pulse_value(pulse: str, t: float) -> float:
    """Evaluate an LTspice PULSE(V1 V2 Td Tr Tf Ton Tper) at time t (t >= 0)."""
    v1, v2, td, tr, tf, ton, per = (float(x) for x in re.findall(r"[-+0-9.e]+", pulse))
    if t < td:
        return v1
    local = (t - td) % per
    if local < tr:
        return v1 + (v2 - v1) * local / tr
    if local < tr + ton:
        return v2
    if local < tr + ton + tf:
        return v2 + (v1 - v2) * (local - tr - ton) / tf
    return v1


class ScheduleTests(unittest.TestCase):
    def test_windows_match_a58_commanded_pwm_mode(self):
        for design in ("zvs", "baseline"):
            a = A.load_a59(design)
            for dr, df in ((a["dead_time_rise_s"], a["dead_time_fall_s"]), (3.75e-9, 2.95e-9), (4.3e-9, 3.5e-9)):
                self.assertEqual(A.schedule_selfcheck(a, a["ton_cmd_s"], dr, df), 0)

    def test_variable_names(self):
        for design in ("zvs", "baseline"):
            A.check_variable_names(A.load_a59(design))

    def test_pulse_reproduces_windows(self):
        """Command 50 % crossings = window boundaries + EDGE/2, for both origins."""
        a = A.load_a59("zvs")
        ton, dr, df = a["ton_cmd_s"], 3.75e-9, 2.95e-9
        windows = A.gate_windows(ton, dr, df)
        for origin in (0.0, A.QUIET_S):
            for (side, phase), (start, end) in windows.items():
                pulse, _ = A.pulse_for(start - origin, end - origin, A.PERIOD_S)
                for k in range(3):
                    for edge, level_after in ((start, 5.0), (end, 0.0)):
                        t = (edge - origin) % A.PERIOD_S + k * A.PERIOD_S
                        if t < 1e-15:
                            t += A.PERIOD_S
                        before = pulse_value(pulse, t - 1e-12)
                        mid = pulse_value(pulse, t + 0.5 * A.EDGE_S)
                        after = pulse_value(pulse, t + A.EDGE_S + 1e-12)
                        self.assertAlmostEqual(before, 5.0 - level_after, places=6)
                        self.assertAlmostEqual(mid, 2.5, places=6)
                        self.assertAlmostEqual(after, level_after, places=6)

    def test_gate_state_at_zstar_origin(self):
        """At tau = 0 phase-1 high is just starting ON (0 V), phases 2-4 low are ON."""
        a = A.load_a59("zvs")
        windows = A.gate_windows(a["ton_cmd_s"], a["dead_time_rise_s"], a["dead_time_fall_s"])
        states = {key: A.pulse_for(s, e, A.PERIOD_S)[1] for key, (s, e) in windows.items()}
        self.assertFalse(states[("high", 1)])
        self.assertFalse(states[("low", 1)])
        for p in (2, 3, 4):
            self.assertTrue(states[("low", p)])
            self.assertFalse(states[("high", p)])


class RreTests(unittest.TestCase):
    def test_linear_map_fixed_point(self):
        """Six slow modes (the rest die in one period): RRE on 12 samples is exact."""
        rng = np.random.default_rng(1)
        n = len(S.STATE_KEYS)
        q, _ = np.linalg.qr(rng.normal(size=(n, n)))
        eig = np.zeros(n)
        eig[:6] = [0.92, 0.87, 0.6, -0.5, 0.3, 0.1]
        m = q @ np.diag(eig) @ q.T
        fixed = rng.normal(size=n) * 10 + 20
        x = fixed + m @ rng.normal(size=n)
        samples = []
        for _ in range(12):
            samples.append(dict(zip(S.STATE_KEYS, x.tolist())))
            x = fixed + m @ (x - fixed)
        est, _, _ = S.rre(samples)
        err = max(abs(est[k] - f) for k, f in zip(S.STATE_KEYS, fixed))
        last = max(abs(samples[-1][k] - f) for k, f in zip(S.STATE_KEYS, fixed))
        self.assertLess(err, 1e-6 * last + 1e-9)


class ModelTests(unittest.TestCase):
    @unittest.skipUnless(A.MODEL_FILE.exists(), "vendor model not fetched")
    def test_vendor_block_hash(self):
        text = A.MODEL_FILE.read_text(encoding="latin-1")
        block = re.search(r"(?ims)^\.subckt\s+EPC2067\s.*?^\.ends", text).group(0)
        self.assertEqual(len(block), 2734)
        self.assertTrue(hashlib.sha256(block.encode("latin-1")).hexdigest().startswith("b1d201cc7ab403f7"))

    @unittest.skipUnless(A.MODEL_FILE.exists(), "vendor model not fetched")
    def test_x_form_only_touches_the_three_charge_capacitors(self):
        import fetch_epc2067_model as F  # noqa: PLC0415
        text = A.MODEL_FILE.read_text(encoding="latin-1")
        block = re.search(r"(?ims)^\.subckt\s+EPC2067\s.*?^\.ends", text).group(0)
        xblock, changes = F.x_form(block)
        self.assertEqual(len(changes), 3)
        orig = [ln for ln in block.split("\n")]
        new = [ln for ln in xblock.split("\n")]
        # every line outside the three capacitor statements is byte-identical
        touched = ("C_CGS1", "C_CGD1", "C_CSD1", "C_CGS1B", "+", ".subckt")
        self.assertEqual([ln for ln in orig if not ln.startswith(touched)],
                         [ln for ln in new if not ln.startswith(touched)])
        # no own-voltage v(...) left in the rewritten capacitors; the cross term kept once
        for ln in new:
            if ln.startswith("C_CGD1"):
                self.assertNotIn("v(gate,drain)", ln)
            if ln.startswith("C_CSD1"):
                self.assertNotIn("v(source,drain)", ln)
            if ln.startswith("C_CGS1 "):
                self.assertNotIn("v(", ln)
        self.assertEqual(sum(ln.startswith("C_CGS1B") and "v(source,drain)" in ln for ln in new), 1)
        self.assertIn(".subckt EPC2067X gatein drainin sourcein", xblock)


if __name__ == "__main__":
    unittest.main()
