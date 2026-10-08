"""A173 cosim cfgs: the final gate-level plant (A172: A167's drive, every switch gate-driven, threshold interlock) on
the rows that ran only with ideal low sides and no interlock (A164 / A167), on three four-module cases, and with the
interlock's release delay set to two realisable comparator forms.
Plant additions to an A164 cfg (as A171 / A172): driver lead_ramp_us 20; gate switches "all", interlock "threshold",
t_il_ns. Trims: A164's per board (A171: Vo(143.5 us) 1.029-1.032 V under this plant on nom / ff / hot / ss); L x 0.7
A172's 35.769 ns; L x 1.3 measured under this plant (stage 1, one shot as A164).
  python3 make_cfgs.py cal   stage 1: cosim_cal/cfg_nom_L13.json, start-up to 150 us at A164's L x 1.3 trim
  python3 make_cfgs.py       stage 2: cosim/cfg_*.json, cosim/ORDER.txt; the L x 1.3 row and trims.json once stage 1
                             has run"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COS, CAL = HERE / "cosim", HERE / "cosim_cal"
TA = HERE.parent
A4 = TA / "A164_p24_gate_drive_spread"
A1 = TA / "A171_p24_gate_interlock_threshold" / "cosim"
A2 = TA / "A172_p24_final_gate_plant" / "cosim"
C14 = TA.parent / "track_C_multi_module" / "C14_sharing_spread_check" / "cosim"
_spec = importlib.util.spec_from_file_location("a164_make_cfgs", A4 / "make_cfgs.py")
MC4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MC4)

T_IL, TON_L07, LEAD = 0.5, 35.769, 8.0
# A164's matrix rows not yet run on the final plant (A171 / A172 ran l_p48_1us at nom / ff / hot / ss / L x 0.7, m4 nom)
COVER = ("nom_s_p62", "nom_l_m80_10us", "nom_slew4", "ff_s_p62", "ff_l_m80_10us", "hot_s_p62", "ss_s_p62",
         "ss_l_m80_10us", "ss_slew4")
# comparator forms (t_il = comparator 0.5 ns + complement's gate falling from its channel-off level to the reference
# + the held gate charging from the reference to its own channel start; EPC model, D79 resistances):
# reference per board (V_th - 0.2 V) 0.95-1.36 ns at any corner; fixed 1.0 V: nom 2.04, ss 8.29 ns
COMPARATOR = {"il1p4_ss_l_p48_1us": ("ss_l_p48_1us", 1.4), "il8p3_ss_l_p48_1us": ("ss_l_p48_1us", 8.3),
              "il2p0_nom_L07_l_p48_1us": ("nom_L07_l_p48_1us", 2.0)}


def final(cfg, t_il=T_IL):
    return dict(cfg, driver=dict(cfg["driver"], lead_ramp_us=20.0),
                gate=dict(cfg["gate"], switches="all", interlock="threshold", t_il_ns=t_il))


def a164(name):
    return json.loads((A4 / "cosim" / f"cfg_{name}.json").read_text())


def strip(c):
    return {k: v for k, v in c.items() if k not in ("out", "note")}


def check_identity():
    """The construction reproduces A171's S50 and A172's cfgs key for key (out / note aside)."""
    for row in ("nom_l_p48_1us", "ff_l_p48_1us", "hot_l_p48_1us", "ss_l_p48_1us", "nom_L07_l_p48_1us"):
        assert strip(final(a164(row))) == strip(json.loads((A1 / f"cfg_S50_{row}.json").read_text())), row
    assert strip(final(dict(a164("nom_L07_l_p48_1us"), ton_ns=TON_L07))) == strip(
        json.loads((A2 / "cfg_nom_L07_l_p48_1us.json").read_text()))
    assert strip(final(a164("m4_nom_l_p48_1us"))) == strip(json.loads((A2 / "cfg_m4_nom_l_p48_1us.json").read_text()))
    tr = json.loads((A4 / "trims.json").read_text())
    assert strip(MC4.gate_cfg(MC4.MC.row_cfg("L07_l_p48_1us"), "nom", tr["nom_L07"]["ton_ns"], LEAD)) == strip(
        a164("nom_L07_l_p48_1us"))


def cal():
    CAL.mkdir(exist_ok=True)
    c = final(a164("nom_L13_l_p48_1us"))
    c = dict(c, t_end_us=150.0, out="run_nom_L13.json",
             note=f"A173 stage 1: board nom_L13 start-up under the final plant at A164's trim {c['ton_ns']} ns")
    (CAL / "cfg_nom_L13.json").write_text(json.dumps(c, indent=1) + "\n")
    print("cal cfg written")


def main():
    check_identity()
    COS.mkdir(exist_ok=True)
    tr = json.loads((A4 / "trims.json").read_text())
    out = {}

    def put(name, cfg, note):
        out[name] = dict(cfg, out=f"run_{name}.json", note=f"A173 {name}: {note}")

    m4l = json.loads((MC4.M.A143C / "cfg_g5_l_p48_1us_k4.json").read_text())
    m4s = json.loads((MC4.M.A143C / "cfg_g5_s_p62_k4.json").read_text())
    put("m4_ss_l_p48_1us", final(MC4.gate_cfg(m4l, "ss", tr["ss_L0"]["ton_ns"], LEAD)),
        "four modules, slow corner, A164's ss trim, final plant")
    put("m4_nom_s_p62", final(MC4.gate_cfg(m4s, "nom", tr["nom_L0"]["ton_ns"], LEAD)),
        "four modules, +62.5 A load step, final plant")
    w5 = json.loads((C14 / "cfg_w5_l_p48_1us.json").read_text())["module_circuit"]
    put("m4_w5_l_p48_1us", dict(final(a164("m4_nom_l_p48_1us")), module_circuit=w5),
        "four modules, C14's w5 spread (module 2 L -5 %, others +5 %), final plant")
    for name, (row, til) in COMPARATOR.items():
        c = a164(row)
        if "L07" in row:
            c = dict(c, ton_ns=TON_L07)
        put(name, final(c, til), f"{row} on the final plant with interlock release t_il {til} ns")
    for row in COVER:
        put(row, final(a164(row)), "A164's row and trim on the final plant")
    put("nom_L07_s_p62", final(MC4.gate_cfg(MC4.MC.row_cfg("L07_s_p62"), "nom", TON_L07, LEAD)),
        f"L x 0.7 load step, A172's trim {TON_L07} ns, final plant")
    rc = CAL / "run_nom_L13.json"
    if rc.exists():
        r = json.loads(rc.read_text())
        ton0 = r["cfg"]["ton_ns"] if "cfg" in r and "ton_ns" in r["cfg"] else a164("nom_L13_l_p48_1us")["ton_ns"]
        vo = float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6]))
        ton = round(ton0 + (MC4.VO_TGT - vo) / MC4.SLOPE, 3)
        (HERE / "trims.json").write_text(json.dumps({"nom_L13": {"ton0_ns": ton0, "vo0": vo, "ton_ns": ton}}, indent=1)
                                         + "\n")
        put("nom_L13_l_p48_1us", final(dict(a164("nom_L13_l_p48_1us"), ton_ns=ton)),
            f"L x 1.3 board re-trimmed under the final plant ({ton0} -> {ton} ns)")
    else:
        print("stage 1 record missing: nom_L13_l_p48_1us not written")
    for name, c in out.items():
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(out) + "\n")
    print(len(out), "cfgs")


if __name__ == "__main__":
    cal() if sys.argv[1:] == ["cal"] else main()
