"""A235 cosim cfgs: the final configuration on plant V7 for the boards V7 has not run (boards.py): F0 (fast devices,
L0), S0 (slow devices, L0), N13 (nominal, 1.3 L0), one module.
- stage 1: each board's start-up to 160 us at 25 C with dton = the mean V5 -> V7 shift of its corner (nominal -0.22 ns;
  slow +0.39 ns, S75's), to read Vo(143.5 us);
- stage 2 (trims from stage 1 by BOUNDARY Section 2's rule, a235_trims.json): per board at 25 C +4.8 V / 1 us, -4.8 V /
  1 us, +62.5 A and -8 V / 10 us at 500 us, end 620 us; S0 at 125 C its start-up to 200 us and +4.8 V / 1 us at 500 us.
    python3 make_cfgs.py 1   -> cosim/cfg_t_*.json, cosim/ORDER_S1.txt
    python3 make_cfgs.py 2   -> cosim/cfg_r_*.json, cosim/ORDER_S2.txt (needs a235_trims.json)"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
_s = importlib.util.spec_from_file_location("a235_boards", HERE / "boards.py")
B = importlib.util.module_from_spec(_s)
_s.loader.exec_module(B)
BOARDS = ("F0", "S0", "N13")
DTON1 = {"F0": -0.22, "N13": -0.22, "S0": 0.39}
EVENTS = {"lp48": {"line_step": {"dv": 4.8, "slew_us": 1.0, "t_us": 500.0}},
          "lm48": {"line_step": {"dv": -4.8, "slew_us": 1.0, "t_us": 500.0}},
          "sp62": {"load_step": {"t_us": 500.0, "i_a": 62.5}},
          "lm80": {"line_step": {"dv": -8.0, "slew_us": 10.0, "t_us": 500.0}}}


def write(rows, order):
    COS.mkdir(exist_ok=True)
    for n, c in rows:
        (COS / f"cfg_{n}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / order).write_text("\n".join(n for n, _ in rows) + "\n")
    print(len(rows), "cfgs ->", order)


def named(c, n, what):
    c["out"] = f"run_{n}.json"
    c["note"] = (f"A235 {n}: {what}; final configuration on plant V7 (r_core {c['circuit']['r_core']} ohm, ton_s_ns {c['ton_s_ns']}, "
                 f"lead {c.get('hand_lead_us', 0)} us, skip {'on' if 'skip' in c else 'off'})")
    return n, c


if __name__ == "__main__":
    if sys.argv[1] == "1":
        rows = []
        for b in BOARDS:
            c = B.final(b, "25", DTON1[b]); c["t_end_us"] = 160.0
            rows.append(named(c, f"t_{b}", f"{b} at 25 C, start-up to 160 us, dton {DTON1[b]} ns from V5"))
        write(rows, "ORDER_S1.txt")
    else:
        dt = json.loads((HERE / "a235_trims.json").read_text())["dton_ns"]
        rows = []
        for b in BOARDS:
            for e, ev in EVENTS.items():
                c = B.final(b, "25", dt[b]); c.update(ev); c["t_end_us"] = 620.0
                rows.append(named(c, f"r_{b}_{e}", f"{b} at 25 C, {json.dumps(ev)}"))
        c = B.final("S0", "hot", dt["S0"]); c["t_end_us"] = 200.0
        rows.append(named(c, "r_S0h_start", "S0 at 125 C, start-up to 200 us (trim set at 25 C)"))
        c = B.final("S0", "hot", dt["S0"]); c.update(EVENTS["lp48"]); c["t_end_us"] = 620.0
        rows.append(named(c, "r_S0h_lp48", "S0 at 125 C, +4.8 V / 1 us at 500 us"))
        write(rows, "ORDER_S2.txt")
