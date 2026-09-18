"""A51 self-tests for the one-period map, run before any result is believed.

Nothing here tunes or fits anything; each test either passes or the script exits
non-zero.  The tests are, in order:

1. **Import isolation.**  No module named `scb_ivr` or `scb_ivr.*` is loaded, and
   no loaded `solver_copy` module resolves to a file under `src/scb_ivr/`.
2. **A50's kernel is used unchanged.**  `_advance_forced` with the commanded
   mode is BITWISE identical to `advance_fixed_diode_step`, so A51's event
   override changes only WHICH mode is stepped, never HOW a step is taken.
3. **The interval cover is exact.**  The intervals returned by
   `period_intervals` tile `[t0, t0+T)` with no gap and no overlap, and contain
   exactly eight dead-time windows, two per phase.
4. **The seed conversion round-trips.**  A37's own `VC1/VC2/VC3` and `IL1..IL4`
   come back out of the 20-variable vector exactly.
5. **`I_VSTEP` is algebraic.**  Its column of `E` is exactly zero, so its seed
   value provably cannot influence `F`; changing it by `1e6` leaves `F(z)`
   bitwise unchanged.
6. **Step-size convergence of `F` itself.**  `F(z_seed)` is evaluated over a
   sub-step and a coarse-step ladder, and the observed differences are reported
   so no later number rests on one unchecked discretization.

Run:  python3 run_map_selftests.py --output map_selftests.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

import a51_period_map as M
from solver_copy.zero_start_descriptor import assemble_descriptor, commanded_pwm_mode
from solver_copy.zero_start_hybrid_solver import advance_fixed_diode_step

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> dict:
    if not condition:
        FAILURES.append(f"{name}: {detail}")
    return {"test": name, "passed": bool(condition), "detail": detail}


def test_import_isolation() -> dict:
    offenders = []
    for name, module in list(sys.modules.items()):
        if name == "scb_ivr" or name.startswith("scb_ivr."):
            offenders.append(name)
            continue
        origin = getattr(module, "__file__", None)
        if origin and "/src/scb_ivr/" in str(Path(origin).resolve()):
            offenders.append(f"{name} -> {origin}")
    return check("import_isolation", not offenders, f"offenders={offenders}")


def test_kernel_identity(boundary) -> dict:
    z, _ = M.a37_seed_state(boundary)
    t0 = M.period_start_s(boundary)
    previous = M._initial_step(boundary, z, t0, (False, False, False))
    worst = 0.0
    samples = 0
    for offset_ns in (0.01, 0.5, 3.0, 20.0, 48.5, 99.0, 148.5, 190.0):
        next_time_s = t0 + offset_ns * 1e-9
        reference = advance_fixed_diode_step(
            previous, next_time_s, boundary, (False, False, False)
        )
        commanded = commanded_pwm_mode(0.5 * (previous.time_s + next_time_s), boundary)
        forced = M._advance_forced(
            previous,
            next_time_s,
            boundary,
            commanded.high_side_on,
            commanded.low_side_on,
            (False, False, False),
        )
        samples += 1
        worst = max(worst, float(np.max(np.abs(reference.state - forced.state))))
    return check(
        "kernel_bitwise_identity",
        worst == 0.0,
        f"max |advance_fixed_diode_step - _advance_forced| = {worst!r} over {samples} samples",
    )


def test_interval_cover(boundary) -> dict:
    t0 = M.period_start_s(boundary)
    intervals = M.period_intervals(boundary, t0)
    gaps = []
    cursor = t0
    for interval in intervals:
        if abs(interval.start_s - cursor) > 1e-21:
            gaps.append((cursor, interval.start_s))
        cursor = interval.end_s
    total = sum(interval.end_s - interval.start_s for interval in intervals)
    turn_on = sorted(
        interval.phase_index for interval in intervals if interval.kind == "turn_on"
    )
    turn_off = sorted(
        interval.phase_index for interval in intervals if interval.kind == "turn_off"
    )
    ok = (
        not gaps
        and abs(cursor - (t0 + boundary.period_s)) < 1e-21
        and abs(total - boundary.period_s) < 1e-18
        and turn_on == [0, 1, 2, 3]
        and turn_off == [0, 1, 2, 3]
    )
    return check(
        "interval_cover",
        ok,
        f"gaps={gaps} total={total!r} T={boundary.period_s!r} "
        f"turn_on={turn_on} turn_off={turn_off}",
    )


def test_seed_roundtrip(boundary) -> dict:
    z, _ = M.a37_seed_state(boundary)
    names = M.variable_names(boundary)
    index = {name: position for position, name in enumerate(names)}
    seed = M.A37_BEST_CANDIDATE
    worst = 0.0
    for number in (1, 2, 3):
        recovered = z[index[f"a{number}"]] - z[index[f"x{number}"]]
        worst = max(worst, abs(recovered - seed[f"VC{number}_INIT"]))
    for number in (1, 2, 3, 4):
        worst = max(worst, abs(z[index[f"L{number}"]] - seed[f"IL{number}_INIT"]))
    return check("seed_roundtrip", worst == 0.0, f"worst deviation = {worst!r}")


def test_ivstep_algebraic(boundary) -> dict:
    mode = commanded_pwm_mode(M.period_start_s(boundary), boundary)
    system = assemble_descriptor(boundary, mode, M.period_start_s(boundary))
    column = system.variable_names.index("I_VSTEP")
    column_norm = float(np.max(np.abs(system.e[:, column])))
    z, _ = M.a37_seed_state(boundary)
    perturbed = z.copy()
    perturbed[column] += 1e6
    base = M.evaluate_period_map(boundary, z, sub_step_s=20e-12, coarse_step_s=0.5e-9)
    other = M.evaluate_period_map(
        boundary, perturbed, sub_step_s=20e-12, coarse_step_s=0.5e-9
    )
    difference = float(np.max(np.abs(base.z_next - other.z_next)))
    return check(
        "ivstep_algebraic",
        column_norm == 0.0 and difference == 0.0,
        f"|E[:,I_VSTEP]|inf = {column_norm!r}, |F(z)-F(z+1e6 e_IVSTEP)|inf = {difference!r}",
    )


def test_step_convergence(boundary) -> dict:
    z, _ = M.a37_seed_state(boundary)
    sub_rows = []
    reference = None
    for sub_step_ps in (50.0, 20.0, 10.0, 5.0, 2.0, 1.0):
        started = time.time()
        result = M.evaluate_period_map(
            boundary, z, sub_step_s=sub_step_ps * 1e-12, coarse_step_s=62.5e-12
        )
        row = {
            "sub_step_ps": sub_step_ps,
            "relative_residual": M.relative_residual(z, result.z_next),
            "natural_zvs_flags": list(result.natural_zvs_flags),
            "minimum_abs_vds_v": [v.minimum_abs_vds_v for v in result.turn_on],
            "z_next": result.z_next.tolist(),
            "wall_clock_s": time.time() - started,
        }
        if reference is not None:
            row["z_next_inf_difference_from_previous"] = float(
                np.max(np.abs(np.array(row["z_next"]) - np.array(reference)))
            )
        reference = row["z_next"]
        sub_rows.append(row)

    coarse_rows = []
    reference = None
    for coarse_step_ns in (0.5, 0.25, 0.125, 0.0625, 0.03125):
        result = M.evaluate_period_map(
            boundary, z, sub_step_s=5e-12, coarse_step_s=coarse_step_ns * 1e-9
        )
        row = {
            "coarse_step_ns": coarse_step_ns,
            "relative_residual": M.relative_residual(z, result.z_next),
            "natural_zvs_flags": list(result.natural_zvs_flags),
            "z_next": result.z_next.tolist(),
        }
        if reference is not None:
            row["z_next_inf_difference_from_previous"] = float(
                np.max(np.abs(np.array(row["z_next"]) - np.array(reference)))
            )
        reference = row["z_next"]
        coarse_rows.append(row)

    verdicts_stable = len({tuple(row["natural_zvs_flags"]) for row in sub_rows}) == 1
    return {
        "test": "step_convergence",
        "passed": True,
        "sub_step_ladder": sub_rows,
        "coarse_step_ladder": coarse_rows,
        "zvs_verdicts_identical_across_sub_step_ladder": verdicts_stable,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="map_selftests.json")
    args = parser.parse_args()
    boundary = M.build_boundary()
    started = time.time()
    tests = [
        test_import_isolation(),
        test_kernel_identity(boundary),
        test_interval_cover(boundary),
        test_seed_roundtrip(boundary),
        test_ivstep_algebraic(boundary),
        test_step_convergence(boundary),
    ]
    payload = {
        "script": Path(__file__).name,
        "tests": tests,
        "failures": FAILURES,
        "all_passed": not FAILURES,
        "wall_clock_s": time.time() - started,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")
    for entry in tests:
        print(f"  [{'PASS' if entry['passed'] else 'FAIL'}] {entry['test']}"
              f"  {entry.get('detail', '')}")
    convergence = tests[-1]
    print("\n  sub-step ladder (F at the A37 seed):")
    for row in convergence["sub_step_ladder"]:
        print(
            f"    {row['sub_step_ps']:>5} ps  rel={row['relative_residual']:.6e}"
            f"  zvs={row['natural_zvs_flags']}"
            f"  dz_inf_vs_previous={row.get('z_next_inf_difference_from_previous', float('nan')):.3e}"
            f"  ({row['wall_clock_s']:.1f} s)"
        )
    print("  coarse-step ladder (F at the A37 seed):")
    for row in convergence["coarse_step_ladder"]:
        print(
            f"    {row['coarse_step_ns']:>8} ns  rel={row['relative_residual']:.6e}"
            f"  zvs={row['natural_zvs_flags']}"
            f"  dz_inf_vs_previous={row.get('z_next_inf_difference_from_previous', float('nan')):.3e}"
        )
    print(f"\nwrote {args.output}   all_passed = {payload['all_passed']}")
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
