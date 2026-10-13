"""A206 cosim cfgs: plant V6 = V5 with the three parts A205 found missing:
- gate "zvs_edge" 1: a turn-on at V_DS <= 0 is an edge (third-quadrant channel while its gate charges);
- gate "miller" 1: an off gate follows its drain's movement, so that edge starts from the gate's dipped level;
- "r_sw_mohm" [high side, low side] with circuit R = 0: the on-resistance sits in the switches.
and, as the design variable, gate "r_on_ls": the low sides' own turn-on resistance (3.0 = as specified so far).

Stage 1 (25 C, nominal devices; A205's three cfgs with their snapshot and edge-log windows):
  V_*  switches at the vendor model's typical R_DS(on) (what LTspice has): N0_steady / N0_step / N75_step at 3.0 ohm,
       N0_steady at 1.0 and 0.3 ohm - replayed in LTspice;
  E_*  switches at the datasheet maximum (the plant's design basis, D62): N0_steady at 3.0 / 1.0 / 0.3 ohm.
Stage 2 (after stage 1 chose r_on_ls; `python3 make_cfgs.py stage2 R`): +4.8 V / 1 us at 500 us + k T / 6 on the
  binding boards of V5 (a194 make_cfgs.board): N75 25 C (k 0, 2, 4), S75 0 C and 25 C (k 0, 2, 4), S75 125 C (k 1, 5),
  N0 25 C (k 0); switches at the datasheet maximum times the vendor model's temperature factor; end 80 us after the step.
  python3 make_cfgs.py            stage 1: cosim/cfg_*.json, cosim/ORDER.txt
  python3 make_cfgs.py stage2 R   stage 2 with r_on_ls = R: cosim/cfg_B_*.json, cosim/ORDER2.txt"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A205 = TA / "A205_p24_ltspice_replay" / "cosim"
COS = HERE / "cosim"
R_TYP = 1.2778e-3                 # ohm per device: p24_gate_model.load_device(temp=25).rds_on() (vendor model, 5 V)
R_MAX = 1.55e-3                   # ohm per device: EPC2067 datasheet maximum at 25 C (D62's basis for R = 0.54 mOhm)
R_TEMP = {-40.0: 0.6617, 0.0: 0.8676, 25.0: 1.0, 125.0: 1.5809}     # vendor model R_DS(on)(T) / R_DS(on)(25 C)
N_HIGH, N_LOW = 2, 3
PER0 = 0.5048                     # us, the nominal board's period (A194)
STAGE2 = (("N75", "25", (0, 2, 4)), ("S75", "c0", (0, 2, 4)), ("S75", "25", (0, 2, 4)), ("S75", "hot", (1, 5)),
          ("N0", "25", (0,)))


def r_sw(r_dev):
    return [round(r_dev / N_HIGH * 1e3, 6), round(r_dev / N_LOW * 1e3, 6)]


def v6(c, r_ls, r_dev):
    """cfg c on plant V6 with the low sides' turn-on resistance r_ls and r_dev ohm per conducting device."""
    return dict(c, gate=dict(c["gate"], zvs_edge=1, miller=1, r_on_ls=r_ls), circuit=dict(c["circuit"], R=0.0),
                r_sw_mohm=r_sw(r_dev))


def tag(r_ls):
    return "ls" + f"{r_ls:g}".replace(".", "p")


def stage1():
    COS.mkdir(exist_ok=True)
    order = []
    rows = [("V", b, 3.0, R_TYP) for b in ("N0_steady", "N0_step", "N75_step")] + \
           [("V", "N0_steady", r, R_TYP) for r in (1.0, 0.3)] + [("E", "N0_steady", r, R_MAX) for r in (3.0, 1.0, 0.3)]
    for kind, base, r_ls, r_dev in rows:
        c = json.loads((A205 / f"cfg_{base}.json").read_text())
        name = f"{kind}_{base}_{tag(r_ls)}"
        c = dict(v6(c, r_ls, r_dev), out=f"run_{name}.json",
                 note=f"A206 {name}: A205's {base} on plant V6 (zvs_edge, miller, r_sw {r_sw(r_dev)} mOhm "
                      f"{'typical' if kind == 'V' else 'datasheet maximum'}, R 0), low-side turn-on {r_ls:g} ohm")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "stage-1 cfgs; run-equivalents of 900 us:", round(sum(
        json.loads((COS / f"cfg_{n}.json").read_text())["t_end_us"] for n in order) / 900.0, 2))


def stage2(r_ls):
    spec = importlib.util.spec_from_file_location("a194_cfgs", TA / "A194_p24_final_plant_random_stimuli" / "make_cfgs.py")
    a194 = importlib.util.module_from_spec(spec); spec.loader.exec_module(a194)
    order = []
    for b, tk, ks in STAGE2:
        temp = a194.TEMPS[tk]
        per = PER0 * {"N75": 0.75, "S75": 0.75}.get(b, 1.0)
        for k in ks:
            t_us = round(500.0 + k * per / 6.0, 4)
            name = f"B_{b}_{tk}_p{k}_{tag(r_ls)}"
            c = v6(a194.board(b, tk), r_ls, R_MAX * R_TEMP[temp])
            c = dict(c, line_step={"dv": 4.8, "slew_us": 1.0, "t_us": t_us}, t_end_us=round(t_us + 81.0, 4),
                     out=f"run_{name}.json",
                     note=f"A206 {name}: board {b}, {temp:g} C, final configuration on plant V6 (r_sw "
                          f"{r_sw(R_MAX * R_TEMP[temp])} mOhm = datasheet maximum x {R_TEMP[temp]}, R 0), low-side "
                          f"turn-on {r_ls:g} ohm, +4.8 V / 1 us at {t_us} us")
            (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    (COS / "ORDER2.txt").write_text("\n".join(order) + "\n")
    print(len(order), "stage-2 cfgs; run-equivalents of 900 us:", round(sum(
        json.loads((COS / f"cfg_{n}.json").read_text())["t_end_us"] for n in order) / 900.0, 2))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stage2":
        stage2(float(sys.argv[2]))
    else:
        stage1()
