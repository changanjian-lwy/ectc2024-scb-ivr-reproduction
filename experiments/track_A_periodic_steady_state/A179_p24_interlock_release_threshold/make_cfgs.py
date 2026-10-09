"""A179 cosim cfgs: the interlock release time between 0.5 and 1.4 ns at the slow corner, with the step-position
scatter measured at each release time.
- Rows: A173's cfgs of ss l_m80_10us (R1), ss s_p62 (R2) and four modules ss l_p48_1us (M4), final plant (V5).
- Only the step time and the run end change: step at 500 us + k T / 3 (k = 0, 1, 2; four modules k = 0 and T / 2),
  end = step + 400 us (A173: step 1000 / 800 us, end + 400 us). T = the steady period before the step in A173's
  records (450-990 us): 0.5048 us single, 0.5069 us four modules. Before the step every run equals A173's.
- t_il: R1 0.5 / 0.8 / 1.0 / 1.4 ns, R2 and M4 0.5 / 1.4 ns.
Writes cosim/cfg_*.json, cosim/ORDER.txt (four-module runs first: the longest)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A3 = HERE.parent / "A173_p24_final_plant_coverage" / "cosim"
T_STEP0 = 500.0                                     # us
POST_US = 400.0                                     # run end after the step (as A173)
PERIOD = {"single": 0.5048, "m4": 0.5069}           # us, A173 ss records 450-990 us
ROWS = {"m4_ss_l_p48_1us": ((0.5, 1.4), (0.0, 0.5)),            # row: (t_il ns, step offsets in periods)
        "ss_l_m80_10us": ((0.5, 0.8, 1.0, 1.4), (0.0, 1 / 3, 2 / 3)),
        "ss_s_p62": ((0.5, 1.4), (0.0, 1 / 3, 2 / 3))}


def til_tag(t):
    return f"t{int(round(t * 10)):02d}"


def main():
    COS.mkdir(exist_ok=True)
    out = {}
    for row, (tils, offs) in ROWS.items():
        base = json.loads((A3 / f"cfg_{row}.json").read_text())
        key = "line_step" if "line_step" in base else "load_step"
        per = PERIOD["m4" if row.startswith("m4") else "single"]
        for k, f in enumerate(offs):
            t = round(T_STEP0 + f * per, 4)
            for til in tils:
                name = f"{til_tag(til)}_p{k}_{row}"
                out[name] = dict(base, **{key: dict(base[key], t_us=t)}, t_end_us=round(t + POST_US, 4),
                                 gate=dict(base["gate"], t_il_ns=til), out=f"run_{name}.json",
                                 note=f"A179 {name}: {row} on the final plant, t_il {til} ns, step at {t} us "
                                      f"(500 us + {f:.3f} T), end + {POST_US:.0f} us")
    for name, c in out.items():
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(out) + "\n")
    print(len(out), "cfgs")


if __name__ == "__main__":
    main()
