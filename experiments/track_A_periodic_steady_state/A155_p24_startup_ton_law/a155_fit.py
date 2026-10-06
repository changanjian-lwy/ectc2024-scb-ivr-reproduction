"""A155 start-up law fit (before the runs) -> a155_fit.json; prints <= 10 lines.
Vo before the handover (section nearest 143.5 us) of every package run so far (A145 e72 n0, A151 n0, A152 big300 and
s50 / s100 l_p48_1us, A153, A154; L x 0.7 / 1.3 rows left out) against
  Vo = c0 + s (ton - 35.5) - a d_on^-1/2 - b L[nH] + c d_off^-1/2,
least squares with leave-one-out errors. In ns: K = a / s (D68's turn-on term), L term b / s, turn-off term c / s.
The start-up ton for a target Vo: ton_S = 35.5 + (V_T - c0 + a d_on^-1/2 + b L - c d_off^-1/2) / s."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PATS = ("A145_p24_finite_switching_edges/cosim/run_e72_l*_n0.json", "A151_p24_slow_hard_turn_on/cosim/run_on*_n0.json",
        "A152_p24_drive_spec_robustness/cosim/run_big300_*.json", "A152_p24_drive_spec_robustness/cosim/run_s*_l_p48_1us.json",
        "A153_p24_slow_turn_on_laws/cosim/run_*.json", "A154_p24_turn_off_large_loops/cosim/run_*.json")


def rows():
    out = []
    for p in PATS:
        for f in sorted(TA.glob(p)):
            if "L07" in f.name or "L13" in f.name:
                continue
            d = json.loads(f.read_text()); c = d["cfg"]
            e, lp = c.get("edge", {}), c.get("loop", {})
            if not lp.get("l_ph"):
                continue
            out.append(dict(run=f"{f.parent.parent.name[:4]}/{f.stem[4:]}", l_ph=lp["l_ph"], d_on=e.get("didt_on_a_ns", e["didt_a_ns"]),
                            d_off=e["didt_a_ns"], ton=c["ton_ns"],
                            vo=min(d["sections"], key=lambda q: abs(q["t_s"] - 143.5e-6))["vo"]))
    return out


def design(r):
    return [1.0, r["ton"] - 35.5, r["d_on"] ** -0.5, r["l_ph"] * 1e-3, r["d_off"] ** -0.5]


def main():
    rs = rows()
    A = np.array([design(r) for r in rs]); y = np.array([r["vo"] for r in rs])
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    loo = []
    for i in range(len(rs)):
        m = np.ones(len(rs), bool); m[i] = False
        ci, *_ = np.linalg.lstsq(A[m], y[m], rcond=None)
        loo.append(float(y[i] - A[i] @ ci))
    out = dict(n=len(rs), c0=float(c[0]), s=float(c[1]), a=float(-c[2]), b=float(-c[3]), c=float(c[4]),
               k_ns=float(-c[2] / c[1]), l_ns_per_nh=float(-c[3] / c[1]), off_ns=float(c[4] / c[1]),
               rms_v=float(np.sqrt(np.mean((y - A @ c) ** 2))), loo_rms_v=float(np.sqrt(np.mean(np.square(loo)))),
               loo_max_v=float(np.max(np.abs(loo))), rows=[dict(r, loo_v=l) for r, l in zip(rs, loo)])
    (HERE / "a155_fit.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"{len(rs)} runs: s {out['s']:.4f} V/ns, K {out['k_ns']:.1f} ns (A/ns)^1/2, L {out['l_ns_per_nh']:.2f} ns/nH, turn-off "
          f"{out['off_ns']:.1f} ns (A/ns)^1/2; rms {out['rms_v']*1e3:.1f} mV, LOO {out['loo_rms_v']*1e3:.1f} / max {out['loo_max_v']*1e3:.1f} mV")


if __name__ == "__main__":
    main()
