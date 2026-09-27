"""A58 proofs for the two-dead-time schedule (BOUNDARY.md Section 1).

Run from this directory: python3 test_a58_schedule.py -v
"""
import json
import sys
import unittest

import numpy as np

import a58_schedule as S

sys.path.insert(0, str(S.A56_DIR))
import orbit_diagnostics as O  # noqa: E402  (A56, read-only; loads the metering chain)

R, M = S.R, S.M
A56_RUN = json.loads((S.A56_DIR / "runs" / "old_critical_dt_x1.json").read_text())
L_ZVS = A56_RUN["phase_inductance_h"]
TON = A56_RUN["regulated"]["ton_cmd_s"]
Z = np.array(A56_RUN["regulated"]["z_star"], dtype=float)
STEPS = dict(coarse_step_s=62.5e-12, sub_step_s=5e-12)
RISE, FALL = 2.0e-9, 0.7e-9


def newton_map(boundary, z):
    """The F that A53's solve_fixed_point iterates."""
    with R.asymmetric_ron_context():
        return R.S.evaluate_period_map_with_rms(boundary, z, **STEPS)


class Boundary(unittest.TestCase):
    def test_mean_is_enforced_and_nan_rejected(self):
        b = S.build_asym_boundary(phase_inductance_h=L_ZVS, dead_time_rise_s=RISE,
                                  dead_time_fall_s=FALL, ton_cmd_s=TON)
        self.assertEqual(b.dead_time_s, 0.5 * (RISE + FALL))
        self.assertEqual(b.load_resistance_ohm, 0.004)
        self.assertEqual(b.on_time_s, TON)
        with self.assertRaises(ValueError):
            S.AsymDeadTimeBoundary(dead_time_s=1e-9, ton_cmd_s=TON, dead_time_rise_s=1e-9,
                                   dead_time_fall_s=float("nan"))
        with self.assertRaises(ValueError):
            S.AsymDeadTimeBoundary(dead_time_s=1.0e-9, ton_cmd_s=TON, dead_time_rise_s=1.5e-9,
                                   dead_time_fall_s=1.0e-9)

    def test_window_overlap_rejected(self):
        with self.assertRaises(ValueError):  # Ton + mean(d) >= T/4
            S.build_asym_boundary(phase_inductance_h=L_ZVS, dead_time_rise_s=40e-9,
                                  dead_time_fall_s=20e-9, ton_cmd_s=20e-9)


class Namespaces(unittest.TestCase):
    def test_every_holder_is_swapped_and_restored(self):
        before = S.holders()
        self.assertEqual(len(before), 6)
        with S.asym_schedule_context() as swapped:
            self.assertEqual(S.holders(), [])
            for module, name in swapped:
                self.assertIs(getattr(module, name), S.REPLACEMENTS[name])
        self.assertEqual(S.holders(), before)

    def test_modes_match_the_analytic_schedule_in_every_namespace(self):
        b = S.build_asym_boundary(phase_inductance_h=L_ZVS, dead_time_rise_s=RISE,
                                  dead_time_fall_s=FALL, ton_cmd_s=TON)
        period = b.period_s
        rng = np.random.default_rng(58)
        times = 3 * period + rng.uniform(0, period, 4000)
        with S.asym_schedule_context() as swapped:
            functions = {getattr(module, name) for module, name in swapped if name == "commanded_pwm_mode"}
            self.assertEqual(functions, {S.commanded_pwm_mode})
            for module, name in swapped:
                if name != "commanded_pwm_mode":
                    continue
                for t in times[:400]:
                    mode = getattr(module, name)(float(t), b)
                    for p in range(4):
                        local = (t - p * period / 4) % period
                        high = RISE / 2 <= local < TON - FALL / 2
                        low = TON + FALL / 2 <= local < period - RISE / 2
                        self.assertEqual((mode.high_side_on[p], mode.low_side_on[p]), (high, low),
                                         f"{module.__name__} t={t} phase {p}")


class Intervals(unittest.TestCase):
    def test_window_lengths_and_cover(self):
        b = S.build_asym_boundary(phase_inductance_h=L_ZVS, dead_time_rise_s=RISE,
                                  dead_time_fall_s=FALL, ton_cmd_s=TON)
        with S.asym_schedule_context():
            t0 = M.period_start_s(b)
            intervals = M.period_intervals(b, t0)
        self.assertAlmostEqual(t0, M.BASE_PERIOD_INDEX * b.period_s + RISE / 2, delta=1e-21)
        self.assertAlmostEqual(intervals[0].start_s, t0, delta=1e-21)
        self.assertAlmostEqual(intervals[-1].end_s, t0 + b.period_s, delta=1e-21)
        for a, c in zip(intervals, intervals[1:]):
            self.assertAlmostEqual(a.end_s, c.start_s, delta=1e-21)
        kinds = [i.kind for i in intervals if i.kind != "normal"]
        self.assertEqual(sorted(kinds), ["turn_off"] * 4 + ["turn_on"] * 4)
        for i in intervals:
            if i.kind == "turn_on" and i.end_s < t0 + b.period_s - 1e-15:
                self.assertAlmostEqual(i.end_s - i.start_s, RISE, delta=1e-20)
            if i.kind == "turn_off":
                self.assertAlmostEqual(i.end_s - i.start_s, FALL, delta=1e-20)


class PeriodMap(unittest.TestCase):
    def test_symmetric_case_is_bit_identical_to_a56(self):
        a56 = R.build_regulated_boundary(phase_inductance_h=L_ZVS, dead_time_s=2.15e-9, ton_cmd_s=TON)
        a58 = S.build_asym_boundary(phase_inductance_h=L_ZVS, dead_time_rise_s=2.15e-9,
                                    dead_time_fall_s=2.15e-9, ton_cmd_s=TON)
        reference = newton_map(a56, Z)
        with S.asym_schedule_context():
            inside_a56 = newton_map(a56, Z)
            result = newton_map(a58, Z)
        self.assertTrue(np.array_equal(reference.z_next, inside_a56.z_next))
        self.assertTrue(np.array_equal(reference.z_next, result.z_next))
        for x, y in zip(reference.turn_on + reference.turn_off, result.turn_on + result.turn_off):
            self.assertEqual(x.switch_on_time_s, y.switch_on_time_s)

    def test_asymmetric_verdict_windows_and_no_scalar_dead_time_reads(self):
        b = S.build_asym_boundary(phase_inductance_h=L_ZVS, dead_time_rise_s=RISE,
                                  dead_time_fall_s=FALL, ton_cmd_s=TON)
        sentinel = S.build_asym_boundary(phase_inductance_h=L_ZVS, dead_time_rise_s=RISE,
                                         dead_time_fall_s=FALL, ton_cmd_s=TON)
        object.__setattr__(sentinel, "dead_time_s", 3.3e-9)  # bypass validation on purpose
        with S.asym_schedule_context():
            result = newton_map(b, Z)
            moved = newton_map(sentinel, Z)
            metered, steps, _ = O.accepted_orbit(b, Z, **STEPS)
        self.assertTrue(np.array_equal(result.z_next, moved.z_next))
        self.assertTrue(np.array_equal(result.z_next, metered.z_next))
        for v in result.turn_on + metered.turn_on:
            self.assertAlmostEqual(v.window_end_s - v.window_start_s, RISE, delta=1e-20)
        for v in result.turn_off + metered.turn_off:
            self.assertAlmostEqual(v.window_end_s - v.window_start_s, FALL, delta=1e-20)
        # accepted samples: a phase is in DEADTIME only inside its own windows
        windows = [(v.window_start_s, v.window_end_s, v.phase_index) for v in metered.turn_on + metered.turn_off]
        period = b.period_s
        for step in steps[1:]:
            for p in range(4):
                if not (step.mode.high_side_on[p] or step.mode.low_side_on[p]):
                    inside = any(s - 1e-18 < t <= e + 1e-18 for s, e, q in windows if q == p
                                 for t in (step.time_s, step.time_s + period, step.time_s - period))
                    self.assertTrue(inside, f"phase {p} dead at {step.time_s} outside its windows")


if __name__ == "__main__":
    unittest.main()
