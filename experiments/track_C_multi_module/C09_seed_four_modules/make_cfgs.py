"""C09 configurations: C06's 18 rows (the four-module final design: A129's g125 + modules 4 + slave_floor 1) with the
adopted single-module phase-1 cap and handover restart (cfg vff rel_q8 320, rel_lp 1, seed 1) in every module, C06's
timing (steps at 800 us); plus C06's s_m25 unchanged except for the step, moved to 800.1831 us so it lands 81.3 ns
after the master's phase-1 turn-on, where C08's s_m25 step landed (c06al_s_m25). Writes cosim/cfg_<row>.json, ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
C06 = HERE.parent / "C06_slave_floor" / "cosim"
Q = {"rel_q8": 320, "rel_lp": 1, "seed": 1}
T_ALIGN_US = 800.1831                     # C06 s_m25's phase-1 turn-on 800.1018 us + C08's offset 81.3 ns


def main():
    rows = (C06 / "ORDER.txt").read_text().split()
    order = []
    (HERE / "cosim").mkdir(exist_ok=True)
    for row in rows:
        c = json.loads((C06 / f"cfg_{row}.json").read_text())
        c["vff"] = dict(c["vff"], **Q)
        c["note"] = f"C09 {row}: C06's {row} with the adopted vff cap and restart (rel_q8 320, rel_lp 1, seed 1)."
        c["out"] = f"run_{row}.json"
        (HERE / "cosim" / f"cfg_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(row)
    c = json.loads((C06 / "cfg_s_m25.json").read_text())
    c["load_step"] = dict(c["load_step"], t_us=T_ALIGN_US)
    c["note"] = "C09 c06al_s_m25: C06's s_m25 (no change to the design) with the step at C08's offset after phase 1's turn-on."
    c["out"] = "run_c06al_s_m25.json"
    (HERE / "cosim" / "cfg_c06al_s_m25.json").write_text(json.dumps(c, indent=1) + "\n")
    order.append("c06al_s_m25")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


def ph1_on(d, t1, t2):
    return [q["t_s"] for q in d["turnons_last"] if q["phase"] == 1 and t1 <= q["t_s"] <= t2]


def contingency(rows):
    """BOUNDARY criterion 3: C06's row with its step moved to C09's offset after the master's phase-1 turn-on
    (cosim/cfg_c06al9_<row>.json, ORDER_c06al9.txt)."""
    names = []
    for row in rows:
        c = json.loads((C06 / f"cfg_{row}.json").read_text())
        key = "load_step" if c.get("load_step") else "line_step"
        t0 = c[key]["t_us"] * 1e-6
        r9 = json.loads((HERE / "cosim" / f"run_{row}.json").read_text())
        r6 = json.loads((C06 / f"run_{row}.json").read_text())
        off = t0 - max(ph1_on(r9, 0.0, t0))
        t_al = min(ph1_on(r6, t0 - 1e-6, t0 + 1e-6), key=lambda t: abs(t + off - t0)) + off
        c[key] = dict(c[key], t_us=round(t_al * 1e6, 4))
        c["note"] = f"C09 c06al9_{row}: C06's {row} (no change to the design) with the step at C09's offset ({off * 1e9:.1f} ns)."
        c["out"] = f"run_c06al9_{row}.json"
        (HERE / "cosim" / f"cfg_c06al9_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
        names.append(f"c06al9_{row}")
        print(names[-1], c[key]["t_us"], "us")
    (HERE / "cosim" / "ORDER_c06al9.txt").write_text("\n".join(names) + "\n")


if __name__ == "__main__":
    import sys
    contingency(sys.argv[2:]) if sys.argv[1:2] == ["--contingency"] else main()
