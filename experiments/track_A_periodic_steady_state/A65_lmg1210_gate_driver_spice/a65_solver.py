"""A65 (copy of A64) - periodic steady state, 250 W regulation and channel-referenced timing in LTspice.

One *chunk* = one LTspice run of n periods from a given state. The first
chunk of a design/case starts from A59's regulated z* at tau = 0 (A52
transcription). Every later chunk is a warm restart at a quiet instant
(tau = QUIET_S) from a state of 13 node voltages and 5 inductor currents,
passed as DC-constrained `.ic` (the vendor devices' internal nodes and the
gates are solved consistently by LTspice's operating point).

Acceptance of a point (BOUNDARY Section 3, all on the LAST simulated period of
a chunk that ran >= n_chunk plain periods from its start state):
  * converged  : relative cycle-to-cycle change of every capacitor voltage and
                 inductor current < 1e-3;
  * regulated  : |mean(Vout^2/R)/250 W - 1| < 1e-3;
  * loss stable: |P_loss_corr(last) - P_loss_corr(previous period)| < 0.005 W
                 (PROJECT_DECISION, stricter than the BOUNDARY, so the loss
                 figure itself is settled; see TOL_PLOSS_W).

Acceleration (NUMERICAL_IDEALIZATION, an initial-guess device only): the
circuit has slow modes (output L-Cout, flying-capacitor/phase-current
exchange) that take tens of periods to decay. Between chunks the start state
of the next chunk is the reduced-rank-extrapolation (RRE; Skelboe 1980,
"Computation of the periodic steady-state response of nonlinear networks by
extrapolation methods") estimate of the period map's fixed point from the
chunk's quiet samples. Ton_cmd is updated by a secant on the power that the
extrapolated orbit would deliver. The accepted period is always an ordinary
simulated period that passes the three tests above, so the extrapolation
cannot enter a result; `run_a65.py --stages brute` checks it against a plain
un-accelerated run.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

import a65_analysis as Y
import a65_ltspice as L
import a65_netlist as A

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
TOL_REL = 1e-3
TOL_P = 1e-3
#: loss-stable test: per-period change of P_loss_corr (PROJECT_DECISION). The
#: slowest mode decays by r ~ 0.87-0.92 per period (plain 80-period runs), so
#: the remaining drift is ~ step * r/(1-r) ~ 10x this; it is reported as
#: `p_loss_tail_estimate_w` for every accepted point.
TOL_PLOSS_W = 0.005
#: Ton is re-aimed while the extrapolated power is off by more than this
#: (the acceptance tolerance stays the BOUNDARY's 1e-3)
TON_AIM = 3e-4
#: samples skipped after a restart before RRE (fast transients of a changed Ton)
RRE_SKIP = 4
#: clamp of the Ton secant slope dP/dTon (W/s). Added after the first sweep:
#: three baseline points (f3.35, f2.85, r4.55) ended NOT_CONVERGED because a
#: noise-driven slope of ~3 W/ns made Ton oscillate by +/-0.3 ns. Those points
#: were re-solved with the clamp (records with `_v2`).
SLOPE_MIN = 10.0 / 1e-9
SLOPE_MAX = 60.0 / 1e-9
P_TARGET_W = 250.0
DEFAULT_MAXSTEP_S = 50e-12
DEFAULT_RELTOL = 1e-4
STATE_KEYS = A.NODE_STATES + tuple(A.INDUCTOR_STATES)


def chunk(a59, case, ton, dr, df, state, origin, n, *, maxstep, reltol, tag,
          save_all_gates=False, keep_raw=False, extra_options="", model=A.DEFAULT_MODEL):
    spec = A.NetlistSpec(design=a59["design"], case=case, ton_s=ton, dr_s=dr, df_s=df,
                         n_periods=n, max_step_s=maxstep, ic=state, origin_s=origin,
                         reltol=reltol, save_all_gates=save_all_gates, extra_options=extra_options,
                         model=model)
    text, meta = A.build(spec, a59)
    run = L.run(text, tag)
    if not run["raw_path"].exists() or run["raw_path"].stat().st_size == 0:
        raise RuntimeError(f"no raw for {tag}: {run['log_text'][-800:]}")
    d = L.load_raw(run["raw_path"])
    if d["time"][-1] < meta["sample_times_s"][-1] * (1 - 1e-9):
        raise RuntimeError(f"{tag}: simulation stopped at {d['time'][-1]:.4e} s: {run['log_text'][-800:]}")
    res = Y.analyze(d, meta, a59)
    sym = symmetry_check(d) if save_all_gates else None
    if not keep_raw:
        for suffix in (".raw", ".op.raw"):
            p = run["raw_path"].with_suffix(suffix)
            if p.exists():
                p.unlink()
    warnings = [ln for ln in run["log_text"].splitlines()
                if any(w in ln.lower() for w in ("warning", "error", "singular", "too small",
                                                 "not found"))]
    return {
        "netlist_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "ton_cmd_s": ton, "dead_time_rise_s": dr, "dead_time_fall_s": df,
        "origin_s": origin, "n_periods": n, "max_step_s": maxstep, "reltol": reltol, "model": model,
        "extra_options": extra_options,
        "initial_state": {k: state[k] for k in STATE_KEYS},
        "wall_s": run["wall_s"], "points": int(len(d["time"])),
        "ltspice_meas": run["meas"], "ltspice_failed_meas": run["failed"], "log_warnings": warnings,
        "periods": res["periods"], "last": res["last"],
        "samples": res["samples"],
        "final_state": res["samples"][-1],
        "symmetry": sym,
        "gates": meta["gates"],
    }


def symmetry_check(d):
    """Max |difference| between parallel devices' gate currents (all devices saved)."""
    worst = 0.0
    for side, count in (("H", A.NHS), ("L", A.NLS)):
        for p in range(1, 5):
            ref = d[f"I(V_G{side}{p}A)"]
            for letter in "BC"[:count - 1]:
                worst = max(worst, float(np.max(np.abs(d[f"I(V_G{side}{p}{letter})"] - ref))))
    return {"max_gate_current_difference_a": worst}


def accepted(ch):
    last, prev = ch["periods"][-1], ch["periods"][-2]
    perr = last["p_out_w"] / P_TARGET_W - 1
    return {
        "rel_change": last["rel_change"],
        "power_relative_error": perr,
        "p_loss_corr_step_w": last["p_loss_corr_w"] - prev["p_loss_corr_w"],
        "converged": last["rel_change"] < TOL_REL,
        "regulated": abs(perr) < TOL_P,
        "loss_stable": abs(last["p_loss_corr_w"] - prev["p_loss_corr_w"]) < TOL_PLOSS_W,
    }


def _scale(x):
    out = []
    for k, v in zip(STATE_KEYS, x):
        floor = 1.0 if k in A.INDUCTOR_STATES else 0.1
        out.append(max(abs(v), floor))
    return np.array(out)


def rre(samples, skip=0):
    """Reduced-rank extrapolation of the fixed point from quiet samples x_0..x_m."""
    X = np.array([[s[k] for k in STATE_KEYS] for s in samples[skip:]])
    scale = _scale(X[-1])
    Y_ = X / scale
    U = np.diff(Y_, axis=0)
    m = U.shape[0]
    # min || sum_i gamma_i u_i ||  s.t. sum_i gamma_i = 1, with gamma_0 eliminated
    # (minimum-norm least squares, robust when the differences are rank deficient)
    D = (U[1:] - U[0]).T
    g_rest = np.linalg.lstsq(D, -U[0], rcond=1e-12)[0]
    gamma = np.concatenate([[1.0 - g_rest.sum()], g_rest])
    s = gamma @ Y_[:m]
    x = s * scale
    step = np.linalg.norm((x - X[-1]) / scale)
    last_step = np.linalg.norm(U[-1])
    return dict(zip(STATE_KEYS, x.tolist())), float(step), float(last_step)


def comp_update(hist, i_cmd, i_meas, target, max_step=1.0e-9):
    """Next command dead time so the measured channel dead time hits target."""
    cmd, meas = hist[-1][i_cmd], hist[-1][i_meas]
    gain = 0.5
    if len(hist) >= 2:
        c0, m0 = hist[-2][i_cmd], hist[-2][i_meas]
        if abs(cmd - c0) > 1e-12:
            slope = (meas - m0) / (cmd - c0)
            if 0.3 < slope < 5.0:
                gain = 1.0 / slope
    step = max(-max_step, min(max_step, gain * (target - meas)))
    return max(0.05e-9, cmd + step)


def power_estimate(ch, state):
    """Power the extrapolated orbit would deliver: last period's P_out scaled by Vout^2."""
    last = ch["periods"][-1]
    ratio = state["out"] / ch["final_state"]["out"]
    return last["p_out_w"] * ratio ** 2


def solve(a59, case, dr, df, ton0, state0, origin0, *, tag, log=print,
          maxstep=DEFAULT_MAXSTEP_S, reltol=DEFAULT_RELTOL, n_first=20, n_chunk=16,
          max_chunks=14, slope_w_per_s=27.0 / 1e-9, compensate_to=None, comp_tol_s=0.03e-9,
          comp_only=True,
          extrapolate=True, save_all_gates_final=False, extra_options="", max_ton_step_s=0.4e-9,
          model=A.DEFAULT_MODEL):
    """Regulate one command timing (dr, df) to an accepted 250 W periodic state.

    compensate_to=(target_rise_s, target_fall_s): additionally move dr/df
    (secant per edge type) until the MEAN channel dead times over the four
    phases equal the targets -- used only to locate the channel-referenced
    sweep centre.
    """
    ton, state, origin = ton0, dict(state0), origin0
    history, chunks, comp_hist = [], [], []
    slope = slope_w_per_s
    started = time.time()
    status = "NOT_CONVERGED"
    use_rre = extrapolate
    for c in range(max_chunks):
        n = n_first if (c == 0 and origin == 0.0) else n_chunk
        ch = chunk(a59, case, ton, dr, df, state, origin, n, maxstep=maxstep, reltol=reltol,
                   tag=f"{tag}_c{c}", extra_options=extra_options, model=model)
        ch["acceptance"] = accepted(ch)
        summ = Y.channel_summary(ch["last"]["edges"])
        ch["channel_summary"] = summ
        chunks.append(ch)
        last = ch["periods"][-1]
        acc = ch["acceptance"]
        comp_ok, er, ef = True, 0.0, 0.0
        if compensate_to is not None:
            er = compensate_to[0] - (summ["rise"]["channel_dead_time_mean_s"] or 0.0)
            ef = compensate_to[1] - (summ["fall"]["channel_dead_time_mean_s"] or 0.0)
            comp_ok = abs(er) < comp_tol_s and abs(ef) < comp_tol_s
        log(f"  [{tag} c{c}] Ton={ton * 1e9:.4f} dr={dr * 1e9:.3f} df={df * 1e9:.3f} n={n} "
            f"Pout={last['p_out_w']:.3f} Pcorr={last['p_loss_corr_w']:.3f} "
            f"dPc={acc['p_loss_corr_step_w']:+.3f} dE/T={last['stored_energy_rate_w']:.2f} "
            f"rel={last['rel_change']:.2e}({last['rel_change_worst']}) "
            f"cdt r/f={fmt_ns(summ['rise']['channel_dead_time_mean_s'])}/"
            f"{fmt_ns(summ['fall']['channel_dead_time_mean_s'])} wall={ch['wall_s']:.0f}s")
        if acc["converged"] and acc["regulated"] and acc["loss_stable"] and comp_ok:
            status = "REGULATED_TO_250W"
            break
        if (compensate_to is not None and comp_only and comp_ok and last["rel_change"] < 1e-2
                and abs(acc["power_relative_error"]) < 1e-2):
            status = "CHANNEL_MATCHED"  # locating the sweep centre only; not an accepted point
            break
        # --- next start state: RRE fixed-point estimate (or the last sample)
        nxt = dict(ch["final_state"])
        info = {"used": False}
        if use_rre and len(ch["samples"]) >= RRE_SKIP + 6:
            try:
                est, step, last_step = rre(ch["samples"], skip=RRE_SKIP)
                sane = (np.isfinite(list(est.values())).all() and step < 60 * max(last_step, 1e-9)
                        and max(abs(est[k]) for k in A.INDUCTOR_STATES) < 400)
                info = {"used": bool(sane), "step_norm": step, "last_diff_norm": last_step}
                if sane:
                    nxt = est
            except np.linalg.LinAlgError:
                info = {"used": False, "error": "lstsq"}
        # if the previous extrapolation made the first period worse, stop extrapolating
        if len(chunks) >= 2 and chunks[-2].get("extrapolation", {}).get("used"):
            if ch["periods"][0]["rel_change"] > 3 * chunks[-2]["periods"][-1]["rel_change"]:
                use_rre = False
                info["disabled_after_worse_start"] = True
        ch["extrapolation"] = info
        # --- Ton: secant on the power the (extrapolated) orbit would deliver
        p_est = power_estimate(ch, nxt)
        history.append((ton, p_est))
        if len(history) >= 2:
            (t0, p0), (t1, p1) = history[-2], history[-1]
            if abs(t1 - t0) > 1e-15 and (p1 - p0) / (t1 - t0) > 0:
                slope = (p1 - p0) / (t1 - t0)
        # the secant slope from un-settled chunks can be noise; the measured
        # dP/dTon is 15-30 W/ns, so clamp (first runs oscillated with ~3 W/ns)
        slope = min(SLOPE_MAX, max(SLOPE_MIN, slope))
        if abs(p_est / P_TARGET_W - 1) > TON_AIM:
            step = (P_TARGET_W - p_est) / slope
            if not info.get("used") and last["rel_change"] > 5e-3:
                step *= 0.5  # transient-dominated estimate: damp
            ton = ton + max(-max_ton_step_s, min(max_ton_step_s, step))
        if compensate_to is not None and not comp_ok:
            # channel dead time vs command dead time is not slope 1 (measured ~2 on
            # the large-ripple rise edge), so a secant per edge type, damped
            # fixed point (gain 0.5) until two points exist
            comp_hist.append((dr, df, compensate_to[0] - er, compensate_to[1] - ef))
            dr = comp_update(comp_hist, 0, 2, compensate_to[0])
            df = comp_update(comp_hist, 1, 3, compensate_to[1])
            history.clear()  # the Ton/P relation moves with the dead times
        state, origin = nxt, A.QUIET_S
    final = chunks[-1]
    if save_all_gates_final and status == "REGULATED_TO_250W":
        sym = chunk(a59, case, final["ton_cmd_s"], final["dead_time_rise_s"], final["dead_time_fall_s"],
                    final["final_state"], A.QUIET_S, 2, maxstep=maxstep, reltol=reltol,
                    tag=f"{tag}_sym", save_all_gates=True, extra_options=extra_options, model=model)
        final["symmetry"] = sym["symmetry"]
    return {
        "status": status,
        "design": a59["design"],
        "model": model,
        "case": case.as_dict(),
        "ton_cmd_s": final["ton_cmd_s"],
        "dead_time_rise_s": final["dead_time_rise_s"],
        "dead_time_fall_s": final["dead_time_fall_s"],
        "periods_total": int(sum(ch["n_periods"] for ch in chunks)),
        "chunks_total": len(chunks),
        "final_chunk_plain_periods": final["n_periods"],
        "chunks": [slim(ch) for ch in chunks],
        "final": summarize(final),
        "wall_s": time.time() - started,
        "slope_w_per_s": slope,
    }


def slim(ch):
    """Chunk record without the bulky per-edge detail (kept only for the final chunk)."""
    out = {k: v for k, v in ch.items() if k not in ("last", "gates", "samples")}
    out["samples"] = ch["samples"]
    out["last_summary"] = {k: ch["last"][k] for k in ("p_rsrc_w", "p_rlind_w", "p_switch_sum_w",
                                                      "p_gate_total_w")}
    return out


def fmt_ns(v):
    return "nan" if v is None else f"{v * 1e9:.3f}"


def tail_estimate(periods, n=6):
    """Geometric estimate of the P_loss_corr drift still to come after the last period."""
    p = [q["p_loss_corr_w"] for q in periods[-n:]]
    d = np.diff(p)
    ratios = [d[i] / d[i - 1] for i in range(1, len(d)) if abs(d[i - 1]) > 1e-9]
    r = float(np.clip(np.median(ratios), 0.0, 0.98)) if ratios else 0.9
    return {"ratio": r, "tail_w": float(d[-1] * r / (1 - r)) if len(d) else 0.0}


def summarize(ch):
    last = ch["periods"][-1]
    lp = ch["last"]
    passive = lp["p_rsrc_w"] + lp["p_rlind_w"]
    tail = tail_estimate(ch["periods"])
    return {
        "p_loss_tail_estimate_w": tail["tail_w"], "p_loss_tail_ratio": tail["ratio"],
        "decomposition": lp.get("decomposition"),
        "state_decomposition": lp.get("state_decomposition"),
        "p_in_w": last["p_in_w"], "p_out_w": last["p_out_w"],
        "p_loss_w": last["p_loss_w"], "p_loss_corr_w": last["p_loss_corr_w"],
        "stored_energy_rate_w": last["stored_energy_rate_w"],
        "ltspice_meas_p_loss_w": ((ch["ltspice_meas"].get("ein", float("nan"))
                                   - ch["ltspice_meas"].get("eout", float("nan"))) / A.PERIOD_S),
        "p_passive_resistive_w": passive,
        "p_device_w": last["p_loss_corr_w"] - passive,
        "p_switch_sum_w": lp["p_switch_sum_w"],
        "closure_w": last["p_loss_corr_w"] - passive - lp["p_switch_sum_w"],
        "p_gate_total_w": lp["p_gate_total_w"],
        "p_total_with_gate_w": last["p_loss_corr_w"] + lp["p_gate_total_w"],
        "rel_change": last["rel_change"], "rel_change_worst": last["rel_change_worst"],
        "power_relative_error": last["p_out_w"] / P_TARGET_W - 1,
        "max_abs_phase_current_a": last["max_abs_phase_current_a"],
        "channel_summary": ch["channel_summary"],
        "edges": lp["edges"],
        "switch_groups_w": lp["p_switch_groups_w"],
        "gate": lp["gate"],
        "final_state": ch["final_state"],
        "symmetry": ch.get("symmetry"),
        "gates": ch["gates"],
        "acceptance": ch["acceptance"],
        "log_warnings": ch["log_warnings"],
        "points_in_final_chunk": ch["points"],
    }


def save_record(record, name):
    RUNS.mkdir(exist_ok=True)
    path = RUNS / f"{name}.json"
    k = 2
    while path.exists():  # never overwrite
        path = RUNS / f"{name}_v{k}.json"
        k += 1
    path.write_text(json.dumps(record, indent=1, default=float))
    return path


def point_name(design, case, dr, df, suffix=""):
    return f"{design}_{case.tag}_r{dr * 1e9:.3f}_f{df * 1e9:.3f}{suffix}"


__all__ = ["solve", "chunk", "save_record", "point_name", "summarize", "accepted", "rre",
           "TOL_REL", "TOL_P", "TOL_PLOSS_W", "P_TARGET_W", "STATE_KEYS"]
