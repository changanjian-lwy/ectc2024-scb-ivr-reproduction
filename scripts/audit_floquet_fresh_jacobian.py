"""D81 check 1: the Floquet moduli of D45-D51 recomputed at each archived orbit.

The archived records took their moduli from orbit_chord's chord matrix, which may come from an earlier Newton step or
an earlier outer iteration (other Ton / delays). This script rebuilds each record's event map at its final parameters,
checks that the archived section is still a fixed point (|F(s) - s|), and computes a fresh central-difference
Jacobian there at five step sizes (1e-3 .. 1e-7 relative to max(1, |s_c|)), with the event order of every perturbed
cycle compared with the base cycle's: large steps show the map's curvature, small ones the integrator's noise (DOP853,
rtol 1e-11, atol 1e-10), and the plateau between them is the derivative.

    python3 -m scripts.audit_floquet_fresh_jacobian [--jobs 4]   (writes diagnostics/D81_floquet_recheck.json)
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
PEAK, T_RS = 125.0, 20e-9
FDS = (1e-3, 1e-4, 1e-5, 1e-6, 1e-7)


def cases():
    out = []
    for part in "ABCD":
        d = json.loads((DIAG / f"D45_orbits_{part}.json").read_text())
        for k, r in enumerate(d["rows"]):
            if "floquet_abs" in r:
                out.append({"file": f"D45_orbits_{part}.json", "row": k, "kind": d["kind"], "rec": r})
    for p in sorted(DIAG.glob("D46_orbit_*.json")):
        out.append({"file": p.name, "row": None, "kind": "drop", "rec": json.loads(p.read_text())})
    for v in ("D47", "D48", "D49", "D50", "D51"):
        for p in sorted(DIAG.glob(f"{v}_orbit_*.json")):
            out.append({"file": p.name, "row": None, "kind": "lowpred", "rec": json.loads(p.read_text())})
    return out


def build(case):
    from scb_ivr.p24_exact_event_map import Circuit, Control, ExactEventMap
    from scb_ivr.p24_nonlinear_event_map import NonlinearEventMap
    from scb_ivr.p24_drop_event_map import DropEventMap
    from scb_ivr.p24_lowpred_event_map import ControlLP, LowPredEventMap
    from scripts.audit_p24_nonlinear_orbits import epc2067
    r, kind = case["rec"], case["kind"]
    kw = dict(ton=r["ton_ns"] * 1e-9, i_target=-r["pct"] / 100 * PEAK, d_high=tuple(x * 1e-9 for x in r["d_ns"]),
              t_restart_high=T_RS)
    if kind == "linear":
        return ExactEventMap(Circuit(), Control(**kw))
    if kind == "nonlinear":
        return NonlinearEventMap(Circuit(), Control(**kw), coss=epc2067())
    if kind == "drop":
        return DropEventMap(Circuit(), Control(**kw, t_d_low=r["td_ns"] * 1e-9), coss=epc2067(), vf=r["vf_v"],
                            r_dev=r["r_ohm_per_device"])
    ckt = Circuit() if "R_ohm" not in r else dataclasses.replace(Circuit(), R=r["R_ohm"])
    kw["d_low"] = tuple(x * 1e-9 for x in r["d_low_ns"])
    if r.get("t0_ns") is not None:
        kw["t0"] = r["t0_ns"] * 1e-9
    return LowPredEventMap(ckt, ControlLP(**kw), coss=epc2067(), vf=r["vf_v"], r_dev=r["r_ohm_per_device"])


def check(case):
    from scb_ivr.p24_nonlinear_event_map import section_jacobian
    t = time.time()
    emap, s = build(case), np.array(case["rec"]["section_free"], float)
    old = case["rec"]["floquet_abs"]
    res = {"file": case["file"], "row": case["row"], "pct": case["rec"]["pct"], "status": case["rec"]["status"],
           "chord_abs": old}
    for fd in FDS:
        J, resid, same = section_jacobian(emap, s, fd)
        mods = sorted(np.abs(np.linalg.eigvals(J)).tolist(), reverse=True)
        res[f"fd{fd:g}"] = {"abs": mods, "residual": resid, "same_order": same}
    top = {f"{fd:g}": res[f"fd{fd:g}"]["abs"][0] for fd in FDS}
    plateau = [top["0.0001"], top["1e-05"]]               # between curvature (1e-3) and noise (1e-6, 1e-7)
    res["max_fresh"] = 0.5 * sum(plateau)
    res["plateau_spread"] = abs(plateau[0] - plateau[1])
    res["d_max_vs_chord"] = res["max_fresh"] - old[0]
    res["wall_s"] = time.time() - t
    print(f"{case['file']:28s} {case['row']} {res['pct']:4.1f}% chord {old[0]:.5f} fresh "
          + " ".join(f"{v:.5f}" for v in top.values())
          + f" resid {res['fd1e-06']['residual']:.1e} order {[res[f'fd{fd:g}']['same_order'] for fd in FDS]} "
          f"{res['wall_s']:.0f} s", flush=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", default=None, help="substring of the file name")
    a = ap.parse_args()
    cs = [c for c in cases() if a.only is None or a.only in c["file"]]
    with ProcessPoolExecutor(a.jobs) as ex:
        rows = list(ex.map(check, cs))
    dm = [abs(r["d_max_vs_chord"]) for r in rows]
    out = {"what": "D81 check 1: Floquet moduli at the archived D45-D51 orbits, fresh central differences",
           "fd_rel": list(FDS), "rows": rows,
           "summary": {"n": len(rows), "max_abs_change_of_max_modulus": max(dm),
                       "max_fresh_modulus": max(r["max_fresh"] for r in rows),
                       "max_plateau_spread": max(r["plateau_spread"] for r in rows),
                       "all_same_event_order": all(r[f"fd{fd:g}"]["same_order"] for r in rows for fd in FDS),
                       "max_fixed_point_residual": max(r["fd1e-06"]["residual"] for r in rows)}}
    if a.only is None:
        (DIAG / "D81_floquet_recheck.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main()
