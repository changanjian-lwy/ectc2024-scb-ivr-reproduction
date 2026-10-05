"""A145 analysis against BOUNDARY Section 2 -> a145_summary.json. Per run: A144's one() (A143 stats, V_DS windows,
turn-on V_DS, turn-off currents), the edge statistics, the edge power over the steady window (900-1000 us) and the
high-side turn-off rate there. id_ runs are compared with A144's records field by field. The loop-dependent loss
P_L = [edge(L) - edge(0)] + damper uses the harness (a145_edge.json) damper energy per 143 A turn-off, scaled by the
run's turn-off rate and (i_loop_off / 143)^2. Prints <= 15 lines."""
from __future__ import annotations

import importlib.util
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
A144D = TA / "A144_p24_commutation_loop_inductance"
spec = importlib.util.spec_from_file_location("a144_analyze", A144D / "a144_analyze.py")
A144 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A144)
ROWS, LS, DIDT = ("n0", "l_p48_1us", "s_p62"), (50, 100, 150), (144, 72)
S0, S1, V_MAX, P_1PCT = A144.S0, A144.S1, 40.0, 2.5


def one(path):
    x = A144.one(path)
    d = json.loads(Path(path).read_text())
    x["steps"], x["wall_s"] = d["steps"], d["wall_s"]
    st = d.get("edge_stats")
    if st:
        secs = d["sections"]
        k = [i for i, q in enumerate(secs) if S0 < q["t_s"] <= S1]
        e = np.sum([secs[i]["edge_energy_j"] for i in k], axis=0)
        dt = secs[k[-1]]["t_s"] - secs[k[0] - 1]["t_s"]
        x["edge"] = {"p_w": float(e.sum() / dt), "p_sw_w": (e / dt).round(4).tolist(), "steps_frac": st["steps"] / d["steps"],
                     "off": st["off"], "on": st["on"], "off_neg_steps": st["off_neg_steps"], "on_vds_max_v": st["on_vds_max_v"],
                     "on_t_max_ns": st["on_t_max_s"] * 1e9, "on_i_max_a": st["on_i_max_a"], "on_forced": st["on_forced"],
                     "e_run_j": float(sum(st["e_total_j"]))}
    hi = [q for q in d["highoffs_last"] if S0 <= q["t_s"] < S1]
    x["off_rate_hz"] = len(hi) / (S1 - S0)
    return x


def identity(name):
    a = json.loads((COS / f"run_id_{name}.json").read_text()); b = json.loads((A144D / "cosim" / f"run_{name}.json").read_text())
    skip = {"cfg", "wall_s", "provenance"}
    bad = [k for k in b if k not in skip and a.get(k) != b[k]] + [k for k in a if k not in b and k not in skip]
    return {"run": name, "identical": not bad, "differs": bad, "src_modified": a["provenance"].get("cosim_sources_modified")}


def ctl_checks(q, b, row):
    """A144's controller checks of run q against reference b."""
    pk = (q["peak_post"], b["peak_post"]) if row != "n0" else (q["peak_steady_end"], b["peak_steady_end"])
    c = {"a": q["status"] == "COMPLETED" and q["overlaps"] == 0, "b": q["late"] <= b["late"] + 5,
         "c": q["on_vds_steady_max"] <= b["on_vds_steady_max"] + 1.0, "d_peak": pk[0] <= pk[1] + 10.0,
         "d_vo": (bool(np.isfinite(q["step"]["back_within_1pct_us"])) if row != "n0" else abs(q["vo_end"] - 1) < 0.01),
         "e": q["new"] <= b["new"]}
    return [k for k, ok in c.items() if not ok], pk[0] - pk[1]


def main():
    paths = sorted(COS.glob("run_*.json"))
    with Pool(6) as p:
        runs = {r["name"]: r for r in p.map(one, paths)}
    ref = json.loads((A144D / "a144_summary.json").read_text())["runs"]
    harness = json.loads((HERE / "a145_edge.json").read_text())
    def e_loop(l, d):
        return next(r["e_loop_nj"] for r in harness["off"] if r["l_ph"] == l and r["q"] == 7 and r["i0"] == 143.0
                    and r["didt_a_ns"] == d) * 1e-9
    ids = [identity(n) for n in ("q7_l100_l_p48_1us", "q7_l50_n0") if (COS / f"run_id_{n}.json").exists()]
    out = {"runs": runs, "identity": ids, "per": {}}
    for d in DIDT:
        p0 = runs[f"e{d}_l0_n0"]["edge"]["p_w"] if f"e{d}_l0_n0" in runs else None
        c0, _ = ctl_checks(runs[f"e{d}_l0_n0"], ref["b_n0"], "n0") if f"e{d}_l0_n0" in runs else (None, None)
        out["per"][f"{d}_l0"] = {"edge_p_w": p0, "controller_bad": c0}
        for l in LS:
            names = [f"e{d}_l{l}_{r}" for r in ROWS]
            if not all(n in runs for n in names):
                continue
            v = {r: max(runs[f"e{d}_l{l}_{r}"]["vds"]["whole"]) for r in ROWS}
            bad, dpk = {}, {}
            for r in ROWS:
                bad[r], dpk[r] = ctl_checks(runs[f"e{d}_l{l}_{r}"], ref[f"q7_l{l}_{r}"], r)
            n0 = runs[f"e{d}_l{l}_n0"]
            sc = (n0["i_loop_off_steady_mean"] / 143.0) ** 2 * n0["off_rate_hz"]
            damper = e_loop(l, d) * sc
            out["per"][f"{d}_l{l}"] = {
                "vds_whole": v, "voltage_ok": max(v.values()) <= V_MAX, "vds_steady_max": max(n0["vds"]["steady"]),
                "vds_steady_sh1": n0["vds"]["steady"][0], "controller_bad": bad, "d_peak_vs_q7": dpk,
                "edge_p_w": n0["edge"]["p_w"], "damper_w": damper, "p_l_w": (n0["edge"]["p_w"] - p0 if p0 is not None else 0.0) + damper,
                "damper_inst_w": e_loop(l, 0.0) * sc, "a144_half_li2_w": ref[f"q7_l{l}_n0"]["p_loop_w"],
                "steps_frac_max": max(runs[n]["edge"]["steps_frac"] for n in names),
                "wall_ratio_max": max(runs[n]["wall_s"] / ref_wall(n.replace(f"e{d}_", "q7_")) for n in names)}
        pl = [(0, 0.0)] + [(l, out["per"][f"{d}_l{l}"]["p_l_w"]) for l in LS if f"{d}_l{l}" in out["per"]]
        out["per"][f"{d}_l_loss_ph"] = next((l0 + (P_1PCT - p0_) * (l1 - l0) / (p1 - p0_) for (l0, p0_), (l1, p1)
                                             in zip(pl, pl[1:]) if p0_ <= P_1PCT < p1), None)
    crit = {"1_identity": bool(ids) and all(i["identical"] and i["src_modified"] is False for i in ids),
            "2_voltage": {d: [l for l in LS if out["per"].get(f"{d}_l{l}", {}).get("voltage_ok")] for d in DIDT},
            "3_controller": all(not b for d in DIDT for l in LS for b in out["per"].get(f"{d}_l{l}", {}).get("controller_bad", {}).values())
                            and all(not out["per"][f"{d}_l0"]["controller_bad"] for d in DIDT),
            "5_cost": all(out["per"][f"{d}_l{l}"]["steps_frac_max"] <= 0.03 and out["per"][f"{d}_l{l}"]["wall_ratio_max"] <= 1.6
                          for d in DIDT for l in LS if f"{d}_l{l}" in out["per"])}
    out["criteria"] = crit
    (HERE / "a145_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"1 identity {crit['1_identity']} ({[(i['run'], i['identical']) for i in ids]}); 3 controller {crit['3_controller']}; 5 cost {crit['5_cost']}")
    print("didt L | whole V n0/l_p48/s_p62 | steady SH1/max | ctl bad | dpk l/s | edge W | damper W (inst) | P_L W | A144 W")
    for d in DIDT:
        x0 = out["per"][f"{d}_l0"]
        print(f"{d:3d}   0 | edge {x0['edge_p_w']:.2f} W, ctl bad {x0['controller_bad']}")
        for l in LS:
            x = out["per"].get(f"{d}_l{l}")
            if not x:
                continue
            v = x["vds_whole"]; bad = {r: b for r, b in x["controller_bad"].items() if b}
            print(f"{d:3d} {l:3d} | {v['n0']:.1f}/{v['l_p48_1us']:.1f}/{v['s_p62']:.1f} | {x['vds_steady_sh1']:.1f}/{x['vds_steady_max']:.1f} | "
                  f"{bad or '-'} | {x['d_peak_vs_q7']['l_p48_1us']:+.1f}/{x['d_peak_vs_q7']['s_p62']:+.1f} | {x['edge_p_w']:.2f} | "
                  f"{x['damper_w']:.2f} ({x['damper_inst_w']:.2f}) | {x['p_l_w']:.2f} | {x['a144_half_li2_w']:.2f}")
        print(f"     L_loss(1 %) {out['per'][f'{d}_l_loss_ph']} pH; steps frac max "
              f"{max(out['per'][f'{d}_l{l}']['steps_frac_max'] for l in LS if f'{d}_l{l}' in out['per']):.3f}")


def ref_wall(name):
    return json.loads((A144D / "cosim" / f"run_{name}.json").read_text())["wall_s"]


if __name__ == "__main__":
    main()
