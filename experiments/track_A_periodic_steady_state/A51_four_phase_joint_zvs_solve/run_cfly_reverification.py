"""A51 step 2 - independent re-verification of `BOUNDARY.md` Section 1's CFLY check.

`BOUNDARY.md` Section 1 reports that replacing A42's own inherited cross-topology
`CFLY = 53.8 uF` placeholder with the corrected `CFLY = 3 uF` leaves A50's own
single-phase gate-2 result qualitatively unchanged.  A51 builds directly on that
conclusion, so it is re-derived here rather than trusted.

Method: A50's own already-committed `a42_local_validation.py` is imported and run
UNMODIFIED.  The only thing this script does is rebind the module-level constant
`a42_local_validation.CFLY_A42_F` at runtime before calling `build_case`, which
`build_boundary` reads at call time.  No file under
`A50_zvs_capable_solver_prototype/` is edited, and `src/scb_ivr/` is neither read
nor imported.

Because A50 Section 3.3 established that a single sub-step cannot answer a
millivolt-margin ZVS question under backward Euler, both CFLY values are run over
the same sub-step ladder A50 used, and a first-order Richardson extrapolation is
reported alongside the `0.0625 ps` row (the row `BOUNDARY.md`'s own table quotes).

Run:  python3 run_cfly_reverification.py --output cfly_reverification.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
A50_DIR = HERE.parent / "A50_zvs_capable_solver_prototype"
if str(A50_DIR) not in sys.path:
    sys.path.insert(0, str(A50_DIR))

import a42_local_validation as a42  # noqa: E402

#: `BOUNDARY.md` Section 1's own published table, the comparison target.
BOUNDARY_SECTION_1 = {
    "53.8uF": {
        "min_abs_vds_7p76_v": 7.867e-3,
        "crossed_7p77": True,
        "crossing_time_7p77_s": 23.14711541e-6,
    },
    "3uF": {
        "min_abs_vds_7p76_v": 9.094e-3,
        "crossed_7p77": True,
        "crossing_time_7p77_s": 23.14711995e-6,
    },
}

SUB_STEPS_S = (1e-12, 0.5e-12, 0.25e-12, 0.125e-12, 0.0625e-12)


def _assert_no_src_import() -> None:
    for name, module in list(sys.modules.items()):
        if name == "scb_ivr" or name.startswith("scb_ivr."):
            raise RuntimeError(f"forbidden import of {name}")
        origin = getattr(module, "__file__", None)
        if origin and "/src/scb_ivr/" in str(Path(origin).resolve()):
            raise RuntimeError(f"module {name} resolves into src/scb_ivr/")


def run_one(cfly_f: float, negative_fraction: float, sub_step_s: float) -> dict:
    a42.CFLY_A42_F = cfly_f
    case = a42.build_case(negative_fraction=negative_fraction)
    boundary = case["boundary"]
    if boundary.flying_capacitances_f != (cfly_f, cfly_f, cfly_f):
        raise RuntimeError("CFLY override did not reach the assembled boundary")
    resolved = a42.resolve_case(case, sub_step_s=sub_step_s)
    window = resolved["window"]
    return {
        "cfly_f": cfly_f,
        "negative_fraction": negative_fraction,
        "negative_current_a": case["negative_current_a"],
        "sub_step_s": sub_step_s,
        "window_start_s": window.start_time_s,
        "window_end_s": window.commanded_end_time_s,
        "step_count": window.step_count,
        "initial_switch_voltage_v": window.initial_switch_voltage_v,
        "minimum_abs_switch_voltage_v": window.minimum_abs_switch_voltage_v,
        "minimum_signed_switch_voltage_v": window.minimum_signed_switch_voltage_v,
        "crossed_tolerance": window.crossed_tolerance,
        "crossed_tolerance_time_s": window.crossed_tolerance_time_s,
        "sign_change_time_s": window.sign_change_time_s,
        "switch_current_at_crossing_a": window.switch_current_at_crossing_a,
        "maximum_descriptor_relative_backward_error": (
            window.maximum_descriptor_relative_backward_error
        ),
        "idle_phase_reference_drift_v": resolved["idle_phase_reference_drift_v"],
        "output_rail_drift_v": resolved["output_rail_drift_v"],
    }


def richardson(coarse: float | None, fine: float | None) -> float | None:
    """First-order Richardson: backward Euler's error is O(h) (A50 Section 3.3)."""
    if coarse is None or fine is None:
        return None
    return 2.0 * fine - coarse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="cfly_reverification.json")
    args = parser.parse_args()

    _assert_no_src_import()
    original_cfly = a42.CFLY_A42_F
    started = time.time()

    ladders: dict[str, dict[str, list[dict]]] = {}
    for label, cfly_f in (("53.8uF", 53.8e-6), ("3uF", 3e-6)):
        ladders[label] = {}
        for fraction_label, fraction in (("7.76pct", 0.0776), ("7.77pct", 0.0777)):
            rows = [run_one(cfly_f, fraction, step) for step in SUB_STEPS_S]
            ladders[label][fraction_label] = rows

    a42.CFLY_A42_F = original_cfly
    _assert_no_src_import()

    summary: dict[str, dict] = {}
    for label in ladders:
        finest_776 = ladders[label]["7.76pct"][-1]
        second_776 = ladders[label]["7.76pct"][-2]
        finest_777 = ladders[label]["7.77pct"][-1]
        second_777 = ladders[label]["7.77pct"][-2]
        summary[label] = {
            "min_abs_vds_7p76_v_at_0p0625ps": finest_776["minimum_abs_switch_voltage_v"],
            "min_abs_vds_7p76_v_richardson": richardson(
                second_776["minimum_abs_switch_voltage_v"],
                finest_776["minimum_abs_switch_voltage_v"],
            ),
            "crossed_7p76_at_0p0625ps": finest_776["crossed_tolerance"],
            "crossed_7p77_at_0p0625ps": finest_777["crossed_tolerance"],
            "crossing_time_7p77_s_at_0p0625ps": finest_777["sign_change_time_s"],
            "crossing_time_7p77_s_richardson": richardson(
                second_777["sign_change_time_s"], finest_777["sign_change_time_s"]
            ),
            "boundary_section_1_published": BOUNDARY_SECTION_1[label],
        }
        published = BOUNDARY_SECTION_1[label]
        summary[label]["reproduced_min_abs_vds_7p76"] = bool(
            abs(
                summary[label]["min_abs_vds_7p76_v_at_0p0625ps"]
                - published["min_abs_vds_7p76_v"]
            )
            <= 0.5e-6
        )
        summary[label]["reproduced_crossing_time_7p77"] = bool(
            abs(
                summary[label]["crossing_time_7p77_s_at_0p0625ps"]
                - published["crossing_time_7p77_s"]
            )
            <= 5e-15
        )

    cross_comparison = {
        "crossing_time_difference_s": (
            summary["3uF"]["crossing_time_7p77_s_at_0p0625ps"]
            - summary["53.8uF"]["crossing_time_7p77_s_at_0p0625ps"]
        ),
        "min_abs_vds_7p76_difference_v": (
            summary["3uF"]["min_abs_vds_7p76_v_at_0p0625ps"]
            - summary["53.8uF"]["min_abs_vds_7p76_v_at_0p0625ps"]
        ),
        "qualitative_bracket_unchanged": bool(
            summary["3uF"]["crossed_7p76_at_0p0625ps"]
            == summary["53.8uF"]["crossed_7p76_at_0p0625ps"]
            and summary["3uF"]["crossed_7p77_at_0p0625ps"]
            == summary["53.8uF"]["crossed_7p77_at_0p0625ps"]
        ),
    }

    payload = {
        "script": Path(__file__).name,
        "purpose": "A51 step 2 - independent re-verification of BOUNDARY.md Section 1",
        "sub_steps_s": list(SUB_STEPS_S),
        "dead_time_s": a42.DEAD_TIME_S,
        "test_phase_index": a42.TEST_PHASE_INDEX,
        "ladders": ladders,
        "summary": summary,
        "cross_cfly_comparison": cross_comparison,
        "wall_clock_s": time.time() - started,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")

    print(f"wrote {args.output}  ({payload['wall_clock_s']:.1f} s)")
    for label in ("53.8uF", "3uF"):
        item = summary[label]
        published = item["boundary_section_1_published"]
        print(f"\nCFLY = {label}")
        print(
            f"  7.76% min|Vds| @0.0625ps = {item['min_abs_vds_7p76_v_at_0p0625ps']*1e3:.6f} mV"
            f"   (BOUNDARY Section 1: {published['min_abs_vds_7p76_v']*1e3:.3f} mV)"
            f"   reproduced={item['reproduced_min_abs_vds_7p76']}"
        )
        print(
            f"  7.76% crossed = {item['crossed_7p76_at_0p0625ps']}"
            f"   7.77% crossed = {item['crossed_7p77_at_0p0625ps']}"
        )
        print(
            f"  7.77% crossing time @0.0625ps = {item['crossing_time_7p77_s_at_0p0625ps']*1e6:.8f} us"
            f"   (BOUNDARY Section 1: {published['crossing_time_7p77_s']*1e6:.8f} us)"
            f"   reproduced={item['reproduced_crossing_time_7p77']}"
        )
        print(
            f"  Richardson: 7.76% min|Vds| = {item['min_abs_vds_7p76_v_richardson']*1e3:.6f} mV,"
            f" 7.77% crossing = {item['crossing_time_7p77_s_richardson']*1e6:.8f} us"
        )
    print(
        f"\n3uF - 53.8uF: crossing time {cross_comparison['crossing_time_difference_s']*1e12:.4f} ps,"
        f" 7.76% min|Vds| {cross_comparison['min_abs_vds_7p76_difference_v']*1e3:+.6f} mV,"
        f" bracket unchanged = {cross_comparison['qualitative_bracket_unchanged']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
