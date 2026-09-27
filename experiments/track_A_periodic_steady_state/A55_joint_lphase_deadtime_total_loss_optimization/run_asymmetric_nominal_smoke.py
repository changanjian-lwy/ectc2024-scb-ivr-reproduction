"""Re-solve only A54's nominal-L point with A55 asymmetric Ron dynamics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
A53_DIR = BASE / "A53_lphase_zvs_load_tradeoff"
A54_DIR = BASE / "A54_epc2067_lphase_joint_tradeoff"
for directory in (HERE, A53_DIR, A54_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import a53_solve as S  # noqa: E402
from asymmetric_ron_dynamics import (  # noqa: E402
    asymmetric_ron_context,
    build_epc2067_boundary,
)
from path_resolved_period import evaluate_period_map_with_paths  # noqa: E402


def main() -> int:
    saved = json.loads((A54_DIR / "key_states.json").read_text())["nominal"]
    boundary = build_epc2067_boundary(
        phase_inductance_h=saved["phase_inductance_h"],
        module_power_w=250.0,
    )
    with asymmetric_ron_context():
        solved = S.solve_fixed_point(
            boundary,
            np.array(saved["z_star"], dtype=float),
            coarse_step_s=62.5e-12,
            sub_step_s=5e-12,
            max_iterations=30,
            picard_iterations=10,
            picard_damping=0.5,
        )
        period, integrals, loss = evaluate_period_map_with_paths(
            boundary,
            solved["z_star"],
            coarse_step_s=62.5e-12,
            sub_step_s=5e-12,
        )
    payload = {
        "classification": "DYNAMICS_GATE_NOMINAL_SMOKE_ONLY",
        "not_an_optimization": True,
        "source_seed": "A54 key_states.json nominal",
        "boundary": {
            "module_power_w": boundary.module_power_w,
            "phase_inductance_h": boundary.phase_inductance_h,
            "dead_time_s": boundary.dead_time_s,
            "high_side_on_resistance_ohm": boundary.high_side_on_resistance_ohm,
            "low_side_on_resistance_ohm": boundary.low_side_on_resistance_ohm,
        },
        "solve": {
            "converged": solved["converged"],
            "relative_residual": solved["final_relative_residual"],
            "natural_zvs_flags": solved["final_natural_zvs_flags"],
            "average_output_v": solved["final_orbit_metrics"]["average_output_v"],
            "average_load_power_w": solved["final_orbit_metrics"][
                "average_load_power_w"
            ],
            "maximum_abs_phase_current_a": solved["safety"][
                "maximum_abs_phase_current_a"
            ],
            "within_current_limit": solved["safety"]["within_limit"],
            "z_star": solved["z_star"].tolist(),
        },
        "path_check": {
            "natural_zvs_flags": list(period.natural_zvs_flags),
            "high_side_i2dt_a2s": list(integrals.high_side_a2s),
            "low_side_i2dt_a2s": list(integrals.low_side_a2s),
            "dead_time_i2dt_a2s": list(integrals.dead_time_a2s),
            "partial_channel_conduction_loss_w": loss.modeled_loss_w,
            "unmodelled_dead_time_current_present": (
                loss.has_unmodeled_dead_time_current
            ),
            "complete_total_loss": loss.is_complete_total_loss,
        },
    }
    (HERE / "asymmetric_nominal_smoke.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
