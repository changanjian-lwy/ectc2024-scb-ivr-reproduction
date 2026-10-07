"""D78: the processor-side face of the IVR - a heat source or a second path? D74 kept it adiabatic.

    PYTHONPATH=src python3 scripts/p24_processor_side.py [--jobs 8]

P24 Fig. 6 puts the IVR on the back of the processor package, under the processor. Its top face (above glass 2) is
joined through the package substrate to the processor's side: a convective-type link h_top = 1 / R''_sub to a
temperature T_proc that the processor's own cooling sets (scenarios: R''_sub 1.2-12 K cm^2/W, i.e. a ~1.2 mm substrate
with through-plane k 1-10 W/(m K); T_proc 45-95 C). Bottom face as D74 (h on the spreader; 2e4, or the D77 cooler's
9e4), losses as D74 (D75 lateral copper, D76 core loss kappa 1 / 4), glass-1 fill 2 %. Reports the module's hottest
point, the heat through the top face (positive = into the processor side) and the warmest processor side that still
keeps the module at 85 C. Writes symbolic_derivations/03_P24_native/diagnostics/D78_processor_side.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import p24_thermal_stack as S  # noqa: E402
from scb_ivr import p24_thermal as T  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
H_TOP = (0.0, 1e3 / 1.2, 3e3, 1e4 / 1.2)      # W/(m^2 K): adiabatic, R'' 12 / 3.3 / 1.2 K cm^2/W
T_PROC = (45.0, 65.0, 85.0, 95.0)
H_BOT = (2e4, 9e4)
T_COOL = (25.0, 45.0)
T_LIMIT = 85.0


def run(job):
    tag, h_top, t_proc, h_bot, t_cool, kappa = job
    src, a_sw, a_cu = S.sources("2.5MHz_N29", "86um_150pH", 1.0, kappa)
    m = T.build({"f_g1": 0.02, "h_bot": h_bot, "t_cool": t_cool, "t_cu": 86e-6, "h_top": h_top, "t_top": t_proc})
    t, st, s2, it, fh = T.coupled(m, src, a_sw, a_cu, method="cg")
    y = m["y_mult"]
    return {"tag": tag, "h_top": h_top, "t_proc": t_proc, "h_bot": h_bot, "t_cool": t_cool, "kappa": kappa,
            "t_max": st["t_max"], "junction_max": st["junction_max"], "inductor_max": st["inductor_max"],
            "top_face_mean": float(t[:, :, -1].mean()), "p_total_w": st["p_total_w"],
            "q_top_w": y * fh.get("z1", 0.0), "q_bottom_w": y * fh["z0"], "iterations": it,
            "energy_rel": y * sum(fh.values()) / st["p_total_w"] - 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()
    jobs = []
    for kappa in (1.0, 4.0):
        for h_bot in H_BOT:
            for t_cool in T_COOL:
                for h_top in H_TOP:
                    for t_proc in (T_PROC if h_top > 0 else (0.0,)):
                        jobs.append((f"k{kappa:g}|hb{h_bot:g}|Tc{t_cool:g}", h_top, t_proc, h_bot, t_cool, kappa))
    with ProcessPoolExecutor(args.jobs) as pool:
        rows = list(pool.map(run, jobs))
    out = {"h_top": H_TOP, "t_proc": T_PROC, "rows": rows, "t_proc_max": {}}
    print(f"{len(rows)} solves; worst energy balance {max(abs(r['energy_rel']) for r in rows):.1e}")
    groups = {}
    for r in rows:
        groups.setdefault(r["tag"], []).append(r)
    for tag, rs in groups.items():
        adi = next(r for r in rs if r["h_top"] == 0)
        print(f"{tag}: adiabatic top T_max {adi['t_max']:.1f} C (top face {adi['top_face_mean']:.1f} C, P {adi['p_total_w']:.1f} W)")
        for h_top in H_TOP[1:]:
            sub = sorted((r for r in rs if r["h_top"] == h_top), key=lambda r: r["t_proc"])
            # T_max is affine in T_proc to within the loss coupling: interpolate the 85 C crossing
            tp = None
            for a, b in zip(sub[:-1], sub[1:]):
                if (a["t_max"] - T_LIMIT) * (b["t_max"] - T_LIMIT) <= 0 and a["t_max"] != b["t_max"]:
                    tp = a["t_proc"] + (T_LIMIT - a["t_max"]) * (b["t_proc"] - a["t_proc"]) / (b["t_max"] - a["t_max"])
            if tp is None:
                tp = "all" if sub[-1]["t_max"] <= T_LIMIT else "none"
            out["t_proc_max"][f"{tag}|htop{h_top:.0f}"] = tp
            print(f"   R'' {1e4 / h_top:4.1f} K cm2/W: " + "; ".join(
                f"T_proc {r['t_proc']:.0f}: T_max {r['t_max']:.1f}, q_top {r['q_top_w']:+.1f} W" for r in sub)
                  + f"  -> T_proc for 85 C: {tp if isinstance(tp, str) else f'{tp:.0f} C'}")
    (DIAG / "D78_processor_side.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"wrote {(DIAG / 'D78_processor_side.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
