"""A225 cosim cfgs: controller items 2, 5 and 6 again on the candidate configuration of A223 / A224 / A227 (plant V7,
A222's trims, vff rel_gate 25, kd 355 ns/V with a 2-code dead band held at the lower Ton limit, skipping with res_ofs_a = zcd_a = 8 ns x Vo / L), one
module.
- a rows (item 2, A198's rows): +4.8 V / 1 us at 2 / 10 / 20 us after mode P's entry on S75 at 125 C (entry
  133.404 us on V7) and 25 C (144.004 us), and on N0 at 2 us (144.004 us); end at the step + 60 us;
- u rows (item 6, A214's rows): the start-up into 30 % of the load (r_load 13.33 mOhm from t = 0) on N0, S75 25 C
  and S75 125 C, to 300 us;
- s rows (item 5, A195's two-cycle orbit): S75 at 25 C in steady state to 500 us at full load and at 50 % of the
  load (A211's widest orbit on V6), and both again with twice r_core (rc2: half the core's damping, A221's bracket).
    python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
KD, DB, GATE = 355.0, 2, 25
ENTRY = {"S75h": 133.404, "S75": 144.004, "N0": 144.004}       # mode P's entry on V7 (A223 / A222 records)
SRC = {"S75h": "A223_p24_cap_on_rising_vin/cosim/cfg_k_S75h_g25.json",
       "S75": "A222_p24_v7_startup_trim/cosim/cfg_s_S75_25_r2.json",
       "N0": "A223_p24_cap_on_rising_vin/cosim/cfg_k_N0_g25.json"}
WHAT = {"S75h": "S75 at 125 C", "S75": "S75 at 25 C", "N0": "N0 at 25 C"}
SKIP_A = {"S75h": 3.636, "S75": 3.636, "N0": 2.727}               # A221: 8 ns x Vo / L


def final(board):
    c = json.loads((TA / SRC[board]).read_text())
    c["vff"] = dict(c["vff"], rel_gate=GATE)
    c["kd_ns_per_v"], c["kd_db"], c["kd_hold"] = KD, DB, 1
    c["skip"] = {"hi_mv": 5.0, "lo_mv": 1.0, "res_ofs_a": SKIP_A[board], "zcd_a": SKIP_A[board]}
    for k in ("line_step", "load_step", "load_step2", "snap_us", "debug_edges_us"):
        c.pop(k, None)
    return c


def a_row(board, d_us):
    c = final(board)
    t = round(ENTRY[board] + d_us, 3)
    c["line_step"] = {"dv": 4.8, "slew_us": 1.0, "t_us": t}
    c["t_end_us"] = round(t + 60.0, 3)
    return f"a_{board}_d{d_us}", c, f"{WHAT[board]}, +4.8 V / 1 us at {t} us = {d_us} us after mode P's entry"


def u_row(board):
    c = final(board)
    c["circuit"] = dict(c["circuit"], r_load=1.0 / 75.0)
    c["t_end_us"] = 300.0
    return f"u_{board}_30", c, f"{WHAT[board]}, start-up into 30 % of the load (13.333 mOhm from t = 0)"


def s_row(share, rc2=False):
    c = final("S75")
    if share < 100:
        c["circuit"] = dict(c["circuit"], r_load=1.0 / (2.5 * share))
    if rc2:
        c["circuit"] = dict(c["circuit"], r_core=2 * c["circuit"]["r_core"])
    c["t_end_us"] = 500.0
    return (f"s_S75_{share}" + ("_rc2" if rc2 else ""), c,
            f"{WHAT['S75']}, steady state at {share} % of the load to 500 us" + (", r_core x 2 (rc2)" if rc2 else ""))


ROWS = ([a_row(b, d) for b in ("S75h", "S75") for d in (2, 10, 20)] + [a_row("N0", 2)] + [u_row(b) for b in ("N0", "S75", "S75h")]
        + [s_row(100), s_row(50), s_row(100, True), s_row(50, True)])

if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    for name, c, what in ROWS:
        c = copy.deepcopy(c)
        c["out"] = f"run_{name}.json"
        c["note"] = (f"A225 {name}: {what}; final configuration on plant V7 (r_core {c['circuit']['r_core']} ohm, ton_s_ns "
                     f"{c['ton_s_ns']}), vff rel_gate {GATE}, kd {KD} ns/V (dead band {DB} codes, held at the lower limit), skip {c.get('skip')}")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(n for n, _, _ in ROWS) + "\n")
    print(len(ROWS), "cfgs")
