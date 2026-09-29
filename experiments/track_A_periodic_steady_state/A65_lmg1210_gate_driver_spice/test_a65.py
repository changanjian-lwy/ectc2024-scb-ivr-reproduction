"""A65 unit checks (no LTspice needed): A64's checks on the copied code, plus the LMG1210 driver."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

import numpy as np

import a65_netlist as A
import a65_solver as S


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



def _load_a64_netlist():
    path = Path(__file__).resolve().parent.parent / "A64_vendor_model_spice_crosscheck" / "a64_netlist.py"
    spec = importlib.util.spec_from_file_location("a64_netlist_ref", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["a64_netlist_ref"] = mod
    spec.loader.exec_module(mod)
    return mod


def _spec(module, case, design="zvs"):
    a = module.load_a59(design)
    return module.NetlistSpec(design=design, case=case, ton_s=a["ton_cmd_s"], dr_s=3.75e-9, df_s=2.3e-9,
                              n_periods=2, max_step_s=5e-11, ic=a["z_star"], origin_s=0.0), a


class DriverTests(unittest.TestCase):
    def test_resistor_case_matches_a64_netlist(self):
        ref = _load_a64_netlist()
        spec64, a64 = _spec(ref, ref.Case(1.0, 60.0))
        spec65, a65 = _spec(A, A.Case(1.0, 60.0))
        old = ref.build(spec64, a64)[0].splitlines()
        new = A.build(spec65, a65)[0].splitlines()
        self.assertEqual(len(old), len(new))
        self.assertEqual(old[2:], new[2:])

    def test_driver_tables(self):
        src, snk = A.driver_tables()
        src = [float(x) for x in src.split(",")]
        snk = [float(x) for x in snk.split(",")]
        sv, si = src[0::2], src[1::2]
        kv, ki = snk[0::2], snk[1::2]
        self.assertEqual((sv[0], sv[-1]), (0.0, 5.5))
        self.assertEqual((kv[0], kv[-1]), (-0.5, 5.0))
        self.assertAlmostEqual(si[0], 1.68, delta=0.02)      # Fig. 1 at 0 V
        self.assertLess(si[-1], 0.0)                          # pull-up clamps towards 5 V
        self.assertAlmostEqual(ki[-1], 3.64, delta=0.02)     # Fig. 2 at 5 V
        self.assertLess(ki[0], 0.0)                           # pull-down clamps towards 0 V
        self.assertTrue(all(b > a for a, b in zip(sv, sv[1:])))
        self.assertTrue(all(b > a for a, b in zip(kv, kv[1:])))

    def test_fanout(self):
        for driver, (nh, nl) in (("LMG1210_SW", (2, 3)), ("LMG1210_DEV", (1, 1))):
            spec, a = _spec(A, A.Case(1.0, 60.0, driver))
            lines = A.build(spec, a)[0].splitlines()
            ups = [ln for ln in lines if ln.startswith("B_U")]
            downs = [ln for ln in lines if ln.startswith("B_D")]
            self.assertEqual((len(ups), len(downs)), (20, 20))
            for ln in ups + downs:
                side = ln[3]
                self.assertTrue(ln.endswith(f"/{nh if side == 'H' else nl}"), ln[:12])
            self.assertFalse(any(ln.startswith("R_G") for ln in lines))

    def test_digitization_residuals(self):
        meta = json.loads((Path(__file__).resolve().parent / "lmg1210_output_iv_digitization.json").read_text())
        for fig in meta["figures"].values():
            self.assertLess(fig["x_resid_max"], 1e-3)
            self.assertLess(fig["y_resid_max"], 1e-3)


if __name__ == "__main__":
    unittest.main()
