"""Exercise A55's path-accounting gate on A54's nominal saved state.

This is not an A55 optimization and does not close the dynamics gate. It uses
A54's unchanged near-ideal uniform-Ron periodic state only to prove that the
new monitor separates high-side, low-side and dead-time current exposure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A54_DIR = HERE.parent / "A54_epc2067_lphase_joint_tradeoff"
if str(A54_DIR) not in sys.path:
    sys.path.insert(0, str(A54_DIR))

import a54_boundary as B  # noqa: E402
from path_resolved_period import evaluate_period_map_with_paths  # noqa: E402


def main() -> int:
    key_states = json.loads((A54_DIR / "key_states.json").read_text())
    nominal = key_states["nominal"]
    boundary = B.build_boundary(
        phase_inductance_h=nominal["phase_inductance_h"],
        module_power_w=250.0,
    )
    result, integrals, loss = evaluate_period_map_with_paths(
        boundary,
        np.array(nominal["z_star"], dtype=float),
        coarse_step_s=62.5e-12,
        sub_step_s=5e-12,
    )
    payload = {
        "classification": "IMPLEMENTATION_GATE_SMOKE_ONLY",
        "source_state": "A54 key_states.json nominal",
        "not_an_optimization": True,
        "dynamics_caveat": (
            "A54 state and this smoke evaluation retain the old uniform "
            "1 uOhm solver resistance; do not cite the watts as an A55 result"
        ),
        "period_s": integrals.period_s,
        "natural_zvs_flags": list(result.natural_zvs_flags),
        "high_side_i2dt_a2s": list(integrals.high_side_a2s),
        "low_side_i2dt_a2s": list(integrals.low_side_a2s),
        "dead_time_i2dt_a2s": list(integrals.dead_time_a2s),
        "effective_resistance_ohm": {
            "high_side": loss.high_side_effective_resistance_ohm,
            "low_side": loss.low_side_effective_resistance_ohm,
        },
        "channel_loss_w_per_phase": {
            "high_side": list(loss.high_side_loss_w_per_phase),
            "low_side": list(loss.low_side_loss_w_per_phase),
        },
        "partial_channel_conduction_loss_w": loss.modeled_loss_w,
        "dead_time_i2_average_a2_per_phase": list(
            loss.dead_time_i2_average_a2_per_phase
        ),
        "unmodelled_dead_time_current_present": loss.has_unmodeled_dead_time_current,
        "complete_total_loss": loss.is_complete_total_loss,
    }
    (HERE / "path_gate_smoke.json").write_text(json.dumps(payload, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
