"""A144 analysis against BOUNDARY Section 2 -> a144_summary.json. Per run: A143's stats (A142 oracle classes, late
fires, post-step peak), matrix.step_stats, peak V_DS per switch (whole run; steady window 900-1000 us; after the step)
from "vds_win_v", high-side turn-on V_DS in the steady window, and the loop energy 0.5 L i_loop^2 at each high-side
turn-off as power over the steady window. b_<row> runs are compared with A143's records field by field."""
from __future__ import annotations

import importlib.util
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from scb_ivr.cosim.matrix import step_stats

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
spec = importlib.util.spec_from_file_location("a143_analyze", TA / "A143_p24_short_comparator_phase" / "a143_analyze.py")
A143 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A143)
A143C = TA / "A143_p24_short_comparator_phase" / "cosim"
REF = {"n0": "run_g3_s100_n0_k4.json", "l_p48_1us": "run_g4_s100_l_p48_1us_k4.json", "s_p62": "run_g4_s100_s_p62_k4.json"}
S0, S1, T_STEP, V_MAX = 900e-6, 1000e-6, 1000e-6, 40.0
LS = (50, 100, 150, 300)


def vds_windows(d):
    secs = d["sections"]
    def mx(a, b):
        w = [q["vds_win_v"] for q in secs if a <= q["t_s"] < b]
        return np.max(np.array(w), axis=0).round(3).tolist()
    return {"whole": [round(x, 3) for x in d["vds_max_v"]], "steady": mx(S0, S1), "post": mx(T_STEP, 1.0)}


def one(path):
    d = json.loads(Path(path).read_text())
    s = A143.stats(path)
    row = next(r for r in REF if path.stem.endswith(r))
    on = [q["vds_v"] for q in d["turnons_last"] if S0 <= q["t_s"] < S1]
    lp = d.get("loop_params")
    hi = [q for q in d["highoffs_last"] if S0 <= q["t_s"] < S1]
    x = {"name": path.stem[4:], "row": row, "l_ph": lp["l_h"] * 1e12 if lp else 0.0, "rp_ohm": lp["rp_ohm"] if lp else None,
         "status": s["status"], "src_modified": s["src_modified"], "overlaps": s["overlaps"], "late": s["late"],
         "new": s["new"], "classes": s["classes"], "ipk": s["ipk"], "peak_post": s["peak_post"],
         "peak_steady_end": max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= S0 and (row == "n0" or q["t_s"] < T_STEP)),
         "vo_end": s["vo_end"], "vds": vds_windows(d), "on_vds_steady_max": max(on), "on_vds_steady_mean": float(np.mean(on)),
         "i_off_steady_mean": float(np.mean([q["i_a"] for q in hi]))}
    if row != "n0":
        x["step"] = step_stats(d, T_STEP)
    if lp:
        x["i_loop_off_steady_mean"] = float(np.mean([q["i_loop_a"] for q in hi]))
        x["p_loop_w"] = 0.5 * lp["l_h"] * sum(q["i_loop_a"] ** 2 for q in hi) / (S1 - S0)
    return x


def identity(path, row):
    """b_ run vs A143's record: every field but cfg / wall_s / provenance, sections without vds_win_v."""
    a = json.loads(Path(path).read_text()); b = json.loads((A143C / REF[row]).read_text())
    skip = {"cfg", "wall_s", "provenance"}
    for q in a["sections"]:
        q.pop("vds_win_v", None)
    bad = [k for k in b if k not in skip and a.get(k) != b[k]] + [k for k in a if k not in b and k not in skip]
    return {"row": row, "identical": not bad, "differs": bad}


def main():
    paths = sorted(COS.glob("run_*.json"))
    with Pool(6) as p:
        runs = {r["name"]: r for r in p.map(one, paths)}
    ids = [identity(COS / f"run_b_{r}.json", r) for r in REF if (COS / f"run_b_{r}.json").exists()]
    crit = {"1_identity": all(i["identical"] for i in ids) and len(ids) == 3, "identity": ids, "per_l": {}}
    for l in LS:
        v_ok, c_ok, why = True, True, []
        for r in REF:
            q, b = runs.get(f"q7_l{l}_{r}"), runs.get(f"b_{r}")
            if not q or not b:
                v_ok = c_ok = None; break
            if max(q["vds"]["whole"]) > V_MAX:
                v_ok = False; why.append(f"{r} V {max(q['vds']['whole']):.1f}")
            pk = (q["peak_post"], b["peak_post"]) if r != "n0" else (q["peak_steady_end"], b["peak_steady_end"])
            checks = {"a": q["status"] == "COMPLETED" and q["overlaps"] == 0, "b": q["late"] <= b["late"] + 5,
                      "c": q["on_vds_steady_max"] <= b["on_vds_steady_max"] + 1.0, "d_peak": pk[0] <= pk[1] + 10.0,
                      "d_vo": (np.isfinite(q["step"]["back_within_1pct_us"]) if r != "n0" else abs(q["vo_end"] - 1) < 0.01),
                      "e": q["new"] <= b["new"]}
            bad = [k for k, ok in checks.items() if not ok]
            if bad:
                c_ok = False; why.append(f"{r} " + ",".join(bad))
        crit["per_l"][l] = {"voltage": v_ok, "controller": c_ok, "why": why}
    lv = [l for l in LS if crit["per_l"][l]["voltage"]]
    lc = [l for l in LS if crit["per_l"][l]["controller"]]
    crit["L_V"] = max(lv) if lv else None
    crit["L_C"] = max(lc) if lc else None
    out = {"runs": runs, "criteria": crit}
    (HERE / "a144_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    print("identity:", [(i["row"], i["identical"], i["differs"]) for i in ids])
    def pk(q):
        return q["peak_post"] if q["peak_post"] is not None else q["peak_steady_end"]
    cols = {"Vmax": lambda q: f"{max(q['vds']['whole']):.1f}", "SH1 post": lambda q: f"{q['vds']['post'][0]:.1f}",
            "on-V": lambda q: f"{q['on_vds_steady_max']:.2f}", "late/new": lambda q: f"{q['late']}/{q['new']}",
            "pk": lambda q: f"{pk(q):.1f}", "P_loop": lambda q: f"{q.get('p_loop_w', 0.0):.1f}"}
    print("per row: b, then Q 7 at " + " / ".join(map(str, LS)) + " pH")
    for r in REF:                                                 # two lines per row
        qs = [runs.get(f"b_{r}")] + [runs.get(f"q7_l{l}_{r}") for l in LS]
        part = {k: " ".join("-" if q is None else fn(q) for q in qs) for k, fn in cols.items()}
        print(f"{r:9s} " + " | ".join(f"{k} {part[k]}" for k in ("Vmax", "SH1 post", "on-V")))
        print(f"{'':9s} " + " | ".join(f"{k} {part[k]}" for k in ("late/new", "pk", "P_loop")))
    for l in (150, 300):
        u = runs.get(f"u_l{l}_l_p48_1us")
        if u:
            print(f"undamped {l} pH l_p48_1us: Vmax {max(u['vds']['whole']):.1f} SH1 post {u['vds']['post'][0]:.1f} on-V "
                  f"{u['on_vds_steady_max']:.2f} late {u['late']} new {u['new']} pk {u['peak_post']:.1f}")
    print("per L:", {l: (v["voltage"], v["controller"]) for l, v in crit["per_l"].items()}, "L_V", crit["L_V"], "L_C", crit["L_C"])


if __name__ == "__main__":
    main()
