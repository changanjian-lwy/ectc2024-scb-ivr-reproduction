"""A134 configurations: the adopted 2.5 MHz design (A129's g125: A124 with the gated Vin feed-forward) with the phase
inductance L x m and the feed-forward's phase-1 cap constant vff.k per arm - f: as adopted (L0 x 180 A), z: 0 (no cap,
the falling term kept), c: k x m (the cap calibrated to the part's L). Plan: T (tolerance) f at m 0.85 / 0.9 / 1.05 /
1.1 on A124's seven step rows + n0 and A129's matrix, f at m 0.7 on the matrix (its step rows are A133's fl07); M
(mechanism) z and c at m 1.1 / 1.2 / 1.3 on n0, s_p62, l_p48_5us, l_p48_1us. Writes cosim/cfg_<arm>l<mmm>_<row>.json
and cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
A129 = PROJECT / "extensions/ml_design_assist/experiments/A129_cosim_vff_slope_gate/cosim"
STEP_ROWS = ("l_p48_5us", "l_p48_1us", "l_m48_1us", "l_m48_5us", "l_m80_10us", "s_p62", "s_m62", "n0")
MATRIX_ROWS = ("m1n", "m1p", "m3n", "m3p", "j30", "j100", "s_m25", "s_p25")
M_ROWS = ("n0", "s_p62", "l_p48_5us", "l_p48_1us")
PLAN = [("f", m, STEP_ROWS + MATRIX_ROWS) for m in (0.85, 0.9, 1.05, 1.1)] + [("f", 0.7, MATRIX_ROWS)] + \
       [(arm, m, M_ROWS) for arm in ("z", "c") for m in (1.1, 1.2, 1.3)]


def name(arm, m, row):
    return f"{arm}l{round(m * 100):03d}_{row}"


def cfg(arm, m, row):
    c = json.loads((A129 / f"cfg_g125_{row}.json").read_text())
    c["circuit"] = dict(c["circuit"], L=c["circuit"]["L"] * m)
    k0 = c["vff"]["k"]
    c["vff"] = dict(c["vff"], k={"f": k0, "z": 0, "c": round(k0 * m)}[arm])
    n = name(arm, m, row)
    c["note"] = f"A134 {n}: A129's g125_{row} at k_L {m:g}, vff.k {c['vff']['k']}"
    c["out"] = f"run_{n}.json"
    return n, c


def main():
    order = []
    for arm, m, rows in PLAN:
        for row in rows:
            n, c = cfg(arm, m, row)
            (HERE / "cosim").mkdir(exist_ok=True)
            (HERE / "cosim" / f"cfg_{n}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(n)
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
