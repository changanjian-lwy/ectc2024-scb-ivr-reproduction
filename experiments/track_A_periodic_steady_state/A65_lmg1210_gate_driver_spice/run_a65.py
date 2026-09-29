"""A65 (copy of A64) driver: one design per process (at most two LTspice processes at once).

Stages (each writes one never-overwritten record per solved point to runs/):

  literal  BOUNDARY timing taken literally: A59's command dead times and Ton as
           the LTspice gate commands, primary case (R_drv 1.0 Ohm, 60 C).
  center   channel-referenced sweep centre for one case: command dead times
           moved (fixed point) until the MEAN channel dead times over the four
           phases equal A59's d_rise / d_fall; rounded to 0.05 ns; then solved.
  sweep    BOUNDARY Section 3 sweep around that centre: d_fall in centre
           +/-0.3 ns (0.1 ns steps) at the centre d_rise, then d_rise +/-0.3 ns
           at the best d_fall; an outward extension (declared) if the best
           value lands on the grid edge.
  transfer for a non-primary case: its own centre plus the primary optimum's
           offsets from the primary centre (channel-referenced transfer).
  step     the chosen point re-solved with half the maximum timestep.
  brute    plain run from A59's z* at the primary centre timing and the
           accepted Ton, no extrapolation and no Ton update, until the
           BOUNDARY stop criterion holds (periods-needed evidence).
  wave     phase-1 edge waveforms at the case optimum (CSV + summary).

Usage: python3 run_a65.py --design zvs --stages literal,center,sweep --case 1.0:60
Environment: A65_WORKDIR (short LTspice work directory, default /tmp/a65).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import a65_netlist as A
import a65_solver as S

HERE = Path(__file__).resolve().parent
LOGS = HERE / "logs"
PRIMARY = A.Case(1.0, 60.0)
A64_RUNS = HERE.parent / "A64_vendor_model_spice_crosscheck" / "runs"
A64_SEEDS = {"zvs": A64_RUNS / "zvs_R1.0_T60_r3.750_f2.300.json",
             "baseline": A64_RUNS / "baseline_R1.0_T60_r4.050_f2.950.json"}
GRID_S = 0.1e-9
HALF_WIDTH_STEPS = 3
MAX_EXTENSION_STEPS = 3


def log_to(path):
    fh = open(path, "a")

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        fh.write(line + "\n")
        fh.flush()
    return log


#: A65 driver cases -> plateau-equivalent series resistance per device (A65
#: BOUNDARY Section 2). Used only for the initial timing guess (`initial_guess`
#: scales A64's measured gate delays by it); the netlist uses the I-V tables.
DRIVER_EQUIV_OHM = {"LMG1210_SW": 1.38, "LMG1210_DEV": 0.61}


def parse_case(text):
    r, t = text.split(":")
    if r in DRIVER_EQUIV_OHM:
        return A.Case(DRIVER_EQUIV_OHM[r], float(t), r)
    return A.Case(float(r), float(t))


def records(design, case=None):
    out = []
    for p in sorted(S.RUNS.glob(f"{design}_*.json")):
        rec = json.loads(p.read_text())
        if case is not None and rec.get("case") != case.as_dict():
            continue
        rec["_file"] = p.name
        out.append(rec)
    return out


def find(design, case, kind, dr=None, df=None, maxstep=S.DEFAULT_MAXSTEP_S):
    best = None
    for rec in records(design, case):
        if rec.get("kind") != kind or rec.get("status") not in ("REGULATED_TO_250W", "CHANNEL_MATCHED"):
            continue
        if dr is not None and abs(rec["dead_time_rise_s"] - dr) > 1e-13:
            continue
        if df is not None and abs(rec["dead_time_fall_s"] - df) > 1e-13:
            continue
        if abs(rec["chunks"][-1]["max_step_s"] - maxstep) > 1e-15:
            continue
        best = rec
    return best


def grid_points(design, case):
    """All accepted grid points (kind center/sweep) of one case at the default step."""
    pts = {}
    for rec in records(design, case):
        if rec.get("kind") in ("center", "sweep", "transfer") and rec["status"] == "REGULATED_TO_250W" \
                and abs(rec["chunks"][-1]["max_step_s"] - S.DEFAULT_MAXSTEP_S) < 1e-15:
            key = (round(rec["dead_time_rise_s"] * 1e12), round(rec["dead_time_fall_s"] * 1e12))
            pts[key] = rec
    return pts


def solve_and_save(a59, case, dr, df, seed, kind, log, suffix="", **kw):
    ton0, state0, origin0 = seed
    name = S.point_name(a59["design"], case, dr, df, suffix)
    log(f"solve {name} ({kind}) from Ton={ton0 * 1e9:.4f} ns origin={origin0 * 1e9:.1f} ns")
    res = S.solve(a59, case, dr, df, ton0, state0, origin0, tag=f"{a59['design'][0]}{kind[:2]}",
                  log=log, **kw)
    res.update({"experiment": "A65", "classification": "SENSITIVITY_ONLY", "kind": kind,
                "a59_record": a59["source_record"],
                "a59_timing": {"dead_time_rise_s": a59["dead_time_rise_s"],
                               "dead_time_fall_s": a59["dead_time_fall_s"],
                               "ton_cmd_s": a59["ton_cmd_s"]}})
    path = S.save_record(res, name)
    fin = res["final"]
    log(f"  -> {res['status']} P_loss={fin['p_loss_corr_w']:.4f} W (raw {fin['p_loss_w']:.4f}) "
        f"Pout={fin['p_out_w']:.3f} gate={fin['p_gate_total_w']:.3f} periods={res['periods_total']} "
        f"file={path.name}")
    return res


def seed_of(rec):
    return rec["ton_cmd_s"], rec["final"]["final_state"], A.QUIET_S


def initial_guess(a59, case):
    """Command dead-time guess for the centre search: A59 d + gate-delay offset.

    Offsets were measured in the first LTspice runs (R_drv 1 Ohm, 60 C) and are
    scaled by (R_drv + rg)/(1 + rg) for other drive cases; the fixed point then
    corrects them. Only a starting value.
    """
    scale = (case.r_drv_ohm + 0.3) / 1.3
    off_r = {"zvs": 1.70e-9, "baseline": 2.15e-9}[a59["design"]]
    off_f = {"zvs": 2.30e-9, "baseline": 2.35e-9}[a59["design"]]
    return a59["dead_time_rise_s"] + off_r * scale, a59["dead_time_fall_s"] + off_f * scale


def snap(x):
    return round(x / 0.05e-9) * 0.05e-9


def stage_literal(a59, log):
    seed = (a59["ton_cmd_s"], a59["z_star"], 0.0)
    return solve_and_save(a59, PRIMARY, a59["dead_time_rise_s"], a59["dead_time_fall_s"], seed,
                          "literal", log, suffix="_literal", max_chunks=10)


def stage_center(a59, case, log):
    existing = find(a59["design"], case, "center")
    if existing:
        log(f"centre exists: {existing['_file']}")
        return existing
    # seed: the primary centre if solved (warm), else A59's z*
    prim = find(a59["design"], PRIMARY, "center")
    if prim is not None and case != PRIMARY:
        seed = seed_of(prim)
    elif A64_SEEDS[a59["design"]].exists():
        # A65 BOUNDARY Section 3: warm start from A64's R_drv 1.0 Ohm optimum
        # (read only). The seed changes convergence speed, not the orbit.
        seed = seed_of(json.loads(A64_SEEDS[a59["design"]].read_text()))
        log(f"  seed: {A64_SEEDS[a59['design']].name} (A64, read only)")
    else:
        seed = (a59["ton_cmd_s"], a59["z_star"], 0.0)
    dr0, df0 = initial_guess(a59, case)
    name = S.point_name(a59["design"], case, dr0, df0, "_centre_search")
    log(f"centre search {name}")
    res = S.solve(a59, case, dr0, df0, *seed, tag=f"{a59['design'][0]}cs", log=log, max_chunks=12,
                  compensate_to=(a59["dead_time_rise_s"], a59["dead_time_fall_s"]))
    res.update({"experiment": "A65", "classification": "SENSITIVITY_ONLY", "kind": "centre_search",
                "a59_record": a59["source_record"]})
    S.save_record(res, name)
    log(f"  centre search {res['status']}: dr={res['dead_time_rise_s'] * 1e9:.4f} "
        f"df={res['dead_time_fall_s'] * 1e9:.4f} ns")
    dr, df = snap(res["dead_time_rise_s"]), snap(res["dead_time_fall_s"])
    return solve_and_save(a59, case, dr, df, seed_of(res), "center", log,
                          slope_w_per_s=res["slope_w_per_s"])


def best_on_line(pts, fixed_key, fixed_val, var_key):
    line = [(k, r) for k, r in pts.items() if k[fixed_key] == fixed_val]
    if not line:
        return None
    k, r = min(line, key=lambda kr: kr[1]["final"]["p_loss_corr_w"])
    return k[var_key], r


def stage_sweep(a59, case, log):
    centre = find(a59["design"], case, "center")
    if centre is None:
        raise RuntimeError("no centre")
    cr, cf = centre["dead_time_rise_s"], centre["dead_time_fall_s"]
    slope = centre.get("slope_w_per_s", 27e9)

    def walk(fixed, values, vary_fall):
        """Continuation outward from the centre along one line."""
        prev = None
        for v in values:
            v = round(v * 1e12) * 1e-12
            dr, df = (fixed, v) if vary_fall else (v, fixed)
            key = (round(dr * 1e12), round(df * 1e12))
            pts = grid_points(a59["design"], case)
            if key in pts:
                prev = pts[key]
                continue
            if prev is None:
                # nearest solved point on this line as the seed
                same = [r for k, r in pts.items() if (k[0] == key[0] if vary_fall else k[1] == key[1])]
                prev = min(same, key=lambda r: abs((r["dead_time_fall_s"] if vary_fall else r["dead_time_rise_s"]) - v))
            prev = solve_and_save(a59, case, dr, df, seed_of(prev), "sweep", log,
                                  slope_w_per_s=prev.get("slope_w_per_s", slope))

    def line(fixed, centre_val, vary_fall):
        up = [centre_val + k * GRID_S for k in range(1, HALF_WIDTH_STEPS + 1)]
        down = [centre_val - k * GRID_S for k in range(1, HALF_WIDTH_STEPS + 1)]
        down = [v for v in down if v > S.DT_FLOOR_S]
        walk(fixed, up, vary_fall)
        walk(fixed, down, vary_fall)
        # declared outward extension while the best value sits on the edge
        for _ in range(MAX_EXTENSION_STEPS):
            pts = grid_points(a59["design"], case)
            fk, vk = (0, 1) if vary_fall else (1, 0)
            best_v, _rec = best_on_line(pts, fk, round(fixed * 1e12), vk)
            vals = sorted(k[vk] for k in pts if k[fk] == round(fixed * 1e12))
            if best_v == vals[-1]:
                walk(fixed, [vals[-1] * 1e-12 + GRID_S], vary_fall)
                log(f"  extension step (edge optimum) {'d_fall' if vary_fall else 'd_rise'} +0.1 ns")
            elif best_v == vals[0] and vals[0] * 1e-12 - GRID_S > S.DT_FLOOR_S:
                walk(fixed, [vals[0] * 1e-12 - GRID_S], vary_fall)
                log(f"  extension step (edge optimum) {'d_fall' if vary_fall else 'd_rise'} -0.1 ns")
            else:
                break

    line(cr, cf, vary_fall=True)
    pts = grid_points(a59["design"], case)
    f_best, _ = best_on_line(pts, 0, round(cr * 1e12), 1)
    f_best_s = f_best * 1e-12
    log(f"  best d_fall at d_rise={cr * 1e9:.3f}: {f_best_s * 1e9:.3f} ns")
    line(f_best_s, cr, vary_fall=False)
    pts = grid_points(a59["design"], case)
    r_best, rec = best_on_line(pts, 1, f_best, 0)
    log(f"  optimum: d_rise={r_best * 1e-3:.3f} d_fall={f_best * 1e-3:.3f} ns "
        f"P_loss={rec['final']['p_loss_corr_w']:.4f} W ({rec['_file'] if '_file' in rec else ''})")


def optimum(design, case):
    pts = grid_points(design, case)
    if not pts:
        return None
    k, rec = min(pts.items(), key=lambda kr: kr[1]["final"]["p_loss_corr_w"])
    return rec


def stage_transfer(a59, case, log):
    prim_c = find(a59["design"], PRIMARY, "center")
    prim_o = optimum(a59["design"], PRIMARY)
    centre = find(a59["design"], case, "center")
    if prim_c is None or prim_o is None or centre is None:
        raise RuntimeError("transfer needs the primary centre/optimum and this case's centre")
    dr = centre["dead_time_rise_s"] + (prim_o["dead_time_rise_s"] - prim_c["dead_time_rise_s"])
    df = centre["dead_time_fall_s"] + (prim_o["dead_time_fall_s"] - prim_c["dead_time_fall_s"])
    if find(a59["design"], case, "transfer", dr, df) or (abs(dr - centre["dead_time_rise_s"]) < 1e-13
                                                         and abs(df - centre["dead_time_fall_s"]) < 1e-13):
        log("transfer point already solved (or equals the centre)")
        return
    solve_and_save(a59, case, dr, df, seed_of(centre), "transfer", log,
                   slope_w_per_s=centre.get("slope_w_per_s", 27e9))


def stage_step(a59, case, log, which="optimum"):
    rec = optimum(a59["design"], case) if which == "optimum" else find(a59["design"], case, "center")
    half = S.DEFAULT_MAXSTEP_S / 2
    if (S.RUNS / (S.point_name(a59["design"], case, rec["dead_time_rise_s"], rec["dead_time_fall_s"],
                               "_step25ps") + ".json")).exists():
        log("step check exists for the optimum")
        return None
    return solve_and_save(a59, case, rec["dead_time_rise_s"], rec["dead_time_fall_s"], seed_of(rec),
                          "step", log, suffix="_step25ps", maxstep=half,
                          slope_w_per_s=rec.get("slope_w_per_s", 27e9), save_all_gates_final=True)


def stage_brute(a59, log, n_max=160, n_chunk=20):
    """Plain periods from z* at the primary centre timing and its accepted Ton."""
    centre = find(a59["design"], PRIMARY, "center")
    dr, df, ton = centre["dead_time_rise_s"], centre["dead_time_fall_s"], centre["ton_cmd_s"]
    state, origin = dict(a59["z_star"]), 0.0
    chunks, total = [], 0
    while total < n_max:
        ch = S.chunk(a59, PRIMARY, ton, dr, df, state, origin, n_chunk, maxstep=S.DEFAULT_MAXSTEP_S,
                     reltol=S.DEFAULT_RELTOL, tag=f"{a59['design'][0]}bf{len(chunks)}")
        ch["acceptance"] = S.accepted(ch)
        total += n_chunk
        rels = [p["rel_change"] for p in ch["periods"]]
        log(f"  brute {total} periods: rel last={rels[-1]:.2e} Pout={ch['periods'][-1]['p_out_w']:.3f} "
            f"Pcorr={ch['periods'][-1]['p_loss_corr_w']:.4f}")
        chunks.append({k: v for k, v in ch.items() if k not in ("last", "gates")})
        if ch["acceptance"]["converged"] and ch["acceptance"]["loss_stable"]:
            break
        state, origin = ch["final_state"], A.QUIET_S
    first = None
    k = 0
    for ch in chunks:
        for p in ch["periods"]:
            k += 1
            if first is None and p["rel_change"] < S.TOL_REL:
                first = k
    rec = {"experiment": "A65", "kind": "brute", "design": a59["design"],
           "case": PRIMARY.as_dict(),
           "status": "CONVERGED" if chunks[-1]["acceptance"]["converged"] else "NOT_CONVERGED",
           "dead_time_rise_s": dr, "dead_time_fall_s": df, "ton_cmd_s": ton,
           "periods_total": total, "first_period_below_1e-3": first,
           "compare_to": centre.get("_file"), "chunks": chunks,
           "final_p_loss_corr_w": chunks[-1]["periods"][-1]["p_loss_corr_w"],
           "final_p_out_w": chunks[-1]["periods"][-1]["p_out_w"]}
    S.save_record(rec, S.point_name(a59["design"], PRIMARY, dr, df, "_brute"))
    log(f"  brute: first period below 1e-3 = {first}; accelerated centre P_loss "
        f"{centre['final']['p_loss_corr_w']:.4f} vs brute {rec['final_p_loss_corr_w']:.4f} W")


def stage_wave(a59, case, log):
    """Phase-1 edge waveforms at the case optimum (2 extra periods, raw kept).

    Writes waveforms/<design>_<case>_phase1_<edge>.csv and a JSON summary that
    splits the outgoing group's edge excess at its drain-voltage milestones.
    """
    import numpy as np  # noqa: PLC0415

    import a65_analysis as Y  # noqa: PLC0415
    import a65_ltspice as L  # noqa: PLC0415

    rec = optimum(a59["design"], case)
    tag = f"{a59['design'][0]}wv"
    ch = S.chunk(a59, case, rec["ton_cmd_s"], rec["dead_time_rise_s"], rec["dead_time_fall_s"],
                 rec["final"]["final_state"], A.QUIET_S, 2, maxstep=S.DEFAULT_MAXSTEP_S,
                 reltol=S.DEFAULT_RELTOL, tag=tag, keep_raw=True)
    raw = L.workdir() / f"{tag}.raw"
    d = L.load_raw(raw)
    t = d["time"]
    out_dir = HERE / "waveforms"
    out_dir.mkdir(exist_ok=True)
    reff = ch["last"]["decomposition"]["r_eff_ohm"]
    summary = {"source_record": rec.get("_file"), "design": a59["design"], "case": case.tag,
               "vth_knee_v": Y.vth_knee(case.temp_c), "edges": []}
    for e in ch["last"]["edges"]:
        if e["phase"] != 1:
            continue
        inc = e["incoming"]
        outg = "low" if inc == "high" else "high"
        w1, w2 = e["cmd_outgoing_off_s"] - 1e-9, e["cmd_incoming_on_s"] + 6e-9
        m = (t >= w1) & (t <= w2)
        cols = {
            "t_ns": (t[m] - e["cmd_outgoing_off_s"]) * 1e9,
            "vgs_out_v": Y.gate_vgs(d, outg, 1)[m], "vgs_in_v": Y.gate_vgs(d, inc, 1)[m],
            "vds_out_v": Y.branch_v(d, outg, 1)[m], "vds_in_v": Y.branch_v(d, inc, 1)[m],
            "id_out_group_a": d[f"I(V_A{outg[0].upper()}1)"][m], "id_in_group_a": d[f"I(V_A{inc[0].upper()}1)"][m],
            "i_l1_a": d["I(LIND1)"][m],
        }
        path = out_dir / f"{a59['design']}_{case.tag}_phase1_{e['edge']}.csv"
        k = 2
        while path.exists():
            path = out_dir / f"{a59['design']}_{case.tag}_phase1_{e['edge']}_v{k}.csv"
            k += 1
        keys = list(cols)
        with open(path, "w") as fh:
            fh.write(",".join(keys) + "\n")
            for i in range(int(m.sum())):
                fh.write(",".join(f"{cols[c][i]:.6g}" for c in keys) + "\n")
        # split the outgoing group's excess at its drain-voltage milestones
        vds_o = Y.branch_v(d, outg, 1)
        id_o = d[f"I(V_A{outg[0].upper()}1)"]
        p_ex = vds_o * id_o - reff[f"{outg[0]}1"] * id_o * id_o
        t_off_cmd, t_end = e["cmd_outgoing_off_s"], e["cmd_incoming_on_s"] + 5e-9
        final_v = float(np.max(vds_o[(t >= t_off_cmd) & (t <= t_end)]))
        up = Y.crossings(t, vds_o, 0.5, t_off_cmd, t_end, +1)
        up90 = Y.crossings(t, vds_o, 0.9 * final_v, t_off_cmd, t_end, +1)
        t_a = up[0] if up else t_end
        t_b = up90[0] if up90 else t_end
        summary["edges"].append({
            "edge": e["edge"], "csv": path.name, "outgoing": outg, "incoming": inc,
            "inductor_current_at_cmd_off_a": e["inductor_current_at_cmd_off_a"],
            "outgoing_vds_0p5V_after_cmd_ns": (t_a - t_off_cmd) * 1e9,
            "outgoing_vds_90pct_after_cmd_ns": (t_b - t_off_cmd) * 1e9,
            "outgoing_excess_before_vds_0p5V_j": Y.integrate(t, p_ex, t_off_cmd, t_a),
            "outgoing_excess_vds_0p5V_to_90pct_j": Y.integrate(t, p_ex, t_a, t_b) if t_b > t_a else 0.0,
            "outgoing_excess_after_90pct_j": Y.integrate(t, p_ex, t_b, t_end) if t_end > t_b else 0.0,
            "outgoing_group_current_at_vds_0p5V_a": Y.interp(t, id_o, t_a),
            "channel_timing": {k: e[k] for k in ("channel_off_s", "channel_on_s", "channel_dead_time_s",
                                                 "turn_off_delay_s", "turn_on_delay_s",
                                                 "vds_in_at_channel_on_v")},
        })
    raw.unlink()
    spath = out_dir / f"{a59['design']}_{case.tag}_phase1_summary.json"
    k = 2
    while spath.exists():
        spath = out_dir / f"{a59['design']}_{case.tag}_phase1_summary_v{k}.json"
        k += 1
    spath.write_text(json.dumps(summary, indent=1))
    log(f"  waveforms written: {spath.name}")


def stage_decomp(a59, case, log, files=None, n=3):
    """Re-run n plain periods from accepted records' final states and decompose by gate state.

    Default targets: the case's centre and optimum (and, for the primary case,
    the literal point). The record keeps its own P_loss so that the re-run
    can be checked against the accepted value.
    """
    import a65_analysis as Y  # noqa: PLC0415
    if Y.coss_table() is None:
        log("decomp skipped: run the coss stage first (runs/static_epc2067_coss.json)")
        return
    targets = []
    if files:
        targets = [json.loads((S.RUNS / f).read_text()) | {"_file": f} for f in files]
    else:
        for rec in (find(a59["design"], case, "center"), optimum(a59["design"], case)):
            if rec is not None and rec["_file"] not in [t["_file"] for t in targets]:
                targets.append(rec)
        if case == PRIMARY:
            lit = [r for r in records(a59["design"], case) if r.get("kind") == "literal"
                   and r["status"] == "REGULATED_TO_250W"]
            targets += lit[-1:]
    for rec in targets:
        # "_decompc": decomposition with the Coss displacement correction
        # (the first two "_decomp" records predate the Coss characterization)
        name = rec["_file"].replace(".json", "_decompc")
        if (S.RUNS / f"{name}.json").exists():
            log(f"decomp exists: {name}")
            continue
        ch = S.chunk(a59, case, rec["ton_cmd_s"], rec["dead_time_rise_s"], rec["dead_time_fall_s"],
                     rec["final"]["final_state"], A.QUIET_S, n,
                     maxstep=rec["chunks"][-1]["max_step_s"], reltol=S.DEFAULT_RELTOL,
                     tag=f"{a59['design'][0]}dc")
        ch["acceptance"] = S.accepted(ch)
        import a65_analysis as Y  # noqa: PLC0415
        ch["channel_summary"] = Y.channel_summary(ch["last"]["edges"])
        out = {"experiment": "A65", "classification": "SENSITIVITY_ONLY", "kind": "decomp",
               "source_record": rec["_file"], "source_p_loss_corr_w": rec["final"]["p_loss_corr_w"],
               "design": a59["design"], "case": rec["case"], "status": "DECOMPOSED",
               "ton_cmd_s": rec["ton_cmd_s"], "dead_time_rise_s": rec["dead_time_rise_s"],
               "dead_time_fall_s": rec["dead_time_fall_s"], "periods": ch["periods"],
               "final": S.summarize(ch)}
        S.save_record(out, name)
        sd = out["final"]["state_decomposition"]
        log(f"  decomp {rec['_file']}: P_loss {out['final']['p_loss_corr_w']:.3f} "
            f"(accepted {rec['final']['p_loss_corr_w']:.3f}); "
            + " ".join(f"{k}={v:.2f}" for k, v in sd["totals_w"].items())
            + f" a59_style_cond={sd['a59_style_conduction_w']:.2f}")


def model_header(model):
    return f".include {A.MODEL_FILES[model].name}\n"


def stage_xcheck(a59, case, log, n=6):
    """Accepted point re-run with EPC2067X (charge expressions in x), same Ton and timing.

    Starts from the accepted final state and runs n plain periods; if the
    x-form changed the device physics the loss, Pout and timing would move.
    """
    targets = [r for r in (optimum(a59["design"], case), find(a59["design"], case, "center")) if r]
    for rec in targets:
        name = rec["_file"].replace(".json", "_xcheck")
        if (S.RUNS / f"{name}.json").exists():
            continue
        ch = S.chunk(a59, case, rec["ton_cmd_s"], rec["dead_time_rise_s"], rec["dead_time_fall_s"],
                     rec["final"]["final_state"], A.QUIET_S, n, maxstep=rec["chunks"][-1]["max_step_s"],
                     reltol=S.DEFAULT_RELTOL, tag=f"{a59['design'][0]}xc", model="EPC2067X")
        import a65_analysis as Y  # noqa: PLC0415
        cs = Y.channel_summary(ch["last"]["edges"])
        last = ch["periods"][-1]
        out = {"experiment": "A65", "kind": "xcheck", "model": "EPC2067X", "source_record": rec["_file"],
               "design": a59["design"], "case": rec["case"], "status": "CHECKED",
               "ton_cmd_s": rec["ton_cmd_s"], "dead_time_rise_s": rec["dead_time_rise_s"],
               "dead_time_fall_s": rec["dead_time_fall_s"],
               "source_p_loss_corr_w": rec["final"]["p_loss_corr_w"], "source_p_out_w": rec["final"]["p_out_w"],
               "p_loss_corr_w": last["p_loss_corr_w"], "p_out_w": last["p_out_w"],
               "rel_change": last["rel_change"], "p_gate_total_w": ch["last"]["p_gate_total_w"],
               "channel_dead_time_rise_mean_s": cs["rise"]["channel_dead_time_mean_s"],
               "channel_dead_time_fall_mean_s": cs["fall"]["channel_dead_time_mean_s"],
               "source_channel_dead_time_rise_mean_s": rec["final"]["channel_summary"]["rise"]["channel_dead_time_mean_s"],
               "source_channel_dead_time_fall_mean_s": rec["final"]["channel_summary"]["fall"]["channel_dead_time_mean_s"],
               "periods": ch["periods"]}
        S.save_record(out, name)
        log(f"  xcheck {rec['_file']}: EPC2067X P_loss {out['p_loss_corr_w']:.3f} W (Pout {out['p_out_w']:.2f}) "
            f"vs as-distributed {out['source_p_loss_corr_w']:.3f} W (Pout {out['source_p_out_w']:.2f})")


def stage_static(log, model=A.DEFAULT_MODEL):
    """Static vendor-model characteristics (single device): Rds(on) at Vgs = 5 V, Vsd at Vgs = 0."""
    import a65_ltspice as L  # noqa: PLC0415
    currents = (10, 25, 50, 75, 100)
    out = {"experiment": "A65", "kind": "static", "status": "MEASURED", "model": model, "points": []}
    for temp in (25, 60):
        for vg, sign in ((5.0, 1), (0.0, -1)):
            meas = "\n".join(f".meas dc V{i} FIND V(d) AT {sign * i}" for i in currents)
            text = (f"* A65 static EPC2067 check\n{model_header(model)}.temp {temp}\n"
                    f"VG g 0 {vg}\nI1 0 d 0\nX1 g d 0 {model}\n"
                    f".dc I1 {min(sign * 100, sign * 1)} {max(sign * 100, sign * 1)} 0.5\n{meas}\n"
                    ".options numdgt=15\n.end\n")
            run = L.run(text, f"static_T{temp}_vg{int(vg)}")
            for i in currents:
                v = run["meas"].get(f"v{i}")
                row = {"temp_c": temp, "vgs_v": vg, "i_d_a": sign * i, "v_ds_v": v}
                if vg > 0 and v is not None:
                    row["r_ds_on_ohm"] = v / i
                out["points"].append(row)
    S.save_record(out, "static_epc2067_vendor_model")
    for row in out["points"]:
        log(f"  static T={row['temp_c']} Vgs={row['vgs_v']} I={row['i_d_a']} -> Vds={row['v_ds_v']}"
            + (f" R={row['r_ds_on_ohm'] * 1e3:.4f} mOhm" if "r_ds_on_ohm" in row else ""))


def charge_ramp(model, current_a, tstop, step, tag, temp=60, gate_ramp=False, vds=20.0, options=""):
    """Charge one device with a constant current; return (V, Q) of the charged port.

    Output ramp (default): gate held at the source (Vgs = 0), current into the
    drain, Q = I*t. Gate ramp: drain held at `vds`, current into the gate
    (stops below threshold use only the first ~1 V), Q = I*t.
    """
    import numpy as np  # noqa: PLC0415

    import a65_ltspice as L  # noqa: PLC0415
    if gate_ramp:
        # the model's 36 MOhm gate-drain/gate-source resistors would bias a floating
        # gate to ~Vds/2 in the operating point: start it at 0 V explicitly. The
        # voltage is read at the INTERNAL gate/source nodes (behind rg = 0.3 Ohm).
        body = (f"VD d 0 {vds}\nI1 0 g PWL(0 0 1p {current_a})\nX1 g d 0 {model}\n"
                ".save V(x1:gate) V(x1:source)\n.ic V(g)=0\n")
        names = ["V(x1:gate)", "V(x1:source)"]
    else:
        body = f"VG g 0 0\nI1 0 d PWL(0 0 1p {current_a})\nX1 g d 0 {model}\n.save V(d)\n"
        names = ["V(d)"]
    text = (f"* A65 charge ramp {model}\n{model_header(model)}.temp {temp}\n{body}"
            f".tran 0 {tstop} 0 {step}\n.options numdgt=15 plotwinsize=0 {options}\n.end\n")
    run = L.run(text, tag)
    d = L.load_raw(run["raw_path"], names)
    run["raw_path"].unlink()
    tt = d["time"]
    v = d[names[0]] - d[names[1]] if gate_ramp else d[names[0]]
    q = np.clip(tt - 0.5e-12, 0.0, None) * current_a
    return v, q


def stage_modelcheck(log):
    """Is the vendor model's nonlinear capacitance integrated charge-conservingly?

    (1) LTspice itself: a 2 nF capacitor written three ways (C=2n, Q=2n*x,
        Q=2n*v(d)) charged by 1 A; the charge absorbed by 2/5/8 V must be
        4/10/16 nC.
    (2) Both vendor variants (as distributed: EPC2067; x-form: EPC2067X):
        output charge Q(V) at Vgs = 0 for three current/timestep pairs, which
        must not depend on either; and Ciss at Vds = 20 V from a gate ramp.
    """
    import numpy as np  # noqa: PLC0415

    import a65_ltspice as L  # noqa: PLC0415
    out = {"experiment": "A65", "kind": "model_check", "status": "MEASURED",
           "datasheet_typ": {"coss_20v_pf": 1071, "qoss_20v_nc": 37, "ciss_20v_pf": 2178,
                             "coss_tr_0_20v_pf": 1860, "qg_5v_nc": 17.1, "rg_ohm": 0.4},
           "ltspice_qcap": [], "output_ramp": [], "gate_ramp": []}
    for name, line in (("C=2n", "C1 d 0 2n"), ("Q=2n*x", "C1 d 0 Q=2n*x"), ("Q=2n*v(d)", "C1 d 0 Q=2n*v(d)")):
        for step in ("2p", "0.2p"):
            text = (f"* qcap check\nI1 0 d PWL(0 0 1p 1)\n{line}\nR1 d 0 1G\n"
                    f".tran 0 10n 0 {step}\n.save V(d)\n.options numdgt=15 plotwinsize=0\n.end\n")
            run = L.run(text, f"mc_q{len(out['ltspice_qcap'])}")
            d = L.load_raw(run["raw_path"], ["V(d)"])
            run["raw_path"].unlink()
            q = np.clip(d["time"] - 0.5e-12, 0, None)
            row = {"element": name, "max_step": step,
                   "charge_nc_at_2_5_8_v": [float(np.interp(x, d["V(d)"], q) * 1e9) for x in (2, 5, 8)],
                   "expected_nc": [4.0, 10.0, 16.0]}
            out["ltspice_qcap"].append(row)
            log(f"  qcap {name} step {step}: Q(2,5,8 V) = {row['charge_nc_at_2_5_8_v']} nC (expected 4/10/16)")
    for model in ("EPC2067", "EPC2067X"):
        for cur, tstop, step, opts in ((0.1, "750n", "20p", ""), (1.0, "75n", "2p", ""), (1.0, "40n", "0.2p", ""),
                                       (1.0, "75n", "2p", "reltol=1e-4"), (1.0, "40n", "0.2p", "reltol=1e-4"),
                                       (1.0, "75n", "2p", "reltol=1e-5")):
            v, q = charge_ramp(model, cur, tstop, step, f"mc_o{len(out['output_ramp'])}", options=opts)
            grid = np.arange(0.0, 20.0001, 0.1)
            qg = np.interp(grid, v, q)
            row = {"model": model, "current_a": cur, "max_step": step, "options": opts or "default reltol 1e-3",
                   "q_nc_at_1_6_12_20_v": [float(np.interp(x, grid, qg) * 1e9) for x in (1, 6, 12, 20)],
                   "c_pf_at_0_12_20_v": [float(x * 1e12) for x in np.interp([0.05, 12, 19.95], grid,
                                                                             np.gradient(qg, grid))],
                   "coss_tr_0_20v_pf": float(np.interp(20, grid, qg) / 20 * 1e12)}
            out["output_ramp"].append(row)
            log(f"  output ramp {model} {cur} A step {step} {opts}: Q(1,6,12,20 V) = "
                + ", ".join(f"{x:.2f}" for x in row["q_nc_at_1_6_12_20_v"]) + " nC")
        for cur, tstop, step in ((0.1, "40n", "20p"), (1.0, "4n", "2p")):
            v, q = charge_ramp(model, cur, tstop, step, f"mc_g{len(out['gate_ramp'])}", gate_ramp=True)
            ciss = float(np.interp(0.5, v, q) / 0.5)
            row = {"model": model, "current_a": cur, "max_step": step, "vds_v": 20.0,
                   "ciss_0_0p5v_pf": ciss * 1e12}
            out["gate_ramp"].append(row)
            log(f"  gate ramp {model} {cur} A step {step}: Ciss(0-0.5 V, Vds 20 V) = {ciss * 1e12:.0f} pF")
        for cur, tstop, step in ((0.1, "300n", "20p"), (1.0, "30n", "2p"), (1.0, "30n", "0.2p")):
            v, q = charge_ramp(model, cur, tstop, step, f"mc_g{len(out['gate_ramp'])}", gate_ramp=True,
                               vds=0.0)
            row = {"model": model, "current_a": cur, "max_step": step, "vds_v": 0.0,
                   "qg_nc_at_1_2p5_5_v": [float(np.interp(x, v, q) * 1e9) for x in (1.0, 2.5, 5.0)]}
            out["gate_ramp"].append(row)
            log(f"  gate ramp {model} {cur} A step {step} (Vds 0): Qg(1, 2.5, 5 V) = "
                + ", ".join(f"{x:.2f}" for x in row["qg_nc_at_1_2p5_5_v"]) + " nC")
    S.save_record(out, "model_check")


def stage_coss(log, temp=60, model=A.DEFAULT_MODEL):
    """Vendor-model output charge Q(V) at Vgs = 0: one device charged by a constant 1 A.

    Coss(V) = dQ/dV feeds the displacement-current correction of the loss
    decomposition. The model's capacitances carry no temperature coefficient
    (TC=0), so one temperature is enough; 25 C is run as a check.
    """
    import numpy as np  # noqa: PLC0415

    result = {"experiment": "A65", "kind": "static_coss", "status": "MEASURED", "model": model,
              "method": f"single {model}, gate held at source (VG=0), 0.1 A into the drain, Q = 0.1 A * t"}
    tables = {}
    for t_c in (temp, 25):
        v, q = charge_ramp(model, 0.1, "750n", "20p", f"coss_T{t_c}", temp=t_c)
        grid = np.arange(0.0, 40.0001, 0.1)
        qg = np.interp(grid, v, q)
        c = np.gradient(qg, grid)
        tables[t_c] = (grid, c, qg)
    grid, c, qg = tables[temp]
    e = np.concatenate([[0.0], np.cumsum(0.5 * (grid[1:] * c[1:] + grid[:-1] * c[:-1]) * np.diff(grid))])
    result.update({"temp_c": temp, "v_grid_v": grid.tolist(), "c_per_device_f": c.tolist(),
                   "q_per_device_c": qg.tolist(), "e_per_device_j": e.tolist(),
                   "check_25c_max_rel_diff": float(np.max(np.abs(tables[25][1] - c) / c)),
                   "q_12v_c": float(np.interp(12, grid, qg)), "e_12v_j": float(np.interp(12, grid, e)),
                   "q_20v_c": float(np.interp(20, grid, qg)), "c_0v_f": float(c[0]),
                   "c_12v_f": float(np.interp(12, grid, c)), "c_20v_f": float(np.interp(20, grid, c))})
    S.save_record(result, "static_epc2067_coss")
    log(f"  coss: C(0)={result['c_0v_f'] * 1e12:.0f} pF C(12)={result['c_12v_f'] * 1e12:.0f} pF "
        f"C(20)={result['c_20v_f'] * 1e12:.0f} pF Q(12)={result['q_12v_c'] * 1e9:.2f} nC "
        f"E(12)={result['e_12v_j'] * 1e9:.1f} nJ Q(20)={result['q_20v_c'] * 1e9:.2f} nC; "
        f"25 C vs 60 C max rel diff {result['check_25c_max_rel_diff']:.1e}")


def stage_repair(a59, case, log):
    """Re-solve NOT_CONVERGED grid points (sweep/centre) with the clamped Ton secant."""
    solved = grid_points(a59["design"], case)
    for rec in records(a59["design"], case):
        if rec.get("kind") not in ("sweep", "center") or rec["status"] == "REGULATED_TO_250W":
            continue
        key = (round(rec["dead_time_rise_s"] * 1e12), round(rec["dead_time_fall_s"] * 1e12))
        if key in solved:
            continue
        # seed from the nearest regulated neighbour (not from the failed orbit)
        near = min(solved.values(), key=lambda r: abs(r["dead_time_rise_s"] - rec["dead_time_rise_s"])
                   + abs(r["dead_time_fall_s"] - rec["dead_time_fall_s"]))
        log(f"repair {rec['_file']} from {near.get('_file')}")
        solve_and_save(a59, case, rec["dead_time_rise_s"], rec["dead_time_fall_s"], seed_of(near),
                       rec["kind"], log, max_chunks=16)
        solved = grid_points(a59["design"], case)


def stage_extend_fall(a59, case, log, steps=4):
    """Declared second pass: d_fall line at the optimum d_rise, walked down while the edge is best."""
    for _ in range(steps):
        best = optimum(a59["design"], case)
        dr = best["dead_time_rise_s"]
        pts = grid_points(a59["design"], case)
        line = sorted((k[1], r) for k, r in pts.items() if k[0] == round(dr * 1e12))
        f_min = line[0][0] * 1e-12
        if best["dead_time_fall_s"] > f_min + 1e-13 or len(line) < 1:
            log(f"  d_fall optimum interior on the r={dr * 1e9:.3f} line")
            return
        nxt = round((f_min - GRID_S) * 1e12) * 1e-12
        if nxt <= S.DT_FLOOR_S:
            return
        failed = [r for r in records(a59["design"], case)
                  if abs(r.get("dead_time_rise_s", 0) - dr) < 1e-13 and abs(r.get("dead_time_fall_s", 0) - nxt) < 1e-13
                  and r.get("status") == "NOT_CONVERGED"]
        if failed:
            log(f"  d_fall {nxt * 1e9:.3f} ns at d_rise {dr * 1e9:.3f} already failed to reach a period-1 "
                f"orbit ({len(failed)} record(s)); extension stops here")
            return
        log(f"  second-pass extension d_fall -> {nxt * 1e9:.3f} ns at d_rise {dr * 1e9:.3f}")
        solve_and_save(a59, case, dr, nxt, seed_of(line[0][1]), "sweep", log, max_chunks=16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True, choices=["zvs", "baseline"])
    ap.add_argument("--stages", required=True)
    ap.add_argument("--case", default="1.0:60")
    ap.add_argument("--files", default="", help="decomp: explicit run records (comma separated)")
    ap.add_argument("--log", default="", help="log file suffix (parallel drivers of one design)")
    args = ap.parse_args()
    a59 = A.load_a59(args.design)
    A.check_variable_names(a59)
    case = parse_case(args.case)
    LOGS.mkdir(exist_ok=True)
    log = log_to(LOGS / f"run_{args.design}{args.log}.txt")
    log(f"=== {args.design} {case.tag} stages={args.stages}")
    for stage in args.stages.split(","):
        if stage == "literal":
            stage_literal(a59, log)
        elif stage == "center":
            stage_center(a59, case, log)
        elif stage == "sweep":
            stage_sweep(a59, case, log)
        elif stage == "transfer":
            stage_transfer(a59, case, log)
        elif stage == "step":
            stage_step(a59, case, log)
        elif stage == "brute":
            stage_brute(a59, log)
        elif stage == "wave":
            stage_wave(a59, case, log)
        elif stage == "decomp":
            stage_decomp(a59, case, log, files=args.files.split(",") if args.files else None)
        elif stage == "static":
            stage_static(log)
        elif stage == "coss":
            stage_coss(log)
        elif stage == "modelcheck":
            stage_modelcheck(log)
        elif stage == "xcheck":
            stage_xcheck(a59, case, log)
        elif stage == "repair":
            stage_repair(a59, case, log)
        elif stage == "extend_fall":
            stage_extend_fall(a59, case, log)
        else:
            raise SystemExit(f"unknown stage {stage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
