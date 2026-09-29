"""Read-only replay of D42 saved 4 and 4.9 mOhm seeds at original tolerances.

python3 -m scripts.audit_p25_saved_return_acceptance
No Newton optimization, Jacobian recomputation or archive write. JSON stdout.
"""
import json
from dataclasses import asdict
from pathlib import Path
import numpy as np
from scripts import audit_p25_single_sensor_closure as solver


def run_saved_return_audit():
    source=Path(__file__).resolve().parents[1]/"symbolic_derivations/02_P25_native/diagnostics/D42_damping_continuation.json"
    archive=json.loads(source.read_text())
    rows=[]
    for resistance in (.004,.0049):
        matches=[p for p in archive["points"] if p["R_ohm"]==resistance]
        if len(matches)!=1:
            raise ValueError("saved resistance point missing or duplicated")
        p=matches[0]
        contract,options=solver.context(solver.P25_SCALE["phase_shift_s"],winding_ohm=(resistance,)*3)
        z=np.array([p["z_star"][name] for name in solver.NAMES])
        _,result=solver.section_map(contract,options,z)
        rows.append(dict(R_ohm=resistance,archived_status=p["status"],replayed_status=result.status,
            failed_mode=result.attempt.failed_mode,
            accepted_modes=[s.mode for s in result.attempt.steps if s.outcome.memory is not None],
            return_check=None if result.state_return is None else asdict(result.state_return)))
    return dict(scope="SAVED_SEED_REPLAY_ORIGINAL_CONTRACT_NOT_NEWTON_OR_STABILITY_RECOMPUTATION",
                rows=rows)


def encode_numpy(value):
    if isinstance(value,np.generic):
        return value.item()
    raise TypeError(f"unsupported JSON type {type(value).__name__}")


if __name__=="__main__":
    print(json.dumps(run_saved_return_audit(),indent=2,default=encode_numpy))
