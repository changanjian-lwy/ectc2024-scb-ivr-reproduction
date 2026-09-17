"""Step-size convergence check for the retained negative-corrected candidate."""
import json
from pathlib import Path
import numpy as np

from p25_native_fixed_slot_ring import event_ring


HERE = Path(__file__).parent
OUT = HERE / "numerical_runs/05_negative_valley_corrected"


def main():
    candidate = json.loads((OUT / "negative_corrected_refined.json").read_text())
    z = np.asarray(candidate["initial_state"], dtype=float)
    target = candidate["negative_target_a"]
    inductance = candidate["inductance_nH"] * 1e-9
    ton = candidate["ton_ns"] * 1e-9
    rows = []
    for step in [1.0, 0.5, 0.25, 0.1]:
        r = event_ring(z, target, lphase=inductance, ton=ton,
                       max_step_ns=step)
        drift = r.final-z
        period = r.history[-1]["next_high_on_ns"]
        rows.append({
            "max_step_ns": step, "passed_events": r.passed,
            "period_ns": period,
            "max_voltage_return_V": float(np.max(abs(drift[1:5]))),
            "max_current_return_A": float(np.max(abs(drift[5:]))),
            "module_average_current_A": float(r.charge_a_ns.sum()/period),
            "state_return": drift.tolist(),
        })
    payload = {"candidate_unchanged": True, "runs": rows}
    (OUT / "step_convergence.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
