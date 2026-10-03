"""A119 configurations: A118's 1 MHz candidate (f6: timed turn-off with a 2 A floor, Cs 6 uF, 10%, 60 kHz) on the
rest of the standard matrix (scb_ivr.cosim.matrix.ROWS), times x5 for 1 MHz: steps at 2000 us, runs to 2500 us (no
step) or 3000 us. A118 already ran n0, s_m62, s_p62 and the 1 us line steps (and 5 / 20 us). Writes cosim/cfg_*.json
and cosim/ORDER.txt."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import ROWS  # noqa: E402

BASE = HERE.parent / "A118_p24_floor_turn_off" / "cosim" / "cfg_f6_n0.json"
DONE = {"n0", "s_m62", "s_p62", "l_m48_1us", "l_p48_1us"}
T_STEP_US, K = 2000.0, 5.0

if __name__ == "__main__":
    names = []
    for row, r in ROWS.items():
        if row in DONE:
            continue
        c = json.loads(BASE.read_text())
        m, sig = r.get("driver", (0.0, 0.0))
        c["driver"] = {"m_ns": m, "sigma_ps": sig, "seed": 1}
        c.pop("load_step", None); c.pop("line_step", None)
        c["t_end_us"] = 2500.0
        if "load_step" in r:
            c["load_step"] = {"t_us": T_STEP_US, "i_a": r["load_step"]}; c["t_end_us"] = 3000.0
        if "line_step" in r:
            dv, slew = r["line_step"]
            c["line_step"] = {"t_us": T_STEP_US, "dv": dv, "slew_us": slew}; c["t_end_us"] = 3000.0
        c["note"] = f"A119 {row}: A118's f6 (floor 2 A, Cs 6 uF, 1 MHz 10%) on the standard matrix row {row} (times x5)."
        c["out"] = f"run_{row}.json"
        (HERE / "cosim" / f"cfg_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
        names.append(row)
    order = [n for n in names if n.startswith(("m3", "l_m80", "j100"))] + [n for n in names if not n.startswith(("m3", "l_m80", "j100"))]
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(names), "configurations:", ", ".join(order))
