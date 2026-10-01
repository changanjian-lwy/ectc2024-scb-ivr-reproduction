"""P24 periodic orbits of the timed-low-side event map, one entry point for the variants D47-D51
(src/scb_ivr/p24_orbit_solver.py).

    python3 -m scripts.p24_orbits --variant D47 --pct 5.0                       # D47: A88's corrector
    python3 -m scripts.p24_orbits --variant D48 --pct 5.0 [--tol 1e-7]          # D47 at 125 C
    python3 -m scripts.p24_orbits --variant D49 --pct 5.0 --m-ns 1.0            # static driver mismatch m
    python3 -m scripts.p24_orbits --variant D50 --pct 5.0 --m-ns 0 [--tol 1e-7] # error-based correctors, e = 94 ps
    python3 -m scripts.p24_orbits --variant D51 --pct 5.0 --m-ns 0 [--tol 1e-7] # D50 with period-following slots
    [--out PATH]   (default: symbolic_derivations/03_P24_native/diagnostics/<variant>_orbit_<...>.json)

    python3 -m scripts.p24_orbits --gate [--jobs 4]
recomputes every archived D47-D51 orbit into tmp/orbit_gate/ and compares each with the archived JSON: every key
the archived record has (except wall_s) must be equal, the outer trace entry by entry on the archived fields.

Each variant's seed and rules are those of its original script (audit_p24_lowpred / _hot / _offset / _errcorr /
_followslot_orbits.py, which stay as they are).
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np  # noqa: E402

from scb_ivr.p24_exact_event_map import Circuit  # noqa: E402
from scb_ivr.p24_nonlinear_event_map import Coss  # noqa: E402
from scb_ivr.p24_orbit_solver import MARGIN, solve  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
COSS_CSV = ROOT / "experiments" / "track_A_periodic_steady_state" / "A59_nonlinear_coss_epc2067" / "epc2067_coss_qoss_eoss_digitized.csv"
VF_25, R_DEV_25 = 2.0894454508, 6.0134369436e-3         # A87's fit to Fig. 8 at 25 C, 10-100 A per device
R_FACTOR_125, VF_125, R_DEV_125 = 1.5858, 1.9483, 8.948e-3   # A90: Fig. 9; Fig. 8 at 125 C
E_TGT_PS = 93.75                                          # A92's targets


def epc2067():
    pts = {}
    with open(COSS_CSV) as fh:
        for row in csv.DictReader(fh):
            if row["curve"] == "coss":
                pts[round(float(row["vds_v"]), 4)] = float(row["value"]) * 1e-12
    v = np.array(sorted(pts)); c = np.array([pts[x] for x in v]); keep = v > 0
    v = np.concatenate([[0.0], v[keep]]); c = np.concatenate([[c[keep][0]], c[keep]])
    return Coss.from_points(v, c)


def tag(x):
    return str(x).replace(".", "p")


def run_variant(variant, pct, m_ns=None, tol=1e-8):
    coss = epc2067()
    t_start = time.time()
    if variant == "D47":
        seed = None
        for part in ("A", "B"):
            for r in json.loads((DIAG / f"D45_orbits_{part}.json").read_text())["rows"]:
                if r["pct"] == pct and "section_free" in r:
                    seed = r
        rec = solve(coss, pct, seed["ton_ns"] * 1e-9, [x * 1e-9 for x in seed["d_ns"]], [1.2e-9] * 4, seed["section_free"],
                    high_rule=lambda v: v, low_rule=lambda c: c + MARGIN, vf=VF_25, r_dev=R_DEV_25, tol=tol,
                    record={"pct": pct, "vf_v": VF_25, "r_ohm_per_device": R_DEV_25, "margin_s": MARGIN})
        rec["seed"] = {"source": "D45", "ton_ns": seed["ton_ns"]}
        name = f"D47_orbit_{tag(pct)}pct.json"
    elif variant == "D48":
        seed = json.loads((DIAG / f"D47_orbit_{tag(pct)}pct.json").read_text())
        ckt = dataclasses.replace(Circuit(), R=Circuit().R * R_FACTOR_125)
        rec = solve(coss, pct, seed["ton_ns"] * 1e-9, [x * 1e-9 for x in seed["d_ns"]], [x * 1e-9 for x in seed["d_low_ns"]],
                    seed["section_free"], high_rule=lambda v: v, low_rule=lambda c: c + MARGIN, ckt=ckt, vf=VF_125,
                    r_dev=R_DEV_125, tol=tol,
                    record={"pct": pct, "R_ohm": ckt.R, "vf_v": VF_125, "r_ohm_per_device": R_DEV_125, "margin_s": MARGIN})
        rec["newton_tol"] = tol
        rec["seed"] = {"source": "D47", "ton_ns": seed["ton_ns"]}
        name = f"D48_orbit_{tag(pct)}pct.json"
    elif variant == "D49":
        seed = json.loads((DIAG / f"D47_orbit_{tag(pct)}pct.json").read_text())
        m = m_ns * 1e-9
        rec = solve(coss, pct, seed["ton_ns"] * 1e-9 + 0.5e-9, [x * 1e-9 for x in seed["d_ns"]],
                    [x * 1e-9 + m for x in seed["d_low_ns"]], seed["section_free"], high_rule=lambda v: v,
                    low_rule=lambda c: c + m, vf=VF_25, r_dev=R_DEV_25, tol=tol,
                    record={"pct": pct, "m_ns": m * 1e9, "vf_v": VF_25, "r_ohm_per_device": R_DEV_25})
        name = f"D49_orbit_{tag(pct)}pct_m{tag(m_ns)}.json"
    elif variant in ("D50", "D51"):
        el, eh, m = E_TGT_PS * 1e-12, E_TGT_PS * 1e-12, m_ns * 1e-9
        mtag = tag(m_ns).replace("-", "n")
        rules = dict(high_rule=lambda v: max(v + eh, -m), low_rule=lambda c: max(c + el, m))
        record = {"pct": pct, "el_ps": el * 1e12, "eh_ps": eh * 1e12, "m_ns": m * 1e9, "vf_v": VF_25,
                  "r_ohm_per_device": R_DEV_25}
        if variant == "D50":
            def floors(rec, cross, valley, sx, emap):
                rec.update(low_floor_binds=[c + el < m for c in cross],
                           high_floor_binds=[x is not None and x + eh < -m for x in valley])
            seed = json.loads((DIAG / f"D47_orbit_{tag(pct)}pct.json").read_text())
            rec = solve(coss, pct, seed["ton_ns"] * 1e-9, [max(x * 1e-9 + eh, -m) for x in seed["d_ns"]],
                        [max(x * 1e-9 + el, m) for x in seed["d_low_ns"]], seed["section_free"], vf=VF_25,
                        r_dev=R_DEV_25, tol=tol, record=record, final=floors, **rules)
        else:
            def vcs(rec, cross, valley, sx, emap):              # a_k - x_k at the section
                rec["vcs_v"] = [float(emap.ckt.vin - sx[0]), float(sx[1]), float(sx[2])]
            seed = json.loads((DIAG / f"D50_orbit_{tag(pct)}pct_m{mtag}.json").read_text())
            rec = solve(coss, pct, seed["ton_ns"] * 1e-9, [x * 1e-9 for x in seed["d_ns"]],
                        [x * 1e-9 for x in seed["d_low_ns"]], seed["section_free"], vf=VF_25, r_dev=R_DEV_25, tol=tol,
                        t0=seed["period_ns"] * 1e-9, follow_slots=True, record=record, final=vcs, **rules)
        rec["newton_tol"] = tol
        name = f"{variant}_orbit_{tag(pct)}pct_m{mtag}.json"
    else:
        raise ValueError(variant)
    rec["wall_s"] = time.time() - t_start
    return rec, name


GATE = [  # (variant, pct, m_ns, tol, archived file)
    ("D47", 2.0, None, 1e-8, "D47_orbit_2p0pct.json"), ("D47", 3.0, None, 1e-8, "D47_orbit_3p0pct.json"),
    ("D47", 5.0, None, 1e-8, "D47_orbit_5p0pct.json"), ("D47", 7.5, None, 1e-8, "D47_orbit_7p5pct.json"),
    ("D48", 2.0, None, 1e-7, "D48_orbit_2p0pct.json"), ("D48", 3.0, None, 1e-8, "D48_orbit_3p0pct.json"),
    ("D48", 5.0, None, 1e-8, "D48_orbit_5p0pct.json"), ("D48", 7.5, None, 1e-8, "D48_orbit_7p5pct.json"),
    ("D49", 5.0, 1.0, 1e-8, "D49_orbit_5p0pct_m1p0.json"), ("D49", 5.0, 3.4, 1e-8, "D49_orbit_5p0pct_m3p4.json"),
    ("D50", 5.0, 0.0, 1e-7, "D50_orbit_5p0pct_m0p0.json"), ("D50", 5.0, 3.4, 1e-8, "D50_orbit_5p0pct_m3p4.json"),
    ("D51", 5.0, 0.0, 1e-7, "D51_orbit_5p0pct_m0p0.json"),
]


def compare(old: dict, new: dict) -> list:
    """Keys of the archived record (except wall_s) whose values differ; the outer trace on the archived fields."""
    bad = []
    for k, v in old.items():
        if k == "wall_s":
            continue
        if k == "outer":
            nv = new.get("outer", [])
            if len(nv) != len(v) or any({q: e[q] for q in o} != {q: e.get(q) for q in o} for o, e in zip(v, nv)):
                bad.append("outer")
        elif new.get(k) != v:
            bad.append(k)
    return bad


def gate(jobs):
    out_dir = ROOT / "tmp" / "orbit_gate"; out_dir.mkdir(parents=True, exist_ok=True)

    def one(case):
        variant, pct, m_ns, tol, archived = case
        out = out_dir / archived
        cmd = [sys.executable, "-m", "scripts.p24_orbits", "--variant", variant, "--pct", str(pct), "--tol", str(tol),
               "--out", str(out)] + (["--m-ns", str(m_ns)] if m_ns is not None else [])
        with open(out_dir / f"log_{archived}.txt", "w") as fh:
            subprocess.run(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
        if not out.exists():
            return archived, ["no output"]
        old = json.loads((DIAG / archived).read_text())
        new = json.loads(out.read_text())
        bad = compare(old, new)
        print(f"{archived:32s} {'IDENTICAL' if not bad else 'DIFFERENT ' + str(bad)} ({new.get('wall_s', 0):.0f} s)", flush=True)
        return archived, bad

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        res = list(pool.map(one, GATE))
    summary = {a: b for a, b in res}
    (out_dir / "gate_summary.json").write_text(json.dumps(summary, indent=1))
    ok = all(not b for b in summary.values())
    print("ORBIT GATE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=("D47", "D48", "D49", "D50", "D51"))
    ap.add_argument("--pct", type=float)
    ap.add_argument("--m-ns", type=float)
    ap.add_argument("--tol", type=float, default=1e-8, help="Newton tolerance (accepted up to 10x); D48 Section 7")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    if a.gate:
        return gate(a.jobs)
    rec, name = run_variant(a.variant, a.pct, a.m_ns, a.tol)
    out = a.out or (DIAG / name)
    out.write_text(json.dumps(rec, indent=1, default=float))
    print({k: rec.get(k) for k in ("status", "ton_ns", "period_ns", "lowoff_i", "turnon_vds", "p_rev_w")},
          f"wrote {out} ({rec['wall_s']:.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
