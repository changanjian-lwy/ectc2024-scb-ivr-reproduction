"""A249 delays (BOUNDARY Section 1), one per board for phases 2-3 and phase 4, as RTL dt_pred (ns):
- settled: the learner's own dt_pred at the end of A246's arm-h runs (full load after the train), median per board;
- opt: A248's one delay per board (the actual turn-on, rail 12 V) mapped back to a command. The plant harness of A248
  (a248_swing.circuit / FastPlant) with the high side commanded at t_cmd after the low side's turn-off command, at the
  rail 12 V and i_off I_OFF, gives the actual turn-on; t_cmd is scanned for the target and dt_pred = t_cmd + the
  board's lead (cfg driver hs_on_lead_ns).
  python3 a249_values.py -> a249_values.json"""
from __future__ import annotations

import importlib.util
import json
import statistics
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a248_swing", TA / "A248_p24_swing_blocks" / "a248_swing.py")
SW = importlib.util.module_from_spec(_s)
_s.loader.exec_module(SW)
BOARDS = ("N0", "N75", "S75h")
I_OFF, RAIL = -17.0, 12.0                                   # A247's median low-side turn-off current of phases 2-4
CMDS = np.arange(-4.0, 16.01, 0.1)


def activation(board, phase, t_cmd):
    """Actual high-side turn-on (ns after the low side's turn-off command) for a command at t_cmd (ns)."""
    from scb_ivr.cosim.circuit import topology
    from scb_ivr.cosim.plant import FastPlant
    p = SW.circuit(board, "full", RAIL)
    n = p.n
    nodes, _ = topology(n, tuple(p.loop_phases))
    v = {f"a{k}": (n - k) * RAIL for k in range(1, n)} | {f"x{k}": 0.0 for k in range(1, n + 1)} | {"out": 1.0}
    for k in p.loop_phases:
        v[f"h{k}"] = 4.0 * RAIL if k == 1 else v[f"a{k - 1}"]
    y = [v[nm] for nm in list(nodes) + [f"h{k}" for k in p.loop_phases]] + [I_OFF] * n + [0.0] * len(p.loop_phases)
    pl = FastPlant(p, np.array(y), [False] * n, [True] * n)
    for j in range(n, 2 * n):
        pl.gm.st[j].update(vgs=p.gate_v_on, drv=True)
    pl.integrate_to(SW.T_PRE, lambda: None)
    for j in range(2 * n):
        pl.gm.st[j]["vds"] = float(pl.vds(j))
    hs, hit = phase - 1, []

    def on_step():
        if not hit and pl.gm.st[hs]["phase"] == "active":
            hit.append(pl.t - SW.T_PRE)
    pl.set_gate(n + phase - 1, False)
    if t_cmd > 0:
        pl.integrate_to(SW.T_PRE + t_cmd * 1e-9, on_step)
    pl.set_gate(hs, True)
    pl.integrate_to(SW.T_PRE + 40e-9, on_step)
    return hit[0] * 1e9 if hit else float("nan")


def one(args):
    board, phase, t_cmd = args
    return activation(board, phase, t_cmd)


def main():
    from multiprocessing import Pool
    a248 = json.loads((TA / "A248_p24_swing_blocks" / "a248_summary.json").read_text())["post_hoc"]["windows"]["at_12v"]
    out = {"i_off_a": I_OFF, "rail_v": RAIL, "boards": {}}
    tasks = [(b, ph, float(c)) for b in BOARDS for ph in (2, 4) for c in CMDS]
    with Pool(10) as pool:
        act = np.array(pool.map(one, tasks, chunksize=8)).reshape(len(BOARDS), 2, len(CMDS))
    for bi, b in enumerate(BOARDS):
        cfg = json.loads(SW.CFGS[b].read_text())
        lead = float(cfg["driver"]["hs_on_lead_ns"])
        recs = [json.loads(f.read_text())["dt_pred_final_ns"]
                for f in (TA / "A246_p24_held_report_floor" / "cosim").glob(f"run_h_p_{b}_*.json")]
        settled = [statistics.median(r[q] for r in recs) for q in (1, 2, 3)]
        opt = []
        for g, key in ((0, f"{b}, phases 2-3"), (1, f"{b}, phase 4")):
            target = a248[key]["fixed_ns"]
            k = int(np.nanargmin(np.abs(act[bi, g] - target)))
            opt.append({"target_act_ns": target, "t_cmd_ns": float(CMDS[k]), "act_ns": float(act[bi, g, k]),
                        "dt_pred_ns": round(float(CMDS[k]) + lead, 3)})
        k_set = [int(np.argmin(np.abs(CMDS - (settled[q] - lead)))) for q in (0, 2)]
        out["boards"][b] = {
            "lead_ns": lead, "settled_dt_pred_ns": [round(x, 3) for x in settled],
            "settled_act_ns_phases_2_4": [float(act[bi, 0, k_set[0]]), float(act[bi, 1, k_set[1]])],
            "opt": opt, "opt_dt_pred_ns": [opt[0]["dt_pred_ns"], opt[0]["dt_pred_ns"], opt[1]["dt_pred_ns"]]}
    (HERE / "a249_values.json").write_text(json.dumps(out, indent=1) + "\n")
    for b, x in out["boards"].items():
        print(b, "settled", x["settled_dt_pred_ns"], "(act", [round(a, 2) for a in x["settled_act_ns_phases_2_4"]], ") opt",
              x["opt_dt_pred_ns"], "(act", [round(o["act_ns"], 2) for o in x["opt"]], "target", [o["target_act_ns"] for o in x["opt"]], ")")


if __name__ == "__main__":
    main()
