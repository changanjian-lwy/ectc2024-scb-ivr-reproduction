"""A180 predictions (written before the runs): how a +4.8 V input step divides over the four rails.

Base: the flying capacitors hold their charge over a 1 us ramp, so rail 1 = vin - Vcs1 takes the whole step.
Ideal clamp (switched, no drop, instantaneous): charge sharing between the ladder (four C_DC in series across vin) and
the flying capacitors, each Cs_k hanging from its ladder node d(4-k) to ground (x_k = 0 while SL_k conducts):
    node d1: (2 Cd + Cs) dd1 - Cd dd2 = 0;  d2: -Cd dd1 + (2 Cd + Cs) dd2 - Cd dd3 = 0;  d3: -Cd dd2 + (2 Cd + Cs) dd3 = Cd dV
rails: dV - dd3, dd3 - dd2, dd2 - dd1, dd1.  Cd -> inf gives dV / 4 each.
Passive diode of vf (no pumping): conducts once the unloaded ladder (dd3 = 3/4 dV) is vf above Vcs1, so rail 1 keeps
about dV - (3/4 dV - vf) at most... bounded below by the ideal-clamp value.
Writes a180_predictions.json.
"""
import json
from pathlib import Path

import numpy as np

CS, DV = 6e-6, 4.8


def ideal_clamp(cd, cs=CS, dv=DV):
    a = np.array([[2 * cd + cs, -cd, 0], [-cd, 2 * cd + cs, -cd], [0, -cd, 2 * cd + cs]])
    d1, d2, d3 = np.linalg.solve(a, [0, 0, cd * dv])
    return [round(float(x), 3) for x in (dv - d3, d3 - d2, d2 - d1, d1)]


def passive(cd, vf, cs=CS, dv=DV):
    """Upper estimate: the clamp engages after the unloaded divider has risen vf above Vcs1; beyond that the
    network shares the remaining rise. Ignores pumping (A180 predicts d07 pumps, see BOUNDARY Section 3)."""
    engage = max(0.0, 0.75 * dv - vf)
    if engage == 0.0:
        return round(dv, 3)
    frac = engage / (0.75 * dv)
    return round(dv - frac * (dv - ideal_clamp(cd, cs, dv)[0]), 3)


if __name__ == "__main__":
    out = {"ideal_clamp_rails_up_4p8V": {f"cdc_{int(c * 1e6)}uF": ideal_clamp(c) for c in (6e-6, 20e-6, 60e-6, 1.0)},
           "passive_rail1_up_4p8V": {f"vf_{vf}_cdc_20uF": passive(20e-6, vf) for vf in (0.7, 3.0)},
           "base_rail1_up_4p8V": DV}
    Path(__file__).with_name("a180_predictions.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
