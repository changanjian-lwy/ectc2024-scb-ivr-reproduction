"""A215 cosim cfgs: rows of the final configuration on plant V6 with the Ton path's registers (cfg "ton_lat" = M clocks,
scb_ctrl cfg_ton_lat) and the lower Ton limit of A208 (ton_min_ns 4.0, also where the source row had another value:
BOUNDARY Section 1 says why the source records stay the references).
  m16_* / m32_*   nine source rows at M = 16 and 32 (A212's nominal rows, A206's binding rows, A208 / A210's 30 % rows);
  k8_*            two rows at an 8 ns clock (fb 8, the same 31.25 ps LSB), ton_lat 8 (the same 64 ns);
  k16_*           one row at a 16 ns clock (fb 9), ton_lat 4.
  python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
TON_MIN_NS = 4.0
SRC = {"n_l_p48_2us": "A212_p24_nominal_rows_v6", "n_l_m48_1us": "A212_p24_nominal_rows_v6",
       "n_l_m80_10us": "A212_p24_nominal_rows_v6", "n_s_p62": "A212_p24_nominal_rows_v6",
       "B_S75_hot_p5_ls0p3": "A206_p24_low_side_zvs_turn_on", "B_N75_25_p4_ls0p3": "A206_p24_low_side_zvs_turn_on",
       "B_S75_25_p4_ls0p3": "A206_p24_low_side_zvs_turn_on", "m30": "A208_p24_ton_lower_limit",
       "r_N75_25_30": "A210_p24_load_range_boards"}
LATS = (16, 32)
CLOCKS = (("k8", 8.0, 8, 8, ("n_s_p62", "n_l_p48_2us")), ("k16", 16.0, 9, 4, ("n_s_p62",)))   # tag, t_clk ns, fb, ton_lat, rows


def source(name):
    return json.loads((TA / SRC[name] / "cosim" / f"cfg_{name}.json").read_text())


def write(tag, name, **over):
    c = source(name)
    c = dict(c, ton_min_ns=TON_MIN_NS, **over)
    c["out"] = f"run_{tag}_{name}.json"
    c["note"] = (f"A215 {tag}_{name}: {SRC[name][:4]}'s {name} with ton_lat {c['ton_lat']} clocks of {c['t_clk_ns']:g} ns "
                 f"(fb {c['fb']}), lower Ton limit {TON_MIN_NS:g} ns | " + c["note"])
    (COS / f"cfg_{tag}_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    return f"{tag}_{name}", c["t_end_us"]


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    rows = [write(f"m{m}", n, ton_lat=m) for m in LATS[:1] for n in SRC]
    rows += [write(tag, n, t_clk_ns=t, fb=fb, ton_lat=m) for tag, t, fb, m, names in CLOCKS for n in names[:1]]
    rows += [write(f"m{m}", n, ton_lat=m) for m in LATS[1:] for n in SRC]
    rows += [write(tag, n, t_clk_ns=t, fb=fb, ton_lat=m) for tag, t, fb, m, names in CLOCKS for n in names[1:]]
    (COS / "ORDER.txt").write_text("\n".join(r[0] for r in rows) + "\n")
    print(len(rows), "cfgs; run-equivalents of 900 us:", round(sum(r[1] for r in rows) / 900.0, 2))
