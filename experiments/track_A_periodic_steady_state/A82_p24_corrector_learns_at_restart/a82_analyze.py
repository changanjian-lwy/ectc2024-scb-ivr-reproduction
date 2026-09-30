"""A82 analysis (copied from A79's). Original docstring:
A78 analysis (copied from A76's): regression gate against A76 run 1, and the negative-current target sweep with
conduction loss (BOUNDARY Section 6).

Reads run_*.json written by a78_transient.py; writes a78_summary.json.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LAST = 50  # cycles for the turn-on statistics
PER = 20   # sections for the periodicity test


def load(path):
    return json.loads(Path(path).read_text())


def gate(ref_path, new_path):
    ref, new = load(ref_path), load(new_path)
    a, b = ref["sections"], new["sections"]
    same_count = len(a) == len(b) and ref["sections_total"] == new["sections_total"]
    dv = max(abs(x - y) for s, r in zip(a, b) for x, y in zip(s["v"] + s["i"], r["v"] + r["i"]))
    dt = max(abs(s["t_s"] - r["t_s"]) for s, r in zip(a, b))
    out = {"reference": str(Path(ref_path).relative_to(HERE.parent)), "candidate": Path(new_path).name,
           "sections_ref": ref["sections_total"], "sections_new": new["sections_total"],
           "max_abs_diff_v_i": dv, "max_abs_diff_t_s": dt,
           "end_y_equal": ref["end"]["y"] == new["end"]["y"],
           "pass": bool(same_count and dv == 0.0 and dt == 0.0 and ref["end"]["y"] == new["end"]["y"])}
    return out


def summarize(path):
    d = load(path); e = d["end"]; secs = d["sections"]; n = len(secs[-1]["i"]); pr = d["params"]
    tot = d["sections_total"] - 1
    last = secs[-(PER + 1):]
    per = np.diff([s["t_s"] for s in last])
    di = max(abs(x - y) for s in last for x, y in zip(s["i"], last[-1]["i"]))
    dvo = max(abs(s["vo"] - last[-1]["vo"]) for s in last)
    s = secs[-1]
    ton = [t for t in e["turnons_last"] if t["cycle"] >= tot - LAST and t["mode"] == "P"]
    cyc = len({t["cycle"] for t in ton}) or 1
    how = {k: dict(Counter(t["how"] for t in ton if t["phase"] == k)) for k in range(1, n + 1)}
    vds = {k: [t["vds_v"] for t in ton if t["phase"] == k] for k in range(1, n + 1)}
    lo = [t for t in e.get("lowoffs_last", []) if t["cycle"] >= tot - LAST and t["mode"] == "P"]
    lo_i = {k: [t["i_a"] for t in lo if t["phase"] == k] for k in range(1, n + 1)}
    c_node = pr["c_high"] + pr["c_low"]
    f_sw = 1.0 / float(np.mean(per)) if len(per) else float("nan")
    e_on = sum(0.5 * c_node * v ** 2 for t in ton for v in [t["vds_v"]]) / cyc   # J per cycle, all phases
    return {
        "case": d["case"], "t_d_ns": pr["t_d"] * 1e9, "valley_mode": pr["valley_mode"], "status": e["status"],
        "periodic": bool(di < 1e-3 and dvo < 1e-4), "last20_max_di_a": di, "last20_max_dvo_v": dvo,
        "period_ns": float(np.mean(per) * 1e9), "vo_v": s["vo"],
        "ladder_ratio": [v / s["vin_v"] for v in s["vcs_v"]], "section_i_a": s["i"],
        "turnon_how_last50": how,
        "turnon_vds_mean_max_last50": {k: [float(np.mean(v)), float(np.max(v))] if v else None for k, v in vds.items()},
        "delayed_edges_last50": sum(1 for t in ton if t.get("delayed")),
        "lowoff_edge_i_mean_min_max_last50": {k: [float(np.mean(v)), float(np.min(v)), float(np.max(v))] if v else None
                                              for k, v in lo_i.items()},
        "restarts_last50": sum(1 for t in ton if t["how"] == "high_restart"),
        "turnon_loss_proxy_w": e_on * f_sw, "turnon_energy_proxy_uj_per_cycle": e_on * 1e6,
        "vds_max_v": max(e["vds_max_v"].values()), "ipk_a": max(x["ipk_a"] for x in secs),
        "dt_pred_ns": [x * 1e9 for x in e["dt_pred_s"]], "half_res_ns": e["half_res_s"] * 1e9,
        "pred_stats": e["pred_stats"], "latent_detections": e["latent_detections"],
        "restart_count_total": e["restart_count"], "diode_cuts": e["diode_cuts"],
        "theta_final_a": e.get("theta_final_a"), "trims": e.get("trims"),
        "lowoff_bind_last50": {k: dict(Counter(t.get("bind") for t in lo if t["phase"] == k)) for k in range(1, n + 1)},
        # single-module criterion 2 (A76 RESULTS Section 1): every phase turns on once per cycle, softly,
        # with no restart, peak Vds below EPC2067's 40 V, and at most a < 1 A dither over the last 20 sections
        "turnons_per_phase_last50": {k: sum(h.values()) for k, h in how.items()},
        "pass_all_soft_no_restart": bool(
            all(set(h) <= {"high_pred", "high_valley", "high_zvs"} and LAST - 1 <= sum(h.values()) <= LAST + 2
                for h in how.values())
            and max(e["vds_max_v"].values()) < 40.0 and di < 1.0),
        "trim_gain": pr.get("trim_gain"), "qualify_current": pr.get("qualify_current"), "zvs_reactive": pr.get("zvs_reactive"),
        "i_target_a": pr["i_target"], **loss(secs, ton, pr, per, s), **vloop(d, secs),
    }


def loss(secs, ton, pr, per, s):
    """Conduction loss from the per-section integral of i^2 dt (R per phase), a turn-on proxy (1/2 C_node Vds^2 f)
    and the output power, over the last LAST sections (BOUNDARY Section 6)."""
    n = len(s["i"]); last = [x for x in secs[-LAST:] if x.get("i2_int_a2s")]
    t_sec = float(np.mean(per)) if len(per) else float("nan")
    i2 = np.mean([x["i2_int_a2s"] for x in last], axis=0) if last else np.full(n, np.nan)
    irms = np.sqrt(i2 / t_sec)
    p_cond = float(pr["R"] * np.sum(i2) / t_sec)
    c_node = [pr["c_low"] + (2 if k < n - 1 else 1) * pr["c_high"] for k in range(n)]
    cyc = len({t["cycle"] for t in ton}) or 1
    e_on = sum(0.5 * c_node[t["phase"] - 1] * t["vds_v"] ** 2 for t in ton) / cyc
    p_out = s["vo"] ** 2 / pr["r_load"]
    return {"irms_a": irms.tolist(), "p_cond_w": p_cond, "p_on_proxy_w": e_on / t_sec, "p_out_w": p_out,
            "loss_share_cond_plus_on_proxy": (p_cond + e_on / t_sec) / p_out}


def vloop(d, secs):
    """Voltage-loop metrics: time after the handover until Vo stays within 1% of vref, final Ton, Vo ripple."""
    pr = d["params"]; th = d["end"]["t_hand_actual_s"] or 0.0; vref = pr.get("vref", 1.0)
    after = [x for x in secs if x["t_s"] >= th]
    t_in = None
    for x in reversed(after):
        if abs(x["vo"] - vref) > 0.01 * vref:
            break
        t_in = x["t_s"]
    last = secs[-(PER + 1):]
    return {"ki_ns_per_v": pr.get("vo_loop_ki", 0.0) * 1e9, "vref_v": vref,
            "settle_1pct_us_after_handover": None if t_in is None else (t_in - th) * 1e6,
            "ton_final_ns": secs[-1].get("ton_cmd_ns"), "vo_ripple_last20_mv": 1e3 * float(np.ptp([x["vo"] for x in last]))}


def main():
    runs = sorted(HERE.glob("run_*.json"))
    rows = {p.stem[4:]: summarize(p) for p in runs}
    gates = {}
    for cand, ref in json.loads((HERE / "gate_pairs.json").read_text()).items():
        if (HERE / f"run_{cand}.json").exists():
            gates[cand] = gate(HERE.parent / ref, HERE / f"run_{cand}.json")
            print("gate", cand, gates[cand])
    for k, r in rows.items():
        print(f"{k:28s} {r['status']:9s} periodic {r['periodic']} T {r['period_ns']:.3f} ns Vo {r['vo_v']:.4f} "
              f"i {np.round(r['section_i_a'], 1)} Vdsmax {r['vds_max_v']:.1f} ipk {r['ipk_a']:.0f} "
              f"restarts(last50) {r['restarts_last50']} PASS {r['pass_all_soft_no_restart']} i_tgt {r['i_target_a']} "
              f"Pcond {r['p_cond_w']:.2f} W Pout {r['p_out_w']:.1f} W ki {r['ki_ns_per_v']} settle1% {r['settle_1pct_us_after_handover']} us "
              f"Ton {r['ton_final_ns']} ns ripple {r['vo_ripple_last20_mv']:.3f} mV")
        print(f"     last20 max di {r['last20_max_di_a']:.3g} A, max dVo {r['last20_max_dvo_v']:.3g} V")
        for ph, h in r["turnon_how_last50"].items():
            print(f"     phase {ph}: {h}  Vds at edge mean/max {np.round(r['turnon_vds_mean_max_last50'][ph], 2)}"
                  f"  low-off edge i mean/min/max {np.round(r['lowoff_edge_i_mean_min_max_last50'][ph], 2)} bind {r['lowoff_bind_last50'][ph]}")
    (HERE / "a82_summary.json").write_text(json.dumps({"gates": gates, "runs": rows}, indent=1))
    return 0 if all(g["pass"] for g in gates.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
