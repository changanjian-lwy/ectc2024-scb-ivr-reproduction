"""A144 single-edge check of the plant's loop inductance: phase 1 conducting I0 through SH1 (phases 2-4 on their low
sides, flying capacitors at 36 / 24 / 12 V, constant 48 V input), SH1 turned off at once with SL1's gate off (its
reverse conduction clamps x1), peak V_DS of SH1 over the next 40 ns. Compared with D65's bound (int v C dv from the
rail) and the series-LC energy balance 0.5 L I0^2 = n int (v - V_rail) C(v) dv. Also: step-size convergence and the
three plant implementations against each other (bit for bit).
Writes a144_edge.json; prints <= 15 lines."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scb_ivr.cosim.circuit import CircuitParams, EPC2067Coss, fit_fig8
from scb_ivr.cosim.plant import FastPlant, KernelPlant, ReferencePlant
from scb_ivr.p24_package_parasitics import overshoot

HERE = Path(__file__).resolve().parent
COSS = EPC2067Coss()
VF, RR, _ = fit_fig8(10.0, 100.0)
VCS = (36.0, 24.0, 12.0)


def series_bound(l, i0, v_rail, n_dev=2, dv=1e-3, v_top=120.0):
    """0.5 L I0^2 = n int_{V_rail}^{V} (v - V_rail) C(v) dv: the loop's energy into the off switch's Coss with the
    rail source returning V_rail dq (KVL L di/dt = V_rail - V_DS around the clamped loop)."""
    v = np.arange(v_rail, v_top, dv)
    f = (v - v_rail) * COSS.c(v)
    e = n_dev * np.concatenate([[0.0], np.cumsum(0.5 * (f[1:] + f[:-1]) * dv)])
    return float(np.interp(0.5 * l * i0 ** 2, e, v))


def q_rp(l, q, v=12.0, n_dev=2):
    """Parallel damping resistance for quality factor q of loop_l with n_dev Coss at v: R = q sqrt(L / C)."""
    return q * float(np.sqrt(l / (n_dev * COSS.c(v))))


def params(l_ph, rp, h=10e-12, phases=(1, 2, 3, 4)):
    return CircuitParams(n=4, vin=48.0, L=2.9333333e-9, R=0.54e-3, cs=6e-6, co=4.672e-3, r_load=4e-3, g_on=1e7, h=h,
                         t_ramp=0.0, nonlinear_coss=True, rev_drop=True, rev_vf=VF, rev_r=RR, diode_check=True,
                         loop_phases=tuple(phases) if l_ph > 0 else (), loop_l=l_ph * 1e-12, loop_rp=rp)


def y0(p, i0, i_other=40.0):
    """SH1 on, SL2..SL4 on: x2..x4 = 0, a_k = x_k + VCS[k-1], x1 = 48 - 36; h_k at its switch's upstream node;
    phase 1 = I0 and phase 1's loop current = I0, the others' loop currents 0."""
    from scb_ivr.cosim.circuit import Sim
    s = Sim(p)
    y = np.zeros(s.ns)
    v = {"x1": 48.0 - VCS[0], "x2": 0.0, "x3": 0.0, "x4": 0.0, "a1": 48.0, "a2": VCS[1], "a3": VCS[2], "out": 1.0,
         "h1": 48.0, "h2": 48.0, "h3": VCS[1], "h4": VCS[2]}
    for nm, k in s.idx.items():
        y[k] = v[nm]
    y[s.nv:s.nv + 4] = [i0, i_other, i_other, i_other]
    if s.nlp:
        y[s.nv + 4 + s.na] = i0                     # loop current of phase 1 (first listed)
    return y


def edge(l_ph, i0, rp=0.0, h=10e-12, impl=FastPlant, t_on=2e-9, t_off=40e-9):
    p = params(l_ph, rp, h)
    pl = impl(p, y0(p, i0), gh=[True, False, False, False], gl=[False, True, True, True])
    pl.integrate_to(t_on, lambda: None)
    pl.set_gate(0, False)
    vmax, tmax, vlo, trace = -1.0, 0.0, 1e9, []
    def on_step():
        nonlocal vmax, tmax, vlo
        v = pl.vds(0)
        if v > vmax:
            vmax, tmax = v, pl.t
        vlo = min(vlo, pl.vds(4))
        trace.append(v)
    pl.integrate_to(t_on + t_off, on_step)
    return dict(l_ph=l_ph, i0=i0, rp=rp, h_ps=h * 1e12, vds_pk=vmax, t_pk_ns=(tmax - t_on) * 1e9, vsl1_min=vlo,
                y_end=[float(x) for x in pl.y]), np.array(trace)


def main():
    out = {"rail_v": 48.0 - VCS[0], "rev_vf": VF, "rev_r": RR, "rows": []}
    # 1. bit-identity of the three plants with the loop on (100 pH, 143 A, undamped)
    ref = [edge(100, 143.0, impl=k, t_off=10e-9)[1] for k in (ReferencePlant, FastPlant, KernelPlant)]
    out["impl_identical"] = bool(np.array_equal(ref[0], ref[1]) and np.array_equal(ref[0], ref[2]))
    # 2. step size at 50 / 300 pH (undamped and Q 7)
    conv = []
    for l in (50, 300):
        for q in (0, 7):
            rp = q_rp(l * 1e-12, q) if q else 0.0
            pk = [edge(l, 143.0, rp, h)[0]["vds_pk"] for h in (10e-12, 5e-12, 2.5e-12)]
            conv.append({"l_ph": l, "q": q, "vds_pk_h10_5_2p5": pk})
    out["convergence"] = conv
    # 3. the sweep against the two energy formulas
    for l in (0, 25, 50, 100, 150, 300):
        for i0 in (143.0, 200.0):
            for q in (0, 7):
                if l == 0 and q:
                    continue
                rp = q_rp(l * 1e-12, q) if (q and l) else 0.0
                r, _ = edge(l, i0, rp)
                r.pop("y_end")
                r.update(q=q, d65_v=overshoot(l * 1e-12, i0, out["rail_v"], COSS, 2) if l else None,
                         series_v=series_bound(l * 1e-12, i0, out["rail_v"]) if l else None)
                out["rows"].append(r)
    (HERE / "a144_edge.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"plants bit-identical with loop on: {out['impl_identical']}")
    for c in conv:
        print(f"h 10/5/2.5 ps, {c['l_ph']} pH Q {c['q'] or 'inf'}: " + " / ".join(f"{v:.3f}" for v in c["vds_pk_h10_5_2p5"]) + " V")
    print("L pH  I0 A  Q   | plant pk V  t_pk ns | D65 V  series V")
    for r in out["rows"]:
        if r["i0"] == 143.0 or r["l_ph"] in (0, 100):
            d, s = r["d65_v"], r["series_v"]
            print(f"{r['l_ph']:4.0f} {r['i0']:5.0f} {r['q'] or 'inf':>3} | {r['vds_pk']:8.2f} {r['t_pk_ns']:7.2f} | "
                  + (f"{d:6.1f} {s:7.1f}" if d else "   -      -"))


if __name__ == "__main__":
    main()
