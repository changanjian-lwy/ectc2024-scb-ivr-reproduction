"""A230 cosim cfgs: start-ups into light and full load on the adopted configuration (plant V7, A222's trims, skipping,
vff rel_gate 25, kd 355 ns/V dead band 2, kd_hold 1, kd_band_ns 4.0; A229), one module, 25 C unless named, in two arms:
base (the handover requested once a Vo sample reaches 1.045 V, A188) and lead (cfg hand_lead_us 0.7: Vo + 0.7 us x its
slope since the previous sample, A230). The load resistance is set from t = 0 (A214's method).
- light rows to 300 us: N0 into 0 / 10 / 30 %, N75 into 0 / 30 %, S75 into 30 % at 25 and 125 C;
- full-load rows to 200 us: S75 at 125 C (its request fires, A188), N0 and S75 at 25 C (it never fires: lead = base).
    python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
LEAD_US = 0.7
SRC = {"N0": "A223_p24_cap_on_rising_vin/cosim/cfg_k_N0_g25.json",
       "N75": "A223_p24_cap_on_rising_vin/cosim/cfg_w5_N75_g25.json",
       "S75": "A222_p24_v7_startup_trim/cosim/cfg_s_S75_25_r2.json",
       "S75h": "A223_p24_cap_on_rising_vin/cosim/cfg_k_S75h_g25.json"}
WHAT = {"N0": "N0 at 25 C", "N75": "N75 at 25 C", "S75": "S75 at 25 C", "S75h": "S75 at 125 C"}
SKIP_A = {"N0": 2.727, "N75": 3.636, "S75": 3.636, "S75h": 3.636}       # A221: 8 ns x Vo / L
LIGHT = (("N0", 0), ("N0", 10), ("N0", 30), ("N75", 0), ("N75", 30), ("S75", 30), ("S75h", 30))
FULL = ("S75h", "N0", "S75")


def adopted(board):
    c = json.loads((TA / SRC[board]).read_text())
    for k in ("line_step", "load_step", "load_step2", "snap_us", "debug_edges_us", "out", "note"):
        c.pop(k, None)
    assert c["hand_vo_v"] == 1.045 and c["circuit"]["r_core"] in (2.8985, 2.1739)
    c["vff"] = dict(c["vff"], rel_gate=25)
    c.update(kd_ns_per_v=355.0, kd_db=2, kd_hold=1, kd_band_ns=4.0)
    c["skip"] = {"hi_mv": 5.0, "lo_mv": 1.0, "res_ofs_a": SKIP_A[board], "zcd_a": SKIP_A[board]}
    return c


def row(board, share, arm):
    c = adopted(board)
    if share < 100:
        c["circuit"] = dict(c["circuit"], r_load=1.0 / (2.5 * share) if share else 1000.0)
    c["t_end_us"] = 300.0 if share < 100 else 200.0
    if arm == "lead":
        c["hand_lead_us"] = LEAD_US
    name = f"u_{board}_{share}_{arm}"
    load = f"{share} % of the load" + (" (1 kOhm)" if share == 0 else f" ({1000 / (2.5 * share):.3f} mOhm)" if share < 100 else "")
    c["out"] = f"run_{name}.json"
    c["note"] = (f"A230 {name}: {WHAT[board]}, start-up into {load} from t = 0, to {c['t_end_us']} us; adopted configuration "
                 f"(V7 r_core {c['circuit']['r_core']} ohm, ton_s_ns {c['ton_s_ns']}, skip, rel_gate 25, kd 355 / db 2 / hold / band 4 ns); "
                 + (f"handover request on Vo + {LEAD_US} us x slope >= 1.045 V" if arm == "lead" else "handover request on Vo >= 1.045 V"))
    return name, c


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    rows = [row(b, s, a) for b, s in LIGHT for a in ("base", "lead")] + [row(b, 100, a) for b in FULL for a in ("base", "lead")]
    for name, c in rows:
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(n for n, _ in rows) + "\n")
    print(len(rows), "cfgs")
