"""A244 control cfgs (BOUNDARY Section 4): every stage-2 row that missed g5 or g6 in a244_summary.json, moved by k T / 6
(k 2 and 4) with A243's rule (make_ctrl_cfgs.moved / period_us). Arm w = the row's A244 cfg moved; arm r = the
reference cfg moved, written only where A243 has no run_cr_ record for it. Rows of A232's step families (f_N75_k0 / k2
/ k4, f_N0_k0 / k4) are positions themselves: no runs, the family is compared as A243 did for f_N75.
  python3 make_ctrl_cfgs.py   (after a244_analyze.py)"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
C43 = HERE.parent / "A243_p24_hold_without_reversal"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a244_make_cfgs", HERE / "make_cfgs.py")
M43 = _load("a243_make_ctrl_cfgs", C43 / "make_ctrl_cfgs.py")
KS = M43.KS


def missed():
    d = json.loads((HERE / "a244_summary.json").read_text())["stage2"]
    return [r for r, x in d.items() if x and not (x["criteria"].get("g5", True) and x["criteria"].get("g6", True))]


def family(row):
    """A232's step family a row belongs to (f_N75 / f_N0), else None."""
    return row.rsplit("_", 1)[0] if row.startswith("f_") and row.rsplit("_", 1)[1] in ("k0", "k2", "k4") else None


def main():
    rows = [r for r in missed() if not family(r)]
    for row in rows:
        c, t = json.loads(MC.src(row).read_text()), M43.period_us(row)
        for k in KS:
            m = M43.moved(c, k * t / 6)
            w = dict(m, out=f"run_cw_{row}_k{k}.json", early_hold_a=MC.HOLD_A, late_hold_a=MC.HOLD_A, hold_wait=MC.WAIT,
                     note=f"A244 control arm w: {MC.src(row).stem[4:]} moved by {k} T / 6 (T {t:.4f} us) + holds, wait {MC.WAIT}")
            (COS / f"cfg_cw_{row}_k{k}.json").write_text(json.dumps(w, indent=1) + "\n")
            if not (C43 / "cosim" / f"run_cr_{row}_k{k}.json").exists():
                r = dict(m, out=f"run_cr_{row}_k{k}.json",
                         note=f"A244 control arm r: {MC.src(row).stem[4:]} moved by {k} T / 6 (T {t:.4f} us)")
                (COS / f"cfg_cr_{row}_k{k}.json").write_text(json.dumps(r, indent=1) + "\n")
    print("missed", missed(), "->", len(list(COS.glob("cfg_c[rw]_*.json"))), "control cfgs")


if __name__ == "__main__":
    main()
