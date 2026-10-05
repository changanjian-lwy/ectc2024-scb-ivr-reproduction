"""A143 cosim cfgs: the adopted single-module design (A141 arm F: A136 q + vff seed 2 + floor_late 1) with phase 1's
comparator phase shortened (cfg lo_learn K instead of 1024; cfg only, no RTL change). Stage 1 (decides K):
g1 = A142's regression rows z104, R_dv4.8_s4_L100, R_dv4.8_s5_L100, Q_dv6.4_s4 (step at 295 us) at K 4 / 16 / 64
(the K 1024 records are A142's); g2 = a rising step inside the shortened window, R_dv4.8_s4_L100 with the step at
146 / 160 us, +4.8 / +6.4 V over 4 us, end = step + 150 us, at K 1024 / 4 / 16 / 64; g3 = the handover rows n0, m1n,
m3n at L x 0.7 / 1.0 / 1.3 (A137's rows) at K 1024 / 4 / 16 / 64. Stage 2 K (the chosen K): g4 = A129's other 13
matrix rows at L x 1.0 plus s_p62, l_p48_1us, l_p48_5us at L x 0.7 / 1.3, at K 1024 and K; g5 = C12's four-module
n0, m3n, s_p62, l_p48_1us at K (the K 1024 records are C12's). Writes cosim/cfg_*.json and cosim/ORDER_<stage>.txt.
Usage: make_cfgs.py 1 | make_cfgs.py 2 K"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
spec = importlib.util.spec_from_file_location("a136_cfgs", TA / "A136_p24_relative_cap_lowpass" / "make_cfgs.py")
A136 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A136)
A142C = TA / "A142_p24_random_stimulus" / "cosim"
C12C = TA.parent / "track_C_multi_module" / "C12_floor_late_four_modules" / "cosim"
KS = (4, 16, 64)
G1_ROWS = ("z104", "R_dv4.8_s4_L100", "R_dv4.8_s5_L100", "Q_dv6.4_s4")
G3_ROWS = ("n0", "m1n", "m3n")
MATRIX = A136.A135.STEP_ROWS + A136.A135.MATRIX_ROWS
G4 = [(1.0, r) for r in MATRIX if r not in G3_ROWS] + [(m, r) for m in (0.7, 1.3) for r in ("s_p62", "l_p48_1us", "l_p48_5us")]
G5_ROWS = ("n0", "m3n", "s_p62", "l_p48_1us")


def adopted(m, row):
    """A141 arm F on A137's row: A136 q + vff seed 2 + floor_late 1."""
    _, c = A136.cfg(m, row)
    c["vff"] = dict(c["vff"], seed=2)
    c["floor_late"] = 1
    return c


def put(c, name, note, k, order):
    c = dict(c, lo_learn=k, out=f"run_{name}.json", note=f"A143 {name}: {note}, lo_learn {k}")
    (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    order.append(name)


def stage1(order):
    for row in G1_ROWS:
        base = json.loads((A142C / f"cfg_{row}.json").read_text())
        for k in KS:
            put(base, f"g1_{row}_k{k}", f"A142 {row}", k, order)
    base = json.loads((A142C / "cfg_R_dv4.8_s4_L100.json").read_text())
    for t in (146.0, 160.0):
        for dv in (4.8, 6.4):
            c = dict(base, line_step={"t_us": t, "dv": dv, "slew_us": 4.0}, t_end_us=t + 150.0)
            for k in (1024,) + KS:
                put(c, f"g2_t{t:.0f}_dv{dv}_k{k}", f"A142 R nominal, +{dv} V / 4 us at {t:.0f} us", k, order)
    for m in (0.7, 1.0, 1.3):
        for row in G3_ROWS:
            for k in (1024,) + KS:
                put(adopted(m, row), f"g3_s{round(m * 100):03d}_{row}_k{k}", f"A141 F on A137 s{round(m * 100):03d}_{row}",
                    k, order)


def stage2(order, k):
    for m, row in G4:
        for kk in (1024, k):
            put(adopted(m, row), f"g4_s{round(m * 100):03d}_{row}_k{kk}", f"A141 F on A129 {row} at L x {m:g}", kk, order)
    for row in G5_ROWS:
        put(json.loads((C12C / f"cfg_{row}.json").read_text()), f"g5_{row}_k{k}", f"C12 {row}", k, order)


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "1"
    COS.mkdir(exist_ok=True)
    order = []
    if stage == "1":
        stage1(order)
    else:
        stage2(order, int(sys.argv[2]))
    # identity: K 1024 on A141's F_s100_l_p48_1us / I1_s100_n0 rows must equal those cfgs (note / out / lo_learn aside)
    a141 = TA / "A141_p24_floor_late_report" / "cosim"
    skip = ("note", "out")
    for row, ref in (("l_p48_1us", "cfg_F_s100_l_p48_1us.json"), ("n0", "cfg_I1_s100_n0.json")):
        a, b = adopted(1.0, row), json.loads((a141 / ref).read_text())
        diff = [x for x in set(a) | set(b) if x not in skip and a.get(x) != b.get(x)]
        assert not diff, (row, diff)
    first = sorted(order, key=lambda n: (not n.startswith("g5"), not n.startswith(("g3", "g4")), n))
    (COS / f"ORDER_{stage}.txt").write_text("\n".join(first) + "\n")
    print(len(order), "cfgs, stage", stage)


if __name__ == "__main__":
    main()
