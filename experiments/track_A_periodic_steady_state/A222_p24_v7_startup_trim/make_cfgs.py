"""A222 cosim cfgs: plant V7 (A221's r_core) with mode S's trim moved by A206's rule (Vo half a microsecond before the
handover against V6's record, divided by 53.5 mV per ns, in whole 31.25 ps steps): N0 +1 step (23.4375 ns), N75
+2 steps (23.46875 ns); S75 unchanged (its handover is requested by Vo; A221: +0.58 mV).
- k_n_s_p62: A221's k row (A215's +62.5 A on N0) with N0's new trim, the whole run (k1 again);
- s_N75_25, s_S75_25: A215's 25 C binding rows of N75 and S75 on V7 to 200 us (the start-up only), N75 retrimmed.
  python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
LSB_NS = 0.03125
TRIM = {"N0": 750 * LSB_NS, "N75": 751 * LSB_NS}          # was 749 / 749 steps (23.4 / 23.411 ns)
T_END_S = 200.0


def row(src_dir, src, name, trim=None, t_end=None):
    c = json.loads((TA / src_dir / "cosim" / f"cfg_{src}.json").read_text())
    if "r_core" not in c["circuit"]:
        c["circuit"] = dict(c["circuit"], r_core=json.loads((TA / "A221_p24_core_loss_and_pause" / "cosim" /
                                                              "cfg_k_B_S75_hot_p5_ls0p3.json").read_text())["circuit"]["r_core"])
    if trim is not None:
        c["ton_s_ns"] = trim
    if t_end is not None:
        c["t_end_us"] = t_end
        c.pop("line_step", None)
    c["out"] = f"run_{name}.json"
    c["note"] = f"A222 {name}: {src_dir.split('_')[0]} {src} on plant V7, ton_s_ns {c['ton_s_ns']}" + (f", to {t_end:g} us" if t_end else "")
    return name, c


ROWS = [row("A221_p24_core_loss_and_pause", "k_n_s_p62", "k_n_s_p62", TRIM["N0"]),
        row("A215_p24_buildable_ton_path", "m16_B_N75_25_p4_ls0p3", "s_N75_25", TRIM["N75"], T_END_S),
        row("A215_p24_buildable_ton_path", "m16_B_S75_25_p4_ls0p3", "s_S75_25", None, T_END_S)]

if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    for name, c in ROWS:
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(n for n, _ in ROWS) + "\n")
    print({n: (c["ton_s_ns"], c["t_end_us"], c["circuit"]) for n, c in ROWS})
