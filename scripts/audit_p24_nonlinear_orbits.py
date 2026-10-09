"""D45 audit: P24 periodic orbits with the EPC2067 datasheet Coss(V) (symbolic_derivations/03_P24_native/D45).

Regulated (Vo = 1 V via Ton), valley-consistent (each soft phase's delay = its natural valley time, measured from the
low-side turn-off itself) orbits with a 20 ns restart, as A86. Parts (run in parallel):
  A  nonlinear, soft branch, 3% -> 2.5 -> 2 -> 1.5 -> 1%
  B  nonlinear, soft branch, 3% -> 5 -> 7.5%
  C  nonlinear, phase-4 restart branch (d_4 = 20 ns) at 3, 2.5, 2%; then the escape test at 2% (d_4 follows its valley)
  D  linear Co(tr) (D43's circuit) with the corrected valley time, 1-7.5% and the restart branch: the size of D43's
     one-grid-step valley offset (D45 Section 7)
  E  (after A-D) which side's curve matters: the datasheet curve on the high sides only (low sides at D44's L2
     constant) and on the low sides only (high sides at L2's constant), at 3% and 2%

python3 -m scripts.audit_p24_nonlinear_orbits --part A   (writes diagnostics/D45_orbits_<part>.json)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time

import numpy as np

from scripts.audit_p24_exact_orbits import ROOT, TRACK_A, PEAK
from scb_ivr.p24_exact_event_map import Circuit, Control, ExactEventMap, section_full
from scb_ivr.p24_nonlinear_event_map import Coss, NonlinearEventMap, nl_valley_after_lowoff, orbit_chord, section_jacobian

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
COSS_CSV = TRACK_A / "A59_nonlinear_coss_epc2067" / "epc2067_coss_qoss_eoss_digitized.csv"
T_RS = 20e-9


def epc2067():
    pts = {}
    with open(COSS_CSV) as fh:
        for row in csv.DictReader(fh):
            if row["curve"] == "coss":
                pts[round(float(row["vds_v"]), 4)] = float(row["value"]) * 1e-12
    v = np.array(sorted(pts)); c = np.array([pts[x] for x in v]); keep = v > 0
    v = np.concatenate([[0.0], v[keep]]); c = np.concatenate([[c[keep][0]], c[keep]])
    return Coss.from_points(v, c)


def make_map(kind, ctl, coss):
    return NonlinearEventMap(Circuit(), ctl, coss=coss) if kind == "nonlinear" else ExactEventMap(Circuit(), ctl)


def report(emap, sx, J, hist, log):
    ckt = emap.ckt
    v, i = section_full(sx, ckt)
    valleys = []
    for ph in range(1, ckt.n + 1):
        r = nl_valley_after_lowoff(emap, v, i, ph)
        valleys.append(None if r is None else {"t_ns": r[0] * 1e9, "vds_v": r[1]})
    lo = {x["phase"]: x["i"] for x in log["lowoff"]}
    ton = {x["phase"]: x for x in log["turnon"]}
    return {"section_free": sx.tolist(), "newton_residuals": hist, "period_ns": log["period"] * 1e9, "vo_v": float(sx[3]),
            "floquet_abs": sorted(np.abs(np.linalg.eigvals(section_jacobian(emap, sx)[0])).tolist(), reverse=True),  # D81
            "lowoff_i": [lo.get(k) for k in range(1, ckt.n + 1)],
            "turnon_vds": [ton[k]["vds"] if k in ton else None for k in range(1, ckt.n + 1)],
            "turnon_how": [ton[k]["how"] if k in ton else None for k in range(1, ckt.n + 1)],
            "ton_ns": emap.ctl.ton * 1e9, "d_ns": [x * 1e9 for x in emap.ctl.d_high], "natural_valley": valleys}


def consistent(kind, coss, pct, ton, d0, s0, restart=(), J=None, iters=30, tol=None):
    """D43's consistent_orbit with the corrected valley time and the chord Newton."""
    tol = tol or (1e-8 if kind == "nonlinear" else 1e-9)
    target = -pct / 100 * PEAK
    d = list(d0)
    for ph in restart:
        d[ph] = T_RS
    s, dvdt = np.array(s0, float), 0.054e9
    rec = {"pct": pct, "target_a": target, "restart_fixed": list(restart), "outer": []}
    for it in range(iters):
        emap = make_map(kind, Control(ton=ton, i_target=target, d_high=tuple(d), t_restart_high=T_RS), coss)
        try:
            sx, J, hist, log = orbit_chord(emap, s, J=J, tol=tol)
        except (RuntimeError, ValueError, np.linalg.LinAlgError) as exc:
            rec.update(status="no_orbit", error=str(exc))
            return rec, None
        if hist[-1] > 10 * tol:
            rec.update(status="no_orbit", newton_residuals=hist)
            return rec, None
        v, i = section_full(sx, emap.ckt)
        new_d = list(d)
        for ph in range(4):
            if ph in restart:
                continue
            r = nl_valley_after_lowoff(emap, v, i, ph + 1)
            if r is not None:
                new_d[ph] = r[0]
        dd = max(abs(a - b) for a, b in zip(new_d, d))
        rec["outer"].append({"vo": float(sx[3]), "dd_ns": dd * 1e9, "d_ns": [x * 1e9 for x in new_d],
                             "newton_iters": len(hist)})
        if abs(sx[3] - 1.0) < 1e-6 and dd < 2e-12:
            rep = report(emap, sx, J, hist, log)
            hows = rep["turnon_how"]
            rep["status"] = "soft" if all(h == "high_on" for h in hows) else \
                "restart(" + ",".join(str(k + 1) for k, h in enumerate(hows) if h != "high_on") + ")"
            rec.update(rep)
            return rec, (sx, emap.ctl.ton, list(emap.ctl.d_high), J)
        ton = ton + (1.0 - sx[3]) / dvdt
        d, s = new_d, sx
    rec.update(status="not_consistent", last_d_ns=[x * 1e9 for x in d])
    return rec, None


def line(r):
    if r["status"] in ("no_orbit", "not_consistent"):
        return f"  {r['pct']:4.1f}% {r['status']} {r.get('last_d_ns', '')}"
    nv = r["natural_valley"][3]
    return (f"  {r['pct']:4.1f}% {r['status']:12s} Ton {r['ton_ns']:.3f} T {r['period_ns']:.2f} ns d {np.round(r['d_ns'], 2)} "
            f"lowoff {np.round(r['lowoff_i'], 3)} Vds_on {np.round(r['turnon_vds'], 3)} valley4 "
            f"{None if nv is None else round(nv['t_ns'], 3)} |mu| {r['floquet_abs'][0]:.4f} outer {len(r['outer'])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=("A", "B", "C", "D", "E"))
    a = ap.parse_args()
    t0 = time.time()
    coss = epc2067()
    kind = "linear" if a.part == "D" else "nonlinear"
    out = {"part": a.part, "kind": kind, "coss_csv_sha256": hashlib.sha256(COSS_CSV.read_bytes()).hexdigest(),
           "co_tr_pf": float(coss.q(20.0) / 20 * 1e12), "t_restart_high_ns": T_RS * 1e9, "rows": []}
    d44 = json.loads((DIAG / "D44_ceq_orbits.json").read_text())
    seed = d44["cases"]["L2" if kind == "nonlinear" else "L0"]["sweep"][0]          # 3%, soft
    s0, ton0 = np.array(seed["section_free"]), seed["ton_ns"] * 1e-9
    d0 = [x * 1e-9 + 0.25e-9 for x in seed["d_ns"]]                                    # D44 used D43's early valley
    print(f"part {a.part} ({kind}); Co(tr) {out['co_tr_pf']:.0f} pF", flush=True)
    if a.part == "E":
        l2 = d44["cases"]["L2"]["per_device_pf"]
        hyb = {"curve_high_only": (coss, Coss.constant(l2["low"] * 1e-12)),
               "curve_low_only": (Coss.constant(l2["high"] * 1e-12), coss)}
        out["hybrids"] = {}
        for name, cc in hyb.items():
            rows, cur = [], None
            for pct in (3.0, 2.0):
                args = (ton0, d0, s0, ()) if cur is None else (cur[1], cur[2], cur[0], (), cur[3])
                r, nxt = consistent(kind, cc, pct, *args)
                rows.append(r); print(f"  {name}" + line(r), flush=True)
                if nxt is not None:
                    cur = nxt
            out["hybrids"][name] = rows
        out["wall_s"] = time.time() - t0
        path = DIAG / "D45_orbits_E.json"
        path.write_text(json.dumps(out, indent=1, default=float))
        print(f"wrote {path.relative_to(ROOT)} ({out['wall_s']:.0f} s)")
        return
    r3, st = consistent(kind, coss, 3.0, ton0, d0, s0)
    out["rows"].append(r3); print(line(r3), flush=True)
    if st is None:
        raise SystemExit("no 3% orbit")
    if a.part in ("A", "B", "D"):
        seqs = {"A": [(2.5, 2.0, 1.5, 1.0)], "B": [(5.0, 7.5)], "D": [(2.5, 2.0, 1.5, 1.0), (5.0, 7.5)]}[a.part]
        for seq in seqs:
            cur = st
            for pct in seq:
                r, nxt = consistent(kind, coss, pct, cur[1], cur[2], cur[0], J=cur[3])
                out["rows"].append(r); print(line(r), flush=True)
                if nxt is not None:
                    cur = nxt
    if a.part in ("C", "D"):
        d43 = json.loads((DIAG / "D43_orbits.json").read_text())          # seed: D43's 3% restart orbit
        rsd = next(r for r in d43["sweep"]["phase4_restart"] if r["pct"] == 3.0)
        cur = (np.array(rsd["section_free"]), rsd["ton_ns"] * 1e-9,
               [x * 1e-9 + 0.25e-9 for x in rsd["d_ns"][:3]] + [T_RS], None)
        rs = []
        for pct in (3.0, 2.5, 2.0):
            r, nxt = consistent(kind, coss, pct, cur[1], cur[2], cur[0], restart=(3,), J=cur[3])
            r["branch"] = "phase4_restart_20ns"; rs.append(r); print("  restart branch" + line(r), flush=True)
            if nxt is not None:
                cur = nxt
        out["restart_branch"] = rs
        last = next((r for r in reversed(rs) if r["pct"] == 2.0 and "natural_valley" in r), None)
        if last is not None and last["natural_valley"][3] is not None:
            d_esc = [x * 1e-9 for x in last["d_ns"][:3]] + [last["natural_valley"][3]["t_ns"] * 1e-9]
            r, _ = consistent(kind, coss, 2.0, last["ton_ns"] * 1e-9, d_esc, np.array(last["section_free"]), J=cur[3])
            r["branch"] = "escape_from_restart"; out["escape_2pct"] = r; print("  escape" + line(r), flush=True)
    out["wall_s"] = time.time() - t0
    path = DIAG / f"D45_orbits_{a.part}.json"
    path.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {path.relative_to(ROOT)} ({out['wall_s']:.0f} s)")


if __name__ == "__main__":
    main()
