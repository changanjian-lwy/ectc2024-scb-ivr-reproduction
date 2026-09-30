"""D44 audit: P24 exact event map with equivalent-linear Coss (symbolic_derivations/03_P24_native/D44).

The mathematical-model check of A86 (EPC2067 datasheet Coss(V) in the physical model). The exact map is piecewise
linear, so each switch position gets a linear capacitance equal to the device's charge-equivalent capacitance
(q(b) - q(a)) / (b - a) over a stated voltage range, computed from A59's digitised datasheet curve:
- L0: Co(tr) 1860 pF (D43; gate at 3%);
- L1: 0-12 V for every device;
- L2: the valley-resonance swing: low sides 0-2.3 V, high sides 12 -/+ 2.3 V.

For each: capacitance continuation from D43's 3% soft orbit, then regulated, valley-consistent orbits (20 ns restart,
as A86) at 3 -> 1% and 3 -> 7.5%, and the phase-4 restart orbit (d_4 = 20 ns) at 3% and 2%.

python3 -m scripts.audit_p24_ceq_orbits   (writes symbolic_derivations/03_P24_native/diagnostics/D44_ceq_orbits.json)
"""
from __future__ import annotations

import csv
import dataclasses
import hashlib
import json
import time

import numpy as np
from scipy.interpolate import PchipInterpolator

from scripts.audit_p24_exact_orbits import ROOT, TRACK_A, PEAK, consistent_orbit, orbit_report
from scb_ivr.p24_exact_event_map import Circuit

D43 = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics" / "D43_orbits.json"
OUT = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics" / "D44_ceq_orbits.json"
COSS_CSV = TRACK_A / "A59_nonlinear_coss_epc2067" / "epc2067_coss_qoss_eoss_digitized.csv"
N_HIGH, N_LOW = 2, 3            # EPC2067 devices in parallel per switch position (A69)
SWING = 2.3                     # V, the valley-resonance swing (D44 Section 1)


def coss_q():
    """Per-device q(V) of the digitised EPC2067 Fig. 5a: PCHIP on a 0.1 V grid (as A59 and A86), q its integral."""
    pts = {}
    with open(COSS_CSV) as fh:
        for row in csv.DictReader(fh):
            if row["curve"] == "coss":
                pts[round(float(row["vds_v"]), 4)] = float(row["value"]) * 1e-12
    v = np.array(sorted(pts)); c = np.array([pts[x] for x in v]); keep = v > 0
    v = np.concatenate([[0.0], v[keep]]); c = np.concatenate([[c[keep][0]], c[keep]])
    grid = np.arange(0.0, 40.0 + 1e-9, 0.1)
    return PchipInterpolator(grid, np.interp(grid, v, c), extrapolate=False).antiderivative()


def ceq(q, a, b):
    return float((q(b) - q(a)) / (b - a))


def how_class(ok, rep):
    if ok is None:
        return "no_orbit"
    if ok is False:
        return "not_consistent"
    return "soft" if all(h == "high_on" for h in rep["turnon_how"]) else \
        "restart(" + ",".join(str(k + 1) for k, h in enumerate(rep["turnon_how"]) if h != "high_on") + ")"


def solve(ckt, pct, ton, d, s, restart=(), iters=12):
    ok, emap, (sx, J, hist, log) = consistent_orbit(ckt, -pct / 100 * PEAK, ton, d, s, restart, iters=iters)
    rec = {"pct": pct, "restart_fixed": list(restart)}
    if ok is None or "error" in log:
        rec["status"] = "no_orbit"
        return rec, None
    rep = orbit_report(emap, sx, J, hist, log)
    rec.update(status=how_class(ok, rep), ton_ns=emap.ctl.ton * 1e9, period_ns=rep["period_ns"], vo_v=rep["vo_v"],
               d_ns=rep["d_ns"], lowoff_i=rep["lowoff_i"], turnon_vds=rep["turnon_vds"], turnon_how=rep["turnon_how"],
               floquet_max=rep["floquet_abs"][0], natural_valley=rep["natural_valley"], section_free=rep["section_free"])
    return rec, (sx, emap.ctl.ton, list(emap.ctl.d_high)) if ok else None


def line(tag, r):
    if r["status"] == "no_orbit":
        return f"  {tag:6s} {r['pct']:4.1f}% no orbit"
    nv = r["natural_valley"][3]
    return (f"  {tag:6s} {r['pct']:4.1f}% {r['status']:15s} Ton {r['ton_ns']:.3f} T {r['period_ns']:.2f} ns "
            f"d {np.round(r['d_ns'], 2)} lowoff4 {r['lowoff_i'][3]:+.3f} A Vds_on {np.round(r['turnon_vds'], 3)} "
            f"valley4 {None if nv is None else round(nv['t_ns'], 2)} ns |mu| {r['floquet_max']:.4f}")


def main():
    t0 = time.time()
    q = coss_q()
    check = {"co_tr_0_20_pf": ceq(q, 0, 20) * 1e12, "printed_co_tr_pf": 1860.0}
    per = {"L0": (1860e-12, 1860e-12), "L1": (ceq(q, 0, 12), ceq(q, 0, 12)),
           "L2": (ceq(q, 12 - SWING, 12 + SWING), ceq(q, 0, SWING))}
    d43 = json.loads(D43.read_text())
    seed = next(r for r in d43["sweep"]["soft"] if r["pct"] == 3.0)
    s3, ton3, d3 = np.array(seed["section_free"]), seed["ton_ns"] * 1e-9, [x * 1e-9 for x in seed["d_ns"]]
    base = Circuit()
    out = {"coss_csv_sha256": hashlib.sha256(COSS_CSV.read_bytes()).hexdigest(), "check": check, "swing_v": SWING,
           "cases": {}}
    print(f"Co(tr) from the curve {check['co_tr_0_20_pf']:.0f} pF (printed 1860)", flush=True)
    for name, (ch, cl) in per.items():
        ckt = dataclasses.replace(base, c_high=N_HIGH * ch, c_low=N_LOW * cl)
        case = {"per_device_pf": {"high": ch * 1e12, "low": cl * 1e12}, "c_high_nf": ckt.c_high * 1e9,
                "c_low_nf": ckt.c_low * 1e9, "continuation": [], "sweep": [], "restart_branch": []}
        print(f"{name}: per device high {ch * 1e12:.0f} pF, low {cl * 1e12:.0f} pF -> c_high {ckt.c_high * 1e9:.3f} nF, "
              f"c_low {ckt.c_low * 1e9:.3f} nF", flush=True)
        st = (s3, ton3, d3)
        for a in (0.25, 0.5, 0.75, 1.0):                  # capacitance continuation at 3%
            c_a = dataclasses.replace(base, c_high=(1 - a) * base.c_high + a * ckt.c_high,
                                      c_low=(1 - a) * base.c_low + a * ckt.c_low)
            rec, nxt = solve(c_a, 3.0, st[1], st[2], st[0], iters=20)
            case["continuation"].append({"alpha": a, "status": rec["status"]})
            if nxt is None:
                print(f"  continuation stopped at alpha {a}: {rec['status']}", flush=True)
                break
            st = nxt
        else:
            rec3 = rec
            if name == "L0":
                out["gate_vs_d43_3pct_max_abs_diff"] = float(np.max(np.abs(np.array(rec3["section_free"]) - s3)))
                print(f"  gate: max |section - D43 3%| = {out['gate_vs_d43_3pct_max_abs_diff']:.2e}", flush=True)
            case["sweep"].append(rec3)
            print(line(name, rec3), flush=True)
            for pcts in ((2.5, 2.0, 1.5, 1.0), (5.0, 7.5)):
                cur = st
                for pct in pcts:
                    r, nxt = solve(ckt, pct, cur[1], cur[2], cur[0])
                    case["sweep"].append(r)
                    print(line(name, r), flush=True)
                    if nxt is not None:
                        cur = nxt
            for pct in (3.0, 2.5, 2.0):                    # phase-4 restart orbit, continued downward from 3%
                r, nxt = solve(ckt, pct, st[1], st[2], st[0], restart=(3,))
                case["restart_branch"].append(r)
                print(line("rs20", r), flush=True)
                if nxt is not None:
                    st = nxt
        out["cases"][name] = case
    out["wall_s"] = time.time() - t0
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {OUT.relative_to(ROOT)} ({out['wall_s']:.0f} s)")


if __name__ == "__main__":
    main()
