"""A257 cfgs (BOUNDARY Section 1): two N13 rows built on A246's cfg_h_r_N13_lm48 (the final configuration on 3.813 nH):
o125_N13 = k_N0's construction (no line step, skip or hand lead; +62.5 A at 500 us, end 620 us) and lp48_N13 = the same
cfg with a +4.8 V / 1 us line step. Arms: h = the final configuration, s = + the adopted limit (140 A on 3.813 nH,
t_ns 1, n_susp 6).
  python3 make_cfgs.py -> cosim/cfg_{h,s}_{o125,lp48}_N13.json"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A46 = HERE.parent / "A246_p24_held_report_floor" / "cosim"
OCP = {"i_a": 140.0, "t_ns": 1.0, "n_susp": 6}


def rows():
    base = json.loads((A46 / "cfg_h_r_N13_lm48.json").read_text())
    o = {k: v for k, v in base.items() if k not in ("line_step", "skip", "hand_lead_us")}
    o |= {"load_step": {"i_a": 62.5, "t_us": 500.0}, "t_end_us": 620.0}
    lp = base | {"line_step": dict(base["line_step"], dv=4.8)}
    return {"o125_N13": o, "lp48_N13": lp}


def main():
    (HERE / "cosim").mkdir(exist_ok=True)
    for row, c in rows().items():
        for arm, extra in (("h", {}), ("s", {"ocp": OCP})):
            d = c | extra
            d.update(out=f"run_{arm}_{row}.json", note=f"A257 arm {arm}: A246 cfg_h_r_N13_lm48 as {row}"
                     + (f" + ocp {OCP}" if extra else ""))
            (HERE / "cosim" / f"cfg_{arm}_{row}.json").write_text(json.dumps(d, indent=1) + "\n")
    print("4 cfgs")


if __name__ == "__main__":
    main()
