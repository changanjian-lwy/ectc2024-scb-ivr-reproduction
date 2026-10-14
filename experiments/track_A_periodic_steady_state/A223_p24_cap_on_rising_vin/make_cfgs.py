"""A223 cosim cfgs: the final configuration (plant V7, A222's mode-S trims, ton_lat 16, lower Ton limit 4 ns, skipping
on the light-load rows) in two arms - off: as adopted; g25: cfg vff rel_gate 25 (scb_vff's relative cap only at
samples where Vin rises by >= 25 codes = 0.5 V; A223). One module, 25 C unless named.
- w rows (problem 9): load released at 300 us, re-applied at 380 us, end 460 us - N0 to 0 / 5 / 20 % and back to
  full load (+250 / +237.5 / +200 A), N75 to 5 % (+237.5 A), S75 at 125 C to 30 % (+175 A, its minimum load);
- u_N0: N0 to 5 %, +62.5 A (A221's u row);
- k_N0: A222's k_n_s_p62 (N0 +62.5 A at 500 us); its off arm is the identity check against A222's record;
- l_N0_p48 / l_N0_m80: A215's N0 +4.8 V / 2 us and -8 V / 10 us at 500 us on V7;
- k_S75h: A221's S75 125 C +4.8 V / 1 us at 500.3155 us (the tightest row, A206) with A222's S75 trim.
    python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
LSB_NS = 0.03125
TRIM = {"N0": 750 * LSB_NS, "N75": 751 * LSB_NS, "S75": 1147 * LSB_NS}      # A222
R_CORE = {"N0": 2.8985, "N75": 2.1739, "S75": 2.1739}                         # A221
SKIP_75 = {"hi_mv": 5.0, "lo_mv": 1.0, "res_ofs_a": 3.636, "zcd_a": 3.636}   # A221: 8 ns x Vo / L at 0.75 L0
GATE = 25


def load(src):
    return json.loads((TA / src).read_text())


def final(c, board):
    c = copy.deepcopy(c)
    c["circuit"] = dict(c["circuit"], r_core=R_CORE[board])
    c["ton_s_ns"] = TRIM[board]
    c.pop("snap_us", None)
    return c


def w(c, board, i_full, i_low, t_end=460.0):
    """Released from full load to i_low at 300 us, back to full load at 380 us."""
    c = final(c, board)
    c.pop("line_step", None)
    c["load_step"] = {"t_us": 300.0, "i_a": -(i_full - i_low)}
    c["load_step2"] = {"t_us": 380.0, "i_a": i_full - i_low}
    c["t_end_us"], c["debug_edges_us"] = t_end, [379.0, 399.9]
    return c


U = "A221_p24_core_loss_and_pause/cosim/cfg_u_N0_25_5_s62.json"
Z75 = "A221_p24_core_loss_and_pause/cosim/cfg_z_N75_25_10.json"
S75H = "A221_p24_core_loss_and_pause/cosim/cfg_k_B_S75_hot_p5_ls0p3.json"
s75w = w(load(S75H), "S75", 250.0, 75.0)
s75w["skip"] = dict(SKIP_75)
u = final(load(U), "N0")
ROWS = {
    "w0_N0": (w(load(U), "N0", 250.0, 0.0), "N0, released to no load, +250 A at 380 us"),
    "w5_N0": (w(load(U), "N0", 250.0, 12.5), "N0, released to 5 %, +237.5 A at 380 us"),
    "w20_N0": (w(load(U), "N0", 250.0, 50.0), "N0, released to 20 %, +200 A at 380 us"),
    "w5_N75": (w(load(Z75), "N75", 250.0, 12.5), "N75, released to 5 %, +237.5 A at 380 us"),
    "w30_S75h": (s75w, "S75 at 125 C, released to 30 %, +175 A at 380 us"),
    "u_N0": (u, "N0, released to 5 %, +62.5 A at 380 us (A221's u row)"),
    "k_N0": (load("A222_p24_v7_startup_trim/cosim/cfg_k_n_s_p62.json"), "N0, +62.5 A at 500 us (A222's k row)"),
    "l_N0_p48": (final(load("A215_p24_buildable_ton_path/cosim/cfg_m16_n_l_p48_2us.json"), "N0"), "N0, +4.8 V / 2 us at 500 us"),
    "l_N0_m80": (final(load("A215_p24_buildable_ton_path/cosim/cfg_m16_n_l_m80_10us.json"), "N0"), "N0, -8 V / 10 us at 500 us"),
    "k_S75h": (final(load(S75H), "S75"), "S75 at 125 C, +4.8 V / 1 us at 500.3155 us (A221's k row)"),
}

if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    order = []
    for name, (c, what) in ROWS.items():
        for arm in ("off", f"g{GATE}"):
            n = f"{name}_{arm}"
            x = copy.deepcopy(c)
            if arm != "off":
                x["vff"] = dict(x["vff"], rel_gate=GATE)
            x["out"] = f"run_{n}.json"
            x["note"] = (f"A223 {n}: {what}; final configuration on plant V7 (r_core {x['circuit']['r_core']} ohm, "
                         f"ton_s_ns {x['ton_s_ns']}), skip {x.get('skip')}"
                         + (f", phase 1's relative cap only while Vin rises (vff rel_gate {GATE})" if arm != "off" else ""))
            (COS / f"cfg_{n}.json").write_text(json.dumps(x, indent=1) + "\n")
            order.append(n)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")
