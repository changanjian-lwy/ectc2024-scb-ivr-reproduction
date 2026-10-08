"""A174 cosim cfgs: the final plant's two marginal rows at four more step positions, and the fixed-reference interlock
delay on the rows where the interlock acted in A173.
- Step position (A129: moving a step by less than a period moves the post-step peak 2-7 A): L x 0.7 +4.8 V / 1 us
  (A172, 199.7 A) and ff -8 V / 10 us (A173, one NEW spike) with the step moved by k T / 5, k = 1..4 (T = the steady
  period before the step: 364.1 / 510.1 ns).
- Fixed 1.0 V interlock reference (A173 il8p3 BOUNDARY: t_il = comparator 0.5 ns + the complement's gate falling to
  1.0 V + the held gate charging back to its own channel start; ss 8.3, nom 2.0, ff 1.0 ns) on A173's rows with
  holds > 0. Rows without holds do not use t_il (bit-identical).
Writes cosim/cfg_*.json, cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A2 = HERE.parent / "A172_p24_final_gate_plant" / "cosim"
A3 = HERE.parent / "A173_p24_final_plant_coverage" / "cosim"
SHIFT = {"nom_L07_l_p48_1us": (A2, 0.3641), "ff_l_m80_10us": (A3, 0.5101)}     # base dir, period (us)
FIXED_REF = {"ss": 8.3, "nom": 2.0, "ff": 1.0}
IL_ROWS = ("m4_ss_l_p48_1us", "ss_s_p62", "ss_l_m80_10us", "ss_slew4", "ff_l_m80_10us")   # A173 holds > 0 (ss l_p48 / L x 0.7: A173)


def main():
    COS.mkdir(exist_ok=True)
    out = {}
    for row in IL_ROWS:
        base = json.loads((A3 / f"cfg_{row}.json").read_text())
        til = next(v for c, v in FIXED_REF.items() if row.startswith(c + "_") or f"_{c}_" in row)
        name = f"fr_{row}"
        out[name] = dict(base, gate=dict(base["gate"], t_il_ns=til), out=f"run_{name}.json",
                         note=f"A174 {name}: {row} on the final plant, fixed-reference interlock t_il {til} ns")
    for row, (d, per) in SHIFT.items():
        base = json.loads((d / f"cfg_{row}.json").read_text())
        key = "line_step" if "line_step" in base else "load_step"
        for k in range(1, 5):
            t = round(base[key]["t_us"] + k * per / 5, 4)
            name = f"sh{k}_{row}"
            out[name] = dict(base, **{key: dict(base[key], t_us=t)}, out=f"run_{name}.json",
                             note=f"A174 {name}: {row} on the final plant, step at {t} us ({k} T / 5 later)")
    for name, c in out.items():
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(out) + "\n")
    print(len(out), "cfgs")


if __name__ == "__main__":
    main()
