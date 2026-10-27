"""A258 cfgs (BOUNDARY Section 1). The adopted limit (A256: ocp {110 A on 2.2 nH, t_ns 1, n_susp 6}) against the same
with the count capped (n_cap 6):
- pr_<board>: A246's p_<board>_1000k (A240's 1 MHz train from 300 us) after a 125 % overload, +62.5 A at 200 us taken
  back at 290 us (load_step + load_step2); arms s (adopted) and c (+ n_cap 6);
- ro_S75h: A246's p_S75h_100k with the train's high level at 312.5 A (125 %), the cap's own risk (re-arming under a
  repeated overload); arms s and c;
- A256's rows that suspended, arm c only (A256's cfg_s_<row> + n_cap 6): the four that re-armed (REARM) and the three
  one-module ones that stay suspended (HOLD; m4_s_p250 not run).
  python3 make_cfgs.py -> cosim/cfg_{s,c}_*.json"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A46 = HERE.parent / "A246_p24_held_report_floor" / "cosim"
A56 = HERE.parent / "A256_p24_limit_suspends_on_overload" / "cosim"
OCP = json.loads((A56 / "cfg_s_o125_N75.json").read_text())["ocp"]           # 110 A, t_ns 1, n_susp 6 (2.2 nH)
CAP = {"n_cap": 6}
PR = ("pr_N75", "pr_S75h")
RO = ("ro_S75h",)
REARM = ("k_S75h", "a_S75h_d2", "a_S75h_d20", "a_S75_d20")
HOLD = ("k_N0", "o125_N75", "o125_S75h")


def base(row):
    if row in PR:
        c = json.loads((A46 / f"cfg_h_p_{row[3:]}_1000k.json").read_text())
        return c | {"load_step": {"i_a": 62.5, "t_us": 200.0}, "load_step2": {"i_a": -62.5, "t_us": 290.0}, "ocp": OCP}
    if row in RO:
        c = json.loads((A46 / f"cfg_h_p_{row[3:]}_100k.json").read_text())
        return c | {"load_pulse": dict(c["load_pulse"], i_hi_a=312.5), "ocp": OCP}
    return json.loads((A56 / f"cfg_s_{row}.json").read_text())


def main():
    assert OCP == {"i_a": 110.0, "t_ns": 1.0, "n_susp": 6}, OCP
    (HERE / "cosim").mkdir(exist_ok=True)
    n = 0
    for row in PR + RO + REARM + HOLD:
        arms = ("s", "c") if row in PR + RO else ("c",)
        for arm in arms:
            c = base(row)
            if arm == "c":
                c["ocp"] = dict(c["ocp"]) | CAP
            c.update(out=f"run_{arm}_{row}.json", note=f"A258 arm {arm}: {row}, ocp {c['ocp']}")
            (HERE / "cosim" / f"cfg_{arm}_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
            n += 1
    print(n, "cfgs")


if __name__ == "__main__":
    main()
