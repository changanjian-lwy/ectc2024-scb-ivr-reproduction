"""D68 numbers: the slow hard turn-on (A151 / A152) from the node charge, checked against the co-simulation records.

(1) Start-up on-time. Mode S is open loop at a fixed 400 ns period, so Vo before the handover follows the effective
    on-time: Vo(143.6 us) falls by S_V_PER_NS per ns lost (A152's calibration). A hard turn-on with a current ramp
    lasts t_r = sqrt(2 (Q + i1 t_r) / didt) (Q: the node charge for the rail swing) and costs eta * t_r of the
    rail's volt-seconds. Harness: A145's single-edge plant, SH1 turned on at V_DS 12 V, per (L, didt, i1); the
    loss is the switch node's volt-second deficit against the instantaneous edge, / 12 V. Co-simulation: A151's n0
    runs (turn-on 36 / 18 / 9 A/ns, turn-off 72) against A145's e72 run at the same L, all at ton 35.5 ns.
    Law: t_lost(d) - t_lost(72) = K (d^-1/2 - 72^-1/2), K from the harness (eta sqrt(2 Q)) and fitted on the cosim.
(2) Line-step overshoot. The ramp time over the SH ring's period, t_r / T ~ sqrt(Q / (didt C)) / sqrt(L C), depends
    on x = L * didt_on only. Whole-run max V_DS of l_p48_1us (A145 72 / 72, A151, A152) against x; the 40 V crossing
    x* by linear interpolation between the measured x means.
Writes diagnostics/D68_slow_turn_on.json; prints <= 15 lines. The cosim parts need the raw records of releases
records-a145, -a151 and -a152 in the experiments' cosim folders."""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TA = ROOT / "experiments" / "track_A_periodic_steady_state"
sys.path.insert(0, str(TA / "A145_p24_finite_switching_edges"))
sys.path.insert(0, str(TA / "A144_p24_commutation_loop_inductance"))
import a145_edge as E  # noqa: E402
from scb_ivr.cosim.circuit import Sim  # noqa: E402

S_V_PER_NS = (1.043 - 0.958) / 3.0      # A152: 100 pH, 18 A/ns, ton 35.5 -> 38.5 ns gives Vo(143.5 us) 0.958 -> 1.043 V
T_VO = 143.6e-6                          # the section just before the handover (mode P at 144.0 us)
REF_D = 72.0                             # the turn-off di/dt kept in the spec, and A145's reference turn-on
LS, DIDT, I1 = (50, 100, 150), (0.0, 72.0, 36.0, 24.0, 18.0, 12.0, 9.0, 6.0), (0.0, 2.0, 5.0)
X_GRID = (0.9, 1.35, 1.8, 2.7, 3.6, 7.2, 10.8)


def harness(l_ph, didt_on, i1=0.0, dv=12.0, q=7, t_win=30e-9):
    """SH1 turned on hard at V_DS dv, phase 1 carrying i1 (> 0: SL1 reverse-conducting), turn-off 72 A/ns."""
    rp = E.q_rp(l_ph * 1e-12, q) if l_ph else 0.0
    p = dataclasses.replace(E.params(l_ph, rp, 10e-12), edge_didt_off=REF_D * 1e9, edge_didt_on=didt_on * 1e9)
    y = E.y0(p, 0.0)
    s = Sim(p)
    a1 = 48.0 - dv
    y[s.idx["a1"]], y[s.idx["x1"]] = a1, a1 - E.VCS[0]
    if s.nlp:
        y[s.idx["h2"]] = a1
        y[s.nv + 4 + s.na] = 0.0
    y[s.nv] = i1
    diode = [False] * 4 + [True, False, False, False] if i1 > 0 else None
    pl, tr, ts, el, st = E.run_edge(p, y, [False] * 4, [False, True, True, True], diode, 0, True, (0, 4), E.FastPlant,
                                    t_win=t_win)
    t_r = st["on_t_max_s"] if st else 0.0
    return {"deficit_vns": float(np.sum(12.0 - tr[4]) * p.h * 1e9), "t_r_ns": t_r * 1e9,
            "vds_int_vns": float(np.sum(np.clip(tr[0], 0.0, None)) * p.h * 1e9),
            "q_nc": (0.5 * didt_on * 1e9 * t_r ** 2 - i1 * t_r) * 1e9 if t_r else 0.0}


def startup_harness():
    rows = []
    for l in LS:
        for i1 in I1:
            base = harness(l, 0.0, i1)["deficit_vns"]
            for d in DIDT[1:]:
                r = harness(l, d, i1)
                rows.append(dict(l_ph=l, i1=i1, didt=d, t_lost_ns=(r["deficit_vns"] - base) / 12.0, t_r_ns=r["t_r_ns"],
                                 q_nc=r["q_nc"], eta=r["vds_int_vns"] / (12.0 * r["t_r_ns"]) if r["t_r_ns"] else 0.0))
    for r in rows:
        ref = next(x for x in rows if x["l_ph"] == r["l_ph"] and x["i1"] == r["i1"] and x["didt"] == REF_D)
        r["dt_vs_72_ns"] = r["t_lost_ns"] - ref["t_lost_ns"]
        r["x"] = r["didt"] ** -0.5 - REF_D ** -0.5
    return rows


def fit_k(pts):
    """Least squares through the origin of dt = K x."""
    x = np.array([p[0] for p in pts]); y = np.array([p[1] for p in pts])
    return float((x @ y) / (x @ x)) if len(pts) else None


def vo_at(path, t=T_VO):
    d = json.loads(path.read_text())
    return min(d["sections"], key=lambda s: abs(s["t_s"] - t))["vo"]


def startup_cosim():
    out = []
    for l in LS:
        ref = TA / "A145_p24_finite_switching_edges" / "cosim" / f"run_e72_l{l}_n0.json"
        if not ref.exists():
            continue
        v72 = vo_at(ref)
        for d in (36, 18, 9):
            f = TA / "A151_p24_slow_hard_turn_on" / "cosim" / f"run_on{d}_l{l}_n0.json"
            if f.exists():
                v = vo_at(f)
                out.append(dict(l_ph=l, didt=float(d), vo=v, vo72=v72, dt_vs_72_ns=(v72 - v) / S_V_PER_NS,
                                x=d ** -0.5 - REF_D ** -0.5))
    return out


def vmax(path, t0=0.0):
    d = json.loads(path.read_text())
    return max(max(s["vds_win_v"]) for s in d["sections"] if s["t_s"] >= t0 and s.get("vds_win_v"))


def overshoot_cosim():
    pts = []
    for l in (50, 100, 150):
        f = TA / "A145_p24_finite_switching_edges" / "cosim" / f"run_e72_l{l}_l_p48_1us.json"
        if f.exists():
            pts.append(("A145", l, 72.0, vmax(f)))
    for f in sorted((TA / "A151_p24_slow_hard_turn_on" / "cosim").glob("run_on*_l_p48_1us.json")):
        n = f.stem[4:]
        pts.append(("A151", int(n.split("_l")[1].split("_")[0]), float(n[2:n.index("_")]), vmax(f)))
    for name, l, d in (("s50_l_p48_1us", 50, 36.0), ("s100_l_p48_1us", 100, 18.0)):
        f = TA / "A152_p24_drive_spec_robustness" / "cosim" / f"run_{name}.json"
        if f.exists():
            pts.append(("A152", l, d, vmax(f)))
    rows = [dict(src=s, l_ph=l, didt=d, x_v=round(l * 1e-12 * d * 1e9, 3), vds_max_v=v) for s, l, d, v in pts]
    curve = []
    for x in X_GRID:
        vs = [r["vds_max_v"] for r in rows if abs(r["x_v"] - x) < 1e-6]
        if vs:
            curve.append((x, float(np.mean(vs)), float(np.ptp(vs)) if len(vs) > 1 else 0.0, len(vs)))
    x_star = None
    for (x0, v0, *_), (x1, v1, *_) in zip(curve, curve[1:]):
        if v0 <= 40.0 < v1:
            x_star = x0 + (40.0 - v0) * (x1 - x0) / (v1 - v0)
    return rows, curve, x_star


def curve_at(curve, x):
    xs, vs = [c[0] for c in curve], [c[1] for c in curve]
    return float(np.interp(x, xs, vs))


def main():
    h = startup_harness()
    k_h = {f"{l}/{i1:g}": fit_k([(r["x"], r["dt_vs_72_ns"]) for r in h if r["l_ph"] == l and r["i1"] == i1 and r["didt"] in
                                 (36.0, 18.0, 9.0)]) for l in LS for i1 in I1}
    q = [r["q_nc"] for r in h if r["i1"] == 0.0]
    eta = [r["eta"] for r in h if r["i1"] == 0.0]
    c = startup_cosim()
    k_c = {l: fit_k([(r["x"], r["dt_vs_72_ns"]) for r in c if r["l_ph"] == l]) for l in LS}
    k_all = fit_k([(r["x"], r["dt_vs_72_ns"]) for r in c])
    rows, curve, x_star = overshoot_cosim()
    out = dict(s_v_per_ns=S_V_PER_NS, startup_harness=h, k_harness=k_h, q_nc=[min(q), max(q)], eta=[min(eta), max(eta)],
               k_harness_th=float(np.mean(eta) * np.sqrt(2 * np.mean(q))), startup_cosim=c, k_cosim_by_l=k_c,
               k_cosim_all=k_all, overshoot_rows=rows, overshoot_curve=curve, x_star_v=x_star)
    (ROOT / "diagnostics").mkdir(exist_ok=True)
    (ROOT / "diagnostics" / "D68_slow_turn_on.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"node charge Q {min(q):.0f}-{max(q):.0f} nC, eta {min(eta):.3f}-{max(eta):.3f}, K_th = eta sqrt(2Q) "
          f"{out['k_harness_th']:.1f} ns (A/ns)^0.5")
    print("K harness (L/i1): " + " ".join(f"{k} {v:.1f}" for k, v in k_h.items()))
    print("K cosim by L: " + " ".join(f"{l} {v:.1f}" for l, v in k_c.items() if v) + f"; all {k_all:.1f}")
    for r in c:
        print(f"  cosim L{r['l_ph']} {r['didt']:g} A/ns: Vo {r['vo']:.4f} (72: {r['vo72']:.4f}) dt {r['dt_vs_72_ns']:.2f} ns, "
              f"K-law {k_all * r['x']:.2f}")
    print("overshoot curve x V -> max V_DS: " + " ".join(f"{x:g}:{v:.1f}" for x, v, *_ in curve) + f"; x* (40 V) {x_star:.2f} V")


if __name__ == "__main__":
    main()
