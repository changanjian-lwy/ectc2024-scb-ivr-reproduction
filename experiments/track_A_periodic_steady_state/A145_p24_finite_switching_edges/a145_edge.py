"""A145 single-edge checks of the plant's finite switching edges (cfg "edge"), from A144's single-edge state
(a144_edge: flying capacitors 36 / 24 / 12 V, constant 48 V input, loop l_ph in series with every high side).
(A) own turn-off (mechanism A): SH1 conducting I0 turns off, SL1 gate off (its reverse conduction clamps x1); peak
    V_DS of SH1, the channel's edge energy, the loop dampers' energy, against the sinc law of a linear ramp
    exciting an LC ring: overshoot(t_f) / overshoot(0) = |sin(pi t_f / T) / (pi t_f / T)|, t_f = I0 / didt, T from
    the instantaneous run (time between the first two V_DS maxima).
(B) hard turn-on (mechanism B): SH1 off at V_DS = dV (phases 2-4 on their low sides), then turned on; peak V_DS of
    SH2 (drain behind its loop at a1) and the edge's energy / duration. dV 3.8 V (valley, i1 = 0) and the reverse-
    conducting cases i1 = +40 / +100 A (SL1 conducts in reverse, dV = 12 V + its drop; A144's start-up case).
(C) Fast, Kernel and Kernel2 plants bit for bit with edges on; edges off = A144's edge() bit for bit.
Writes a145_edge.json; prints <= 15 lines."""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A144_p24_commutation_loop_inductance"))
from a144_edge import VCS, edge as a144_edge_run, params, q_rp, y0  # noqa: E402

from scb_ivr.cosim.plant import FastPlant, KernelPlant, KernelPlant2  # noqa: E402

DIDT = (0.0, 288.0, 144.0, 72.0, 48.0)          # A/ns; 144 A in 0.5 / 1 / 2 / 3 ns; 0 = instantaneous
LS = (50, 100, 150, 300)
T_WIN = 40e-9


def eparams(l_ph, rp, didt, h=10e-12):
    return dataclasses.replace(params(l_ph, rp, h), edge_didt_off=didt * 1e9, edge_didt_on=didt * 1e9)


def loop_energy(pl, p, y_prev, y_now, h):
    """Trapezoid of sum (v_up - v_h)^2 / rp over one step (the loop dampers)."""
    if not (p.loop_phases and p.loop_rp > 0):
        return 0.0
    s = pl.sim
    def pw(y):
        tot = 0.0
        for k in p.loop_phases:
            up = p.vin if k == 1 else y[s.idx[f"a{k - 1}"]]
            tot += (up - y[s.idx[f"h{k}"]]) ** 2 / p.loop_rp
        return tot
    return 0.5 * h * (pw(y_prev) + pw(y_now))


def run_edge(p, y_init, gh, gl, diode, j_sw, level, watch, impl=FastPlant, t_on=2e-9, t_win=T_WIN):
    """Integrate to t_on, set gate j_sw to level, then t_win more; per watched switch the V_DS trace."""
    pl = impl(p, y_init, gh=gh, gl=gl)
    if diode is not None:
        pl.diode = diode
    pl.integrate_to(t_on, lambda: None)
    pl.set_gate(j_sw, level)
    tr = {j: [] for j in watch}
    ts, el, prev = [], [0.0], [np.array(pl.y)]
    def on_step():
        for j in watch:
            tr[j].append(float(pl.vds(j)))
        ts.append(pl.t - t_on)
        y = np.array(pl.y); el[0] += loop_energy(pl, p, prev[0], y, p.h); prev[0] = y
    pl.integrate_to(t_on + t_win, on_step)
    st = getattr(pl, "edge_stats", None)
    return pl, {j: np.array(v) for j, v in tr.items()}, np.array(ts), el[0], st


def ring_period(v, t):
    """Time between the first two local maxima of v (after the first one)."""
    pk = [k for k in range(1, len(v) - 1) if v[k] >= v[k - 1] and v[k] > v[k + 1]]
    big = [k for k in pk if v[k] > v.min() + 0.5 * (v.max() - v.min())]
    return float(t[big[1]] - t[big[0]]) if len(big) >= 2 else None


def turn_off(l_ph, q, didt, i0=143.0, impl=FastPlant):
    rp = q_rp(l_ph * 1e-12, q) if (q and l_ph) else 0.0
    p = eparams(l_ph, rp, didt)
    pl, tr, ts, el, st = run_edge(p, y0(p, i0), [True, False, False, False], [False, True, True, True], None, 0, False,
                                  (0, 4), impl)
    v = tr[0]
    out = dict(l_ph=l_ph, q=q, didt_a_ns=didt, i0=i0, t_f_ns=(i0 / didt if didt else 0.0), vds_pk=float(v.max()),
               t_pk_ns=float(ts[v.argmax()] * 1e9), vsl1_min=float(tr[4].min()), e_loop_nj=el * 1e9,
               e_edge_nj=(st["e_total_j"][0] * 1e9 if st else 0.0), off_neg_steps=(st["off_neg_steps"] if st else 0),
               t_ring_ns=(ring_period(v, ts) or 0.0) * 1e9)
    return out, v


def hard_on(l_ph, q, didt, case, impl=FastPlant):
    """case 'valley': x1 = 12 - 3.8 (SH1 V_DS 3.8 V), i1 = 0; 'rev40' / 'rev100': i1 = +40 / +100 A through SL1's
    reverse conduction (x1 below 0). Phases 2-4: low sides on, i = 40 A. SH1 turned on at t_on."""
    rp = q_rp(l_ph * 1e-12, q) if (q and l_ph) else 0.0
    p = eparams(l_ph, rp, didt)
    y = y0(p, 0.0)
    from scb_ivr.cosim.circuit import Sim
    s = Sim(p)
    dv, i1, diode = {"valley": (3.8, 0.0, None), "rev40": (12.0, 40.0, [False] * 4 + [True, False, False, False]),
                     "rev100": (12.0, 100.0, [False] * 4 + [True, False, False, False])}[case]
    a1 = 48.0 - dv
    y[s.idx["a1"]], y[s.idx["x1"]] = a1, a1 - VCS[0]
    if s.nlp:
        y[s.idx["h2"]] = a1                                  # SH2's drain at its upstream node, loop currents 0
        y[s.nv + 4 + s.na] = 0.0
    y[s.nv] = i1
    pl, tr, ts, el, st = run_edge(p, y, [False] * 4, [False, True, True, True], diode, 0, True, (0, 1, 2, 3), impl)
    out = dict(l_ph=l_ph, q=q, didt_a_ns=didt, case=case, i1=i1, vds_sh1_at_on=None, vds_pk=[float(tr[j].max()) for j in (1, 2, 3)],
               e_edge_nj=(st["e_total_j"][0] * 1e9 if st else 0.0), on_t_ns=(st["on_t_max_s"] * 1e9 if st else 0.0),
               on_i_max=(st["on_i_max_a"] if st else 0.0), on_forced=(st["on_forced"] if st else 0), e_loop_nj=el * 1e9)
    return out, pl


def main():
    out = {"didt_a_ns": DIDT, "off": [], "on": []}
    # (C) identity: edges off = A144's edge(); Fast / Kernel / Kernel2 with edges on
    a = a144_edge_run(100, 143.0, q_rp(100e-12, 7))[1]
    b = turn_off(100, 7, 0.0)[1]
    out["off_equals_a144"] = bool(np.array_equal(a, b))
    tr = [turn_off(100, 7, 144.0, impl=k)[1] for k in (FastPlant, KernelPlant, KernelPlant2)]
    on = [hard_on(100, 7, 144.0, "rev40", impl=k)[1].y for k in (FastPlant, KernelPlant, KernelPlant2)]
    out["impl_identical"] = bool(all(np.array_equal(tr[0], x) for x in tr[1:]) and all(np.array_equal(on[0], x) for x in on[1:]))
    # step size with an edge (100 pH Q 7, 144 A/ns): 10 / 5 ps
    pk = []
    for h in (10e-12, 5e-12):
        p = dataclasses.replace(eparams(100, q_rp(100e-12, 7), 144.0, h))
        pl, tr_h, _, _, st = run_edge(p, y0(p, 143.0), [True, False, False, False], [False, True, True, True], None, 0, False, (0,))
        pk.append([float(tr_h[0].max()), st["e_total_j"][0] * 1e9])
    out["h_check"] = pk
    for l in (0,) + LS:
        for q in ((0,) if l == 0 else (7, 0)):
            base = None
            for d in DIDT:
                for i0 in (143.0, 200.0):
                    r, _ = turn_off(l, q, d, i0)
                    if d == 0.0:
                        r["sinc"] = 1.0
                    else:
                        b0 = next(x for x in out["off"] if x["l_ph"] == l and x["q"] == q and x["i0"] == i0 and x["didt_a_ns"] == 0.0)
                        T = b0["t_ring_ns"]
                        x = np.pi * r["t_f_ns"] / T if T else None
                        r["sinc"] = float(abs(np.sin(x) / x)) if x else None
                    out["off"].append(r)
            for case in ("valley", "rev40", "rev100"):
                if l == 0:
                    continue
                for d in DIDT:
                    out["on"].append(hard_on(l, q, d, case)[0])
    (HERE / "a145_edge.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"edges off = A144 edge(): {out['off_equals_a144']}; Fast/Kernel/Kernel2 identical with edges: {out['impl_identical']}")
    print(f"h 10 / 5 ps (100 pH Q7, 144 A/ns): pk {pk[0][0]:.3f} / {pk[1][0]:.3f} V, E {pk[0][1]:.2f} / {pk[1][1]:.2f} nJ")
    print("turn-off 143 A, Q 7: L | over-rail V at didt " + " / ".join(f"{d:g}" for d in DIDT) + " A/ns | ratio vs sinc at 144")
    for l in LS:
        rows = [x for x in out["off"] if x["l_ph"] == l and x["q"] == 7 and x["i0"] == 143.0]
        r144 = next(x for x in rows if x["didt_a_ns"] == 144.0)
        print(f" {l:3d} | " + " / ".join(f"{x['vds_pk'] - 12:.1f}" for x in rows)
              + f" | {(r144['vds_pk'] - 12) / (rows[0]['vds_pk'] - 12):.2f} vs {r144['sinc']:.2f} (T {rows[0]['t_ring_ns']:.2f} ns)"
              + f" E_edge {r144['e_edge_nj']:.0f} nJ")
    print("hard turn-on rev40, Q 7: L | SH2 pk V at didt " + " / ".join(f"{d:g}" for d in DIDT))
    for l in LS:
        rows = [x for x in out["on"] if x["l_ph"] == l and x["q"] == 7 and x["case"] == "rev40"]
        print(f" {l:3d} | " + " / ".join(f"{x['vds_pk'][0]:.1f}" for x in rows))


if __name__ == "__main__":
    main()
