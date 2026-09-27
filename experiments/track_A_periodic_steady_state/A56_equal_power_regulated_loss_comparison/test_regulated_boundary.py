"""A56 regulation-variable proof (BOUNDARY.md S1 implementation note).

Run from anywhere:
    python3 experiments/track_A_periodic_steady_state/A56_equal_power_regulated_loss_comparison/test_regulated_boundary.py -v

Proves that ``RegulatedBoundary.ton_cmd_s`` is what every scheduler code path
used by the A56 solve and metering reads, that nothing on those paths derives
on-time from ``duty``, and that the load stays exactly 0.004 Ohm.
"""
from __future__ import annotations

import json
import sys
import unittest
from dataclasses import asdict, dataclass, fields
from math import floor
from pathlib import Path
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import regulated_boundary as R  # noqa: E402

A55_GRID = R.A55_DIR / "joint_local_grid.json"
NS = 1e-9


def _a55_probe(label: str) -> dict:
    grid = json.loads(A55_GRID.read_text())
    return next(p for p in grid["probes"] if p["label"] == label)


@dataclass(frozen=True)
class PoisonedDuty(R.RegulatedBoundary):
    """Tripwire: any code path that derives on-time from duty will raise."""

    @property
    def duty(self) -> float:  # type: ignore[override]
        raise AssertionError("a solve/metering path read boundary.duty")


def _poisoned(**kwargs) -> PoisonedDuty:
    base = R.build_regulated_boundary(**kwargs)
    values = {f.name: getattr(base, f.name) for f in fields(base)}
    return PoisonedDuty(**values)


class RegulatedBoundaryFieldTests(unittest.TestCase):
    def test_only_on_time_changes_and_load_is_exactly_4_mohm(self):
        for _, inductance in R.L_ROWS:
            for _, dead_time in R.DT_COLUMNS:
                reference = R.A.build_epc2067_boundary(
                    phase_inductance_h=inductance, dead_time_s=dead_time)
                for ton in (12.0 * NS, R.NOMINAL_TON_S, 19.5 * NS, 24.0 * NS):
                    b = R.build_regulated_boundary(
                        phase_inductance_h=inductance, dead_time_s=dead_time, ton_cmd_s=ton)
                    self.assertEqual(b.on_time_s, ton)
                    self.assertEqual(b.load_resistance_ohm, 0.004)
                    self.assertEqual(b.vout_target_v, 1.0)
                    self.assertEqual(b.module_power_w, 250.0)
                    self.assertEqual(b.duty, reference.duty)  # untouched, unused
                    record = asdict(b)
                    self.assertEqual(record.pop("ton_cmd_s"), ton)
                    self.assertEqual(record, asdict(reference))

    def test_ton_cmd_must_be_explicit(self):
        with self.assertRaises(ValueError):
            R.RegulatedBoundary(dead_time_s=2.15e-9)
        with self.assertRaises(ValueError):
            R.build_regulated_boundary(phase_inductance_h=1e-9, dead_time_s=2.15e-9,
                                       ton_cmd_s=49.0 * NS)

    def test_descriptor_load_conductance_is_1_over_4_mohm(self):
        b = R.build_regulated_boundary(phase_inductance_h=0.6215e-9, dead_time_s=4.3e-9,
                                       ton_cmd_s=21.0 * NS)
        with R.asymmetric_ron_context():
            mode = R.D.commanded_pwm_mode(0.0, b)
            system = R.M.assemble_descriptor(b, mode, 0.0)
        out = system.node_names.index("out")
        # Only the load resistor is a conductance at node `out`.
        self.assertEqual(system.a[out, out], 1.0 / 0.004)


class SchedulerPathTests(unittest.TestCase):
    ton = 19.5 * NS
    dead = 2.15e-9

    def setUp(self):
        self.b = R.build_regulated_boundary(phase_inductance_h=1.4666667e-9,
                                            dead_time_s=self.dead, ton_cmd_s=self.ton)

    def test_commanded_pwm_mode_uses_ton_cmd(self):
        b, half, eps = self.b, 0.5 * self.dead, 1e-13
        period = b.period_s
        for phase in range(4):
            t_phase = 7 * period + phase * period / 4
            def mode(local):
                return R.D.commanded_pwm_mode(t_phase + local, b)
            # Past the NOMINAL command-off edge the high side must still be on.
            self.assertTrue(mode(R.NOMINAL_TON_S - half + eps).high_side_on[phase])
            self.assertTrue(mode(self.ton - half - eps).high_side_on[phase])
            dead_mode = mode(self.ton)
            self.assertFalse(dead_mode.high_side_on[phase])
            self.assertFalse(dead_mode.low_side_on[phase])
            self.assertTrue(mode(self.ton + half + eps).low_side_on[phase])
            self.assertFalse(mode(self.ton - half + eps).high_side_on[phase])

    def test_next_pwm_edge_uses_ton_cmd(self):
        b, half = self.b, 0.5 * self.dead
        start = 7 * b.period_s
        edge = R.H.next_pwm_edge_s(start + half + 1e-12, b)
        self.assertAlmostEqual(edge, start + self.ton - half, delta=1e-21)
        edge = R.H.next_pwm_edge_s(start + self.ton - half + 1e-12, b)
        self.assertAlmostEqual(edge, start + self.ton + half, delta=1e-21)

    def test_period_intervals_center_turn_off_windows_on_ton_cmd(self):
        b, half = self.b, 0.5 * self.dead
        t0 = R.M.period_start_s(b)
        intervals = R.M.period_intervals(b, t0)
        offs = sorted((i for i in intervals if i.kind == "turn_off"),
                      key=lambda i: i.phase_index)
        self.assertEqual(len(offs), 4)
        for window in offs:
            center = R.M.BASE_PERIOD_INDEX * b.period_s + window.phase_index * b.period_s / 4 + self.ton
            self.assertAlmostEqual(window.start_s, center - half, delta=1e-20)
            self.assertAlmostEqual(window.end_s, center + half, delta=1e-20)
            mid = R.M._window_mode(b, window.start_s, window.end_s, (False,) * 3)
            self.assertFalse(mid.high_side_on[window.phase_index])
            self.assertFalse(mid.low_side_on[window.phase_index])


class SolveAndMeteringPathTests(unittest.TestCase):
    def test_solver_and_meter_share_one_period_map_module(self):
        self.assertIs(R.S.M, R.M)
        self.assertIs(R.A.M, R.M)
        self.assertIs(R.A.P.M, R.M)

    def test_solve_fixed_point_passes_the_regulated_boundary_through(self):
        b = R.build_regulated_boundary(phase_inductance_h=1.4666667e-9, dead_time_s=2.15e-9,
                                       ton_cmd_s=18.0 * NS)
        with patch.object(R.S.M, "evaluate_period_map", side_effect=RuntimeError("sentinel")) as run:
            with self.assertRaisesRegex(RuntimeError, "sentinel"):
                R.S.solve_fixed_point(b, np.zeros(20))
        self.assertIs(run.call_args.args[0], b)

    def test_unscoped_a55_metering_would_drop_ton_cmd_scoped_metering_keeps_it(self):
        b = R.build_regulated_boundary(phase_inductance_h=0.6215240418389056e-9,
                                       dead_time_s=4.3e-9, ton_cmd_s=20.0 * NS)
        point = dict(phase_inductance_h=b.phase_inductance_h, dead_time_s=b.dead_time_s,
                     z_star=[0.0] * 20)
        original_builder = R.A.build_epc2067_boundary
        with patch.object(R.A.P, "evaluate_period_map_with_paths",
                          side_effect=RuntimeError("sentinel")) as run:
            with self.assertRaisesRegex(RuntimeError, "sentinel"):
                R.A.metered_orbit(point)
            unscoped = run.call_args.args[0]
            # This is the defect that forces the documented local override.
            self.assertNotIsInstance(unscoped, R.RegulatedBoundary)
            self.assertNotEqual(unscoped.on_time_s, b.on_time_s)
            with self.assertRaisesRegex(RuntimeError, "sentinel"):
                with R.regulated_metering(b):
                    R.A.metered_orbit(point)
            self.assertIs(run.call_args.args[0], b)
        self.assertIs(R.A.build_epc2067_boundary, original_builder)
        with self.assertRaisesRegex(RuntimeError, "dead time differs"):
            with R.regulated_metering(b):
                R.A.metered_orbit(dict(point, dead_time_s=2.15e-9))
        self.assertIs(R.A.build_epc2067_boundary, original_builder)

    def test_full_period_and_a55_metering_never_read_duty_and_follow_ton_cmd(self):
        probe = _a55_probe("nominal_dt_x1")
        ton, dead = 19.0 * NS, 2.15e-9
        b = _poisoned(phase_inductance_h=probe["phase_inductance_h"], dead_time_s=dead,
                      ton_cmd_s=ton)
        z = np.array(probe["z_star"])
        with R.asymmetric_ron_context():
            period = R.M.evaluate_period_map(b, z, coarse_step_s=62.5e-12, sub_step_s=5e-12)
        metrics = R.meter_regulated(b, z, coarse_step_s=62.5e-12, sub_step_s=5e-12)
        self.assertEqual(metrics["full_boundary"]["ton_cmd_s"], ton)
        np.testing.assert_array_equal(
            metrics["natural_zvs_flags"], list(period.natural_zvs_flags))
        t0 = R.M.period_start_s(b)
        windows = {(i.kind, i.phase_index): i for i in R.M.period_intervals(b, t0)}
        for verdict in metrics["high_side_turn_on_verdicts"]:
            window = windows[("turn_on", verdict["phase_index"])]
            self.assertEqual(verdict["window_start_s"], window.start_s)
            self.assertTrue(verdict["commanded_dead_time_confirmed"])
        for verdict in metrics["low_side_turn_on_verdicts"]:
            window = windows[("turn_off", verdict["phase_index"])]
            self.assertAlmostEqual(verdict["window_start_s"], window.start_s, delta=1e-20)
            self.assertAlmostEqual(verdict["window_end_s"], window.end_s, delta=1e-20)
        # Nominal L at 2.15 ns hard-switches every high side, so the modeled
        # high-channel active time is exactly Ton_cmd - d (not 16.6667 ns - d).
        self.assertFalse(any(metrics["natural_zvs_flags"]))
        for duration in metrics["modeled_high_channel_active_duration_s"]:
            self.assertAlmostEqual(duration, ton - dead, delta=1e-15)

    def test_nominal_ton_cmd_reproduces_a55_boundary_bitwise(self):
        probe = _a55_probe("new_passing_dt_x2")
        reference = R.A.build_epc2067_boundary(phase_inductance_h=probe["phase_inductance_h"],
                                               dead_time_s=probe["dead_time_s"])
        b = R.build_regulated_boundary(phase_inductance_h=probe["phase_inductance_h"],
                                       dead_time_s=probe["dead_time_s"],
                                       ton_cmd_s=reference.on_time_s)
        z = np.array(probe["z_star"])
        with R.asymmetric_ron_context():
            old = R.M.evaluate_period_map(reference, z, coarse_step_s=62.5e-12, sub_step_s=5e-12)
            new = R.M.evaluate_period_map(b, z, coarse_step_s=62.5e-12, sub_step_s=5e-12)
        np.testing.assert_array_equal(old.z_next, new.z_next)


if __name__ == "__main__":
    unittest.main()
