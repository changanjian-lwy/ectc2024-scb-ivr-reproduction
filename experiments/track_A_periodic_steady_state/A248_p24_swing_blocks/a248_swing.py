"""A248 single-edge harness: one low-side turn-off at a negative current and the node's free swing, on the plant alone
(FastPlant, as A206's harness), with the circuit built by the bridge from a plant-V7 cfg (make_params; every block the
co-simulation has). All low sides conduct, the high sides are off, the ladder sits at rail k = Vin / 4 each; phase
PHASE's low side is commanded off at t = 0 (after T_PRE) with i_off in its inductor and no turn-on follows. Logged for
T_END: the high side's V_DS and the low side's channel state.
Variants drop one block each from the cfg's circuit: gate (ideal switches), miller, r_core, loop, edge; "bare" drops all
(the nearest the plant gets to D57's free node). The channel stops at the end of the low side's last pending / active
gate phase after the command (0 with ideal switches); its current starts to fall at its first active phase.
  python3 a248_swing.py [--jobs 10]          every board x variant x phase group x rail x current -> tmp/a248_swing.npz
  python3 a248_swing.py --smoke              timing of one swing per variant"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from scb_ivr.cosim.bridge import make_params
from scb_ivr.cosim.circuit import topology
from scb_ivr.cosim.plant import FastPlant

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
T_PRE, T_END = 0.1e-9, 40e-9
T_NS = np.arange(0.0, 40.0001, 0.05)
VARIANTS = ("full", "gate", "miller", "r_core", "loop", "edge", "bare")
DROP = {"gate": dict(gate_dev="", gate_switches=()), "miller": dict(gate_miller=False), "r_core": dict(r_core=0.0),
        "loop": dict(loop_phases=(), loop_l=0.0, loop_rp=0.0), "edge": dict(edge_didt_off=0.0, edge_didt_on=0.0)}
CFGS = {   # board -> a plant-V7 cfg carrying it (A246's arm h; A231's N0 at 125 C; A235's L x 1.3 corner)
    "N0": TA / "A246_p24_held_report_floor" / "cosim" / "cfg_h_p_N0_100k.json",
    "N75": TA / "A246_p24_held_report_floor" / "cosim" / "cfg_h_p_N75_100k.json",
    "S75h": TA / "A246_p24_held_report_floor" / "cosim" / "cfg_h_p_S75h_100k.json",
    "N0h": TA / "A231_p24_lead_per_corner" / "cosim" / "cfg_u_N0h_100_base.json",
    "N13": TA / "A235_p24_v7_corner_boards" / "cosim" / "cfg_r_N13_lm48.json",
}
PHASES = (2, 4)                                  # phases 2-3 (the next phase's high side on the node); phase 4
RAILS = np.arange(10.0, 14.01, 1.0)
CURRENTS = np.arange(-60.0, -9.99, 5.0)


def circuit(board, variant, rail):
    cfg = json.loads(CFGS[board].read_text())
    ref = json.loads((PROJECT / cfg["init_run"]).read_text())
    p = make_params(cfg, ref)
    drop = {} if variant == "full" else (
        {k: v for d in DROP.values() for k, v in d.items()} if variant == "bare" else DROP[variant])
    return replace(p, vin=4.0 * rail, t_ramp=0.0, vin_step=0.0, i_step=0.0, i_step2=0.0, pulse_t0=1.0, **drop)


def swing(p, phase, i_off, rail, vo=1.0):
    """V_DS of phase's high side on T_NS after its low side's turn-off command; the times (ns) its channel current
    starts to fall and stops."""
    n = p.n
    nodes, _ = topology(n, tuple(p.loop_phases))
    v = {f"a{k}": (n - k) * rail for k in range(1, n)} | {f"x{k}": 0.0 for k in range(1, n + 1)} | {"out": vo}
    for k in p.loop_phases:                                            # h_k at its upstream node, no loop current
        v[f"h{k}"] = 4.0 * rail if k == 1 else v[f"a{k - 1}"]
    names = list(nodes) + [f"h{k}" for k in p.loop_phases]
    y = [v[nm] for nm in names] + [float(i_off)] * n + [0.0] * len(p.loop_phases)
    pl = FastPlant(p, np.array(y), [False] * n, [True] * n)
    if p.gate_dev:
        for j in range(n, 2 * n):
            pl.gm.st[j].update(vgs=p.gate_v_on, drv=True)
    pl.integrate_to(T_PRE, lambda: None)
    if p.gate_dev:
        for j in range(2 * n):
            pl.gm.st[j]["vds"] = float(pl.vds(j))
    log = []
    ls = n + phase - 1

    def on_step():
        log.append((pl.t - T_PRE, float(pl.vds(phase - 1)), pl.gm.st[ls]["phase"] if p.gate_dev else "idle"))

    pl.set_gate(ls, False)
    pl.integrate_to(T_PRE + T_END, on_step)
    t = np.array([a[0] for a in log]); vd = np.array([a[1] for a in log])
    cond = [a[0] for a in log if a[2] in ("pending", "active")]
    act = [a[0] for a in log if a[2] == "active"]
    return np.interp(T_NS * 1e-9, t, vd), (act[0] * 1e9 if act else 0.0), (cond[-1] * 1e9 if cond else 0.0)


def one(args):
    board, var, phase, rail, i_off = args
    tr, t_fall, t_stop = swing(circuit(board, var, rail), phase, i_off, rail)
    return tr.astype(np.float32), t_fall, t_stop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if not a.smoke:
        from multiprocessing import Pool
        boards = tuple(CFGS)
        tasks = [(b, v, ph, float(r), float(i)) for b in boards for v in VARIANTS for ph in PHASES for r in RAILS
                 for i in CURRENTS]
        with Pool(a.jobs) as pool:
            res = pool.map(one, tasks, chunksize=4)
        shape = (len(boards), len(VARIANTS), len(PHASES), len(RAILS), len(CURRENTS))
        out = PROJECT / "tmp" / "a248_swing.npz"
        np.savez_compressed(out, traces=np.array([r[0] for r in res]).reshape(shape + (-1,)),
                            t_fall=np.array([r[1] for r in res]).reshape(shape),
                            t_stop=np.array([r[2] for r in res]).reshape(shape), boards=np.array(boards),
                            variants=np.array(VARIANTS), phases=np.array(PHASES), rails=RAILS, currents=CURRENTS,
                            t_ns=T_NS)
        print(len(tasks), "swings ->", out.relative_to(PROJECT))
        return
    if a.smoke:
        for var in VARIANTS:
            t0 = time.time()
            tr, _, _ = swing(circuit("N0", var, 12.0), 2, -20.0, 12.0)
            print(f"{var:7s} {time.time() - t0:5.2f} s  V_DS(0) {tr[0]:.2f} V  finite {bool(np.all(np.isfinite(tr)))}")


if __name__ == "__main__":
    main()
