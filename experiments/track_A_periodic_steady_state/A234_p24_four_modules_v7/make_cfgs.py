"""A234 cosim cfgs: four modules on plant V7 for the first time (25 C, nominal L0 boards, common Ton as C12 / C13:
modules 4, slave_floor 1), from the one-module final configuration (a230 make_cfgs.adopted("N0")) without skipping
(the slaves do not follow a pause, A216). Arms: d0 = the final configuration before A229 (no gate, no derivative
term, no handover lead) and b = the final configuration (A229 + A231). Rows (system totals as C12): +4.8 V / 1 us,
+250 A (62.5 A per module) and -8 V / 10 us at 400 us, end 500 / 500 / 510 us.
    python3 make_cfgs.py            -> cosim/cfg_*.json, cosim/ORDER.txt
    python3 make_cfgs.py smoke      -> tmp/a234_smoke/cfg_smoke.json (arm b to 20 us, timing only)"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
_s = importlib.util.spec_from_file_location("a230_make_cfgs", TA / "A230_p24_handover_slope_lead" / "make_cfgs.py")
M30 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M30)
T_EV = 400.0
ROWS = {"l_p48_1us": ({"line_step": {"dv": 4.8, "slew_us": 1.0, "t_us": T_EV}}, 500.0),
        "s_p250": ({"load_step": {"t_us": T_EV, "i_a": 250.0}}, 500.0),
        "l_m80_10us": ({"line_step": {"dv": -8.0, "slew_us": 10.0, "t_us": T_EV}}, 510.0)}


def row(name, arm):
    c = M30.adopted("N0")
    c.pop("skip")
    c["modules"], c["slave_floor"] = 4, 1
    if arm == "d0":
        c["vff"] = {k: v for k, v in c["vff"].items() if k != "rel_gate"}
        for k in ("kd_ns_per_v", "kd_db", "kd_hold", "kd_band_ns"):
            c.pop(k)
    else:
        c["hand_lead_us"] = 0.7
    ev, t_end = ROWS[name]
    c.update(ev)
    c["t_end_us"] = t_end
    n = f"m4_{name}_{arm}"
    c["out"] = f"run_{n}.json"
    c["note"] = (f"A234 {n}: four modules (common Ton, slave floor), N0 boards at 25 C, plant V7 (r_core {c['circuit']['r_core']} ohm, "
                 f"ton_s_ns {c['ton_s_ns']}), no skipping; {json.dumps(ev)}; "
                 + ("final configuration before A229" if arm == "d0" else "final configuration (rel_gate 25, kd 355 / db 2 / hold / band 4 ns, hand_lead 0.7)"))
    return n, c


if __name__ == "__main__":
    if sys.argv[1:] == ["smoke"]:
        n, c = row("l_p48_1us", "b")
        c.pop("line_step"); c["t_end_us"] = 20.0; c["out"] = "run_smoke.json"
        d = HERE.parents[2] / "tmp" / "a234_smoke"
        d.mkdir(parents=True, exist_ok=True)
        (d / "cfg_smoke.json").write_text(json.dumps(c, indent=1) + "\n")
        print(d / "cfg_smoke.json")
    else:
        COS.mkdir(exist_ok=True)
        rows = [row(r, a) for r in ROWS for a in ("d0", "b")]
        for n, c in rows:
            (COS / f"cfg_{n}.json").write_text(json.dumps(c, indent=1) + "\n")
        (COS / "ORDER.txt").write_text("\n".join(n for n, _ in rows) + "\n")
        print(len(rows), "cfgs")
