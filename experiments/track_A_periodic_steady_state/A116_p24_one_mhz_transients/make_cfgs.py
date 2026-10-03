"""A116 configurations: A115's 1 MHz 10% design (cosim/cfg_n10.json and its step rows) against its load-decrease
runaway, with two remedies and their combination (one factor: the controller variant):
- t60: A115 as is (timed phase-1 turn-off, D59 loop at 60 kHz); only the line-step rows, which A115 did not run;
- t30: the loop at 30 kHz (D59 at A115's 5% point, as the 60 kHz gains);
- c60: the comparator-decided phase-1 turn-off (A105's I1, cfg lo_pred = 0; A113's cmp);
- c30: both.
Rows: n0, the -/+62.5 A load steps, the +/-4.8 V input steps over 1 us (A106's l_p48_1us / l_m48_1us at 2000 us).
Writes cosim/cfg_<variant>_<row>.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A115 = HERE.parent / "A115_p24_one_mhz_design_point" / "cosim"
T_STEP_US, T_END_US = 2000.0, 3000.0
FC30 = {"kp_ns_per_v": 287.23, "ki_ns_per_v": 11.9816}       # a116_predictions.json, D59 at 30 kHz
VARIANTS = {"t60": {}, "t30": FC30, "c60": {"lo_pred": 0}, "c30": {"lo_pred": 0, **FC30}}
ROWS = {"s_m62": "n10_s_m62", "n0": "n10", "s_p62": "n10_s_p62",
        "l_p48_1us": ("n10", 4.8), "l_m48_1us": ("n10", -4.8)}


def base(src):
    if isinstance(src, tuple):
        name, dv = src
        c = json.loads((A115 / f"cfg_{name}.json").read_text())
        c["line_step"] = {"t_us": T_STEP_US, "dv": dv, "slew_us": 1.0}
        c["t_end_us"] = T_END_US
        return c
    return json.loads((A115 / f"cfg_{src}.json").read_text())


if __name__ == "__main__":
    names = []
    for row, src in ROWS.items():                      # the decisive rows first: the load decrease
        for v, change in VARIANTS.items():
            if v == "t60" and not row.startswith("l_"):
                continue
            c = base(src)
            c.update(change)
            c["note"] = f"A116 {v}_{row}: A115's 1 MHz 10% design ({src}) with {change or 'no change'}."
            c["out"] = f"run_{v}_{row}.json"
            (HERE / "cosim" / f"cfg_{v}_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
            names.append(f"{v}_{row}")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(names) + "\n")
    print(len(names), "configurations:", ", ".join(names))
