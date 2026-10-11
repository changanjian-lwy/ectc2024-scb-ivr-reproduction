"""A196 cosim cfgs: the slow boards' corrector setting found by A195 (early step 0.0625 ns, late gain 1/4) on the slow
corner's binding row. Board S75 (slow devices, L x 0.75), +4.8 V / 1 us at 500 us + k T / 3, k = 0, 1, 2, at 0 C
(A193's cfg: cold trim, lead 9.5 ns) and 25 C (A192's cfg). Only dt_step_ns and err_shift differ from those cfgs.
  python3 make_cfgs.py   cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
REF = {"c0": TA / "A193_p24_slow_lead_cold" / "cosim" / "cfg_S75_c0_l9p5_p{k}.json",
       "25": TA / "A192_p24_slow_lead_rows" / "cosim" / "cfg_S75_25_p48_1us_p{k}.json"}
SET = {"dt_step_ns": 0.0625, "err_shift": 2}
COS = HERE / "cosim"


def main():
    names = []
    for temp, pat in REF.items():
        for k in (0, 1, 2):
            ref = json.loads(Path(str(pat).format(k=k)).read_text())
            assert (ref["dt_step_ns"], ref["err_shift"], ref["driver"]["hs_on_lead_ns"]) == (0.282843, 1, 9.5)
            name = f"S75_{temp}_p{k}"
            c = dict(ref, **SET, out=f"run_{name}.json",
                     note=f"A196 {name}: {ref['note'].split(': ', 1)[1]}; corrector step 0.0625 ns, err_shift 2")
            assert {x for x in c if c[x] != ref[x]} == {"dt_step_ns", "err_shift", "out", "note"}
            (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            names.append(f"cfg_{name}.json")
    (COS / "ORDER.txt").write_text("\n".join(names) + "\n")
    print(len(names), "cfgs")


if __name__ == "__main__":
    main()
