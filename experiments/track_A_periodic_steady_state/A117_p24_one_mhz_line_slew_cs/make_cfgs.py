"""A117 configurations: D63's design map at 1 MHz 10% put to the co-simulation, without an RTL change. Factors: the
input slew (+-4.8 V over 5-50 us; A116 ran 1 us), the series capacitor (15 uF, A115; 3 uF, the ladder 5x faster) and
phase 1's turn-off (cmp: A116 c60, lo_pred 0; tim: A115 n10, timed). The loop is D59's 60 kHz in every row.
Rows from A116's c60 / A115's n10 configurations; the line step at 2000 us, run to 3000 us. Writes cosim/cfg_*.json
and cosim/ORDER.txt (the predicted runaways first, then the decisive ones)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A115 = HERE.parent / "A115_p24_one_mhz_design_point" / "cosim"
A116 = HERE.parent / "A116_p24_one_mhz_transients" / "cosim"
SRC = {"cmp": A116 / "cfg_c60_n0.json", "tim": A115 / "cfg_n10.json"}
ROWS = {   # name: (cs uF, rule, line step dv or None, slew us, load step A or None)
    "c3_cmp_l_p48_5us": (3, "cmp", 4.8, 5, None), "c3_cmp_l_m48_1us": (3, "cmp", -4.8, 1, None),
    "c15_tim_l_m48_20us": (15, "tim", -4.8, 20, None), "c3_tim_l_m48_10us": (3, "tim", -4.8, 10, None),
    "c15_tim_l_m48_50us": (15, "tim", -4.8, 50, None),
    "c15_cmp_l_p48_20us": (15, "cmp", 4.8, 20, None), "c15_cmp_l_p48_50us": (15, "cmp", 4.8, 50, None),
    "c15_cmp_l_m48_5us": (15, "cmp", -4.8, 5, None), "c15_tim_l_p48_10us": (15, "tim", 4.8, 10, None),
    "c3_tim_l_p48_1us": (3, "tim", 4.8, 1, None), "c3_cmp_l_p48_20us": (3, "cmp", 4.8, 20, None),
    "c3_cmp_s_m62": (3, "cmp", None, None, -62.5),
    "c3_tim_n0": (3, "tim", None, None, None), "c3_cmp_n0": (3, "cmp", None, None, None),
}

if __name__ == "__main__":
    for name, (cs, rule, dv, slew, di) in ROWS.items():
        c = json.loads(SRC[rule].read_text())
        c["circuit"] = dict(c["circuit"], cs=cs * 1e-6)
        c.pop("line_step", None); c.pop("load_step", None)
        if dv is not None:
            c["line_step"] = {"t_us": 2000.0, "dv": dv, "slew_us": float(slew)}
            c["t_end_us"] = 3000.0
        elif di is not None:
            c["load_step"] = {"t_us": 2000.0, "i_a": di}
            c["t_end_us"] = 3000.0
        else:
            c["t_end_us"] = 2500.0
        c["note"] = f"A117 {name}: {SRC[rule].parent.parent.name}'s {SRC[rule].stem[4:]} with Cs {cs} uF" + (
            f", input {dv:+.1f} V over {slew} us at 2000 us" if dv is not None else f", load {di:+.1f} A at 2000 us" if di else "") + "."
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(ROWS) + "\n")
    print(len(ROWS), "configurations")
