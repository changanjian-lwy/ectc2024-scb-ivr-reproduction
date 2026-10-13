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
  A board's r_on_ls is R times its own drive-resistance factor (gate r_on / 3.0: 1.2 on the slow boards).
Start-up (between the stages, BOUNDARY Sections 4-5): the stage-2 boards to 150 us on V6 with the V5 trims (T0_*; N0
  is stage 1's E run), then to 175 us with ton_s moved by trims.json (T1_*; N0 = the E run repeated,
  E_N0_steady_<ls>_t).
  trims.json {board_temp: ns} is written by a206_analyze.py trims; stage 2 applies it when it exists.
  python3 make_cfgs.py            stage 1: cosim/cfg_*.json, cosim/ORDER.txt
  python3 make_cfgs.py startup R  start-up runs with r_on_ls = R: cosim/cfg_T0_*.json or cfg_T1_*.json, ORDER_T.txt
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
TRIMS = HERE / "trims.json"
T_END = {"T0": 150.0, "T1": 175.0}        # us; T1 covers 25 us after the latest handover (the hot boards' own peak)


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


def _a194():
    spec = importlib.util.spec_from_file_location("a194_cfgs", TA / "A194_p24_final_plant_random_stimuli" / "make_cfgs.py")
    a194 = importlib.util.module_from_spec(spec); spec.loader.exec_module(a194)
    return a194


def board_v6(a194, b, tk, r_ls, trims):
    """The board's final-configuration cfg on V6 (no stimulus), its ton_s raised by trims[b_tk] ns."""
    c = a194.board(b, tk)
    r_b = round(r_ls * c["gate"]["r_on"] / 3.0, 4)              # the board's drive-resistance corner
    c = v6(c, r_b, R_MAX * R_TEMP[a194.TEMPS[tk]])
    d = (trims or {}).get(f"{b}_{tk}", 0.0)
    if d:
        c["ton_s_ns"] = round(c["ton_s_ns"] + d, 3)
    return c, r_b, d


def startup(r_ls):
    a194 = _a194()
    trims = json.loads(TRIMS.read_text())["dton_s_ns"] if TRIMS.exists() else None
    pre, order = ("T1" if trims else "T0"), []
    for b, tk in sorted({(b, tk) for b, tk, _ in STAGE2}):
        if trims and not trims.get(f"{b}_{tk}", 0.0):
            continue                                             # no trim change: its T0 (or E) run stands
        if b == "N0":
            if not trims:
                continue                                         # T0 of N0 = stage 1's E run
            c = json.loads((COS / f"cfg_E_N0_steady_{tag(r_ls)}.json").read_text())
            d = trims.get("N0_25", 0.0)
            name = f"E_N0_steady_{tag(r_ls)}_t"
            c = dict(c, ton_s_ns=round(c["ton_s_ns"] + d, 3), out=f"run_{name}.json",
                     note=c["note"] + f"; ton_s moved by {d:+g} ns (trims.json)")
        else:
            c, r_b, d = board_v6(a194, b, tk, r_ls, trims)
            name = f"{pre}_{b}_{tk}_{tag(r_ls)}"
            c = dict(c, t_end_us=T_END[pre], out=f"run_{name}.json",
                     note=f"A206 {name}: board {b}, {a194.TEMPS[tk]:g} C, final configuration on plant V6, low-side "
                          f"turn-on {r_b:g} ohm, start-up to {T_END[pre]:g} us, ton_s {c['ton_s_ns']} ns (V5 trim {d:+g} ns)")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (COS / f"ORDER_{pre}.txt").write_text("\n".join(order) + "\n")
    print(len(order), pre, "cfgs:", " ".join(order))


def stage2(r_ls):
    a194 = _a194()
    trims = json.loads(TRIMS.read_text())["dton_s_ns"] if TRIMS.exists() else None
    order = []
    for b, tk, ks in STAGE2:
        temp = a194.TEMPS[tk]
        per = PER0 * {"N75": 0.75, "S75": 0.75}.get(b, 1.0)
        for k in ks:
            t_us = round(500.0 + k * per / 6.0, 4)
            name = f"B_{b}_{tk}_p{k}_{tag(r_ls)}"
            c, r_b, d = board_v6(a194, b, tk, r_ls, trims)
            c = dict(c, line_step={"dv": 4.8, "slew_us": 1.0, "t_us": t_us}, t_end_us=round(t_us + 81.0, 4),
                     out=f"run_{name}.json",
                     note=f"A206 {name}: board {b}, {temp:g} C, final configuration on plant V6 (r_sw "
                          f"{r_sw(R_MAX * R_TEMP[temp])} mOhm = datasheet maximum x {R_TEMP[temp]}, R 0), low-side "
                          f"turn-on {r_b:g} ohm, ton_s {c['ton_s_ns']} ns (V5 trim {d:+g} ns), "
                          f"+4.8 V / 1 us at {t_us} us")
            (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    (COS / "ORDER2.txt").write_text("\n".join(order) + "\n")
    print(len(order), "stage-2 cfgs; run-equivalents of 900 us:", round(sum(
        json.loads((COS / f"cfg_{n}.json").read_text())["t_end_us"] for n in order) / 900.0, 2))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stage2":
        stage2(float(sys.argv[2]))
    elif len(sys.argv) > 1 and sys.argv[1] == "startup":
        startup(float(sys.argv[2]))
    else:
        stage1()
