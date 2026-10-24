"""A245 cfgs (BOUNDARY Section 1). Stage 1: the start-ups of item 6c, each from its A230 / A231 / A239 cfg, in two arms:
f = the final configuration (+ A244's early_hold_a / late_hold_a 0.0, hold_wait 32), r = f + "rev_n" REV_N. Stage 2
(identity): A244's records with the longest runs of reverse-conduction reports (phases 2-4: 6; phase 1 of one / four
modules: 35 / 30, which the rule leaves), A244's cfg_w_ + rev_n, to equal A244's run_w_ bit for bit. FIRST: queue order.
  python3 make_cfgs.py"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
A230, A231, A239 = (TA / n / "cosim" for n in ("A230_p24_handover_slope_lead", "A231_p24_lead_per_corner",
                                                 "A239_p24_minimum_load"))
A244 = TA / "A244_p24_holds_after_handover" / "cosim"
HOLD_A, WAIT, REV_N = 0.0, 32, 16
STAGE1 = {"u_S75h_30": A230 / "cfg_u_S75h_30_base.json", "u_S75_30": A230 / "cfg_u_S75_30_base.json",
          "u_S75h_30_l": A230 / "cfg_u_S75h_30_lead.json", "u_S75_30_l": A230 / "cfg_u_S75_30_lead.json",
          "u5_N0": A239 / "cfg_u5_N0.json", "u5_N0h": A239 / "cfg_u5_N0h.json",
          "u5_N75": A239 / "cfg_u5_N75.json", "u5_N75h": A239 / "cfg_u5_N75h.json",
          "u_N0_10": A230 / "cfg_u_N0_10_base.json", "u_N0_20": A231 / "cfg_u_N0_20_base.json",
          "u_N0_30": A230 / "cfg_u_N0_30_base.json", "u_N0h_30": A231 / "cfg_u_N0h_30_base.json",
          "u_N75_20": A231 / "cfg_u_N75_20_base.json", "u_N75_30": A230 / "cfg_u_N75_30_base.json",
          "u_N75h_30": A231 / "cfg_u_N75h_30_base.json",
          "u_N0_100": A230 / "cfg_u_N0_100_base.json", "u_N0h_100": A231 / "cfg_u_N0h_100_base.json",
          "u_N75h_100": A231 / "cfg_u_N75h_100_base.json", "u_S75_100": A230 / "cfg_u_S75_100_base.json",
          "u_S75h_100": A230 / "cfg_u_S75h_100_base.json"}
FIRST = ("m4_l_m80_10us", "u5_N0", "u5_N0h", "u5_N75", "u5_N75h", "u_S75_30", "u_S75_30_l", "u_S75h_30", "u_S75h_30_l")
LEAD = ("u_S75h_30_l", "u_S75_30_l")        # A230's lead arm: the same start, handed over 0.6 us earlier (history)
STAGE2 = ("p_N0_10k", "p_N0_100k", "p_N0_30k", "r_F0_lm80", "m4_l_m80_10us")   # phases 2-4: 6 in a row; phase 1: 35 / 30


def main():
    for row, path in STAGE1.items():
        c = json.loads(path.read_text())
        f = dict(c, early_hold_a=HOLD_A, late_hold_a=HOLD_A, hold_wait=WAIT, out=f"run_f_{row}.json",
                 note=f"A245 arm f: {path.parent.parent.name} {path.stem[4:]} + A244's holds (wait {WAIT})")
        r = dict(f, rev_n=REV_N, out=f"run_r_{row}.json", note=f["note"] + f" + rev_n {REV_N}")
        (COS / f"cfg_f_{row}.json").write_text(json.dumps(f, indent=1) + "\n")
        (COS / f"cfg_r_{row}.json").write_text(json.dumps(r, indent=1) + "\n")
    for row in STAGE2:
        c = json.loads((A244 / f"cfg_w_{row}.json").read_text())
        i = dict(c, rev_n=REV_N, out=f"run_i_{row}.json", note=f"A245 identity: A244 w_{row} + rev_n {REV_N}")
        (COS / f"cfg_i_{row}.json").write_text(json.dumps(i, indent=1) + "\n")
    print(len(list(COS.glob("cfg_*.json"))), "cfgs")


if __name__ == "__main__":
    main()
