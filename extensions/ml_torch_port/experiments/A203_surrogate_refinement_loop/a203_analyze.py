"""A203 analysis: the loop (a203_loop.json) against D63's own search (tmp/a203/d63_100k.npz, a203_reference.json)
and the criteria of BOUNDARY.md. Writes a203_summary.json; prints <= 15 lines.

    PYTHONPATH=src python3 .../a203_analyze.py        (numpy only)"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from a203_d63_reference import A120, DD, STANDARD, TMP, judge, verdict  # noqa: E402

from scb_ivr.extensions.ml_nn import MLP, Scaler  # noqa: E402

BUDGETS, DRAWS = (160, 1160), 1000                                  # the loop's own D63 designs; plus A120's 8000 transients


def surrogate_table(net, sx, sy, designs):
    feats = DD.features([dict(d, kind=k, di_a=di, dv_v=dv, slew_us=sl) for d in designs for k, di, dv, sl in STANDARD])
    p = sy.inv(net.predict(sx.fwd(feats))).reshape(len(designs), len(STANDARD), -1)
    f1 = p[:, :, 0].max(axis=1)
    feas = np.array([verdict(p[i, :, 0], p[i, :, 2], np.expm1(p[i, :, 3])) for i in range(len(p))])
    return f1, feas


def against(f1s, feas_s, f1, feas):
    """How a surrogate's feasible set and its worst peak compare with D63's on the same designs."""
    both = feas_s & feas
    return {"surrogate_feasible": int(feas_s.sum()), "both": int(both.sum()),
            "precision": float(both.sum() / max(feas_s.sum(), 1)), "recall": float(both.sum() / max(feas.sum(), 1)),
            "peak_mae_on_d63_feasible_a": float(np.mean(np.abs(f1s[feas] - f1[feas]))),
            "peak_bias_on_d63_feasible_a": float(np.mean(f1[feas] - f1s[feas]))}


def main():
    ref = json.loads((HERE / "a203_reference.json").read_text())
    loop = json.loads((HERE / "a203_loop.json").read_text())
    designs = DD.sample(ref["n"], ref["seed"])
    f1, f2, feas, div = judge(np.load(TMP / "d63_100k.npz")["res"].astype(np.float64))
    best_ref, best_loop = ref["best"]["f1"], loop["best"]["d63_f1"] if loop["best"] else np.inf
    # random search in D63 at the loop's cost: the best feasible worst peak of a random subset
    rng = np.random.default_rng(0)
    base = {}
    for n in BUDGETS:
        bests = []
        for _ in range(DRAWS):
            j = rng.choice(len(f1), n, replace=False)
            bests.append(f1[j][feas[j]].min() if feas[j].any() else np.inf)
        bests = np.array(bests)
        base[n] = {"found_feasible": float(np.isfinite(bests).mean()), "median_best_a": float(np.median(bests)) if np.isfinite(np.median(bests)) else None,
                   "loop_better": float((best_loop < bests).mean())}
    net0, z = MLP.load(A120 / "a120_mlp.npz")
    sx, sy = Scaler(z["x_mean"], z["x_sd"]), Scaler(z["y_mean"], z["y_sd"])
    w = np.load(HERE / "a203_surrogate_final.npz")
    net1 = MLP.__new__(MLP)
    net1.out, net1.W, net1.b = "linear", [w[f"W{i}"] for i in range(3)], [w[f"b{i}"] for i in range(3)]
    before, after = against(*surrogate_table(net0, sx, sy, designs), f1, feas), against(*surrogate_table(net1, sx, sy, designs), f1, feas)
    last = [r["margin_optimism_a"] for r in loop["rounds"][-3:]]
    mae = loop["rounds"][-1]["test_mae_after_a"]
    first_hit = next((r["round"] for r in loop["rounds"] if r["best_d63_f1"] is not None and r["best_d63_f1"] <= best_ref + 1.5), None)
    crit = {"c1_reaches_reference": {"loop_best_a": float(best_loop), "reference_best_a": best_ref, "first_round_within": first_hit,
                                     "pass": bool(best_loop <= best_ref + 1.5)},
            "c2_beats_random_d63": {str(n): base[n] for n in BUDGETS},
            "c3_optimism_last_rounds": {"values_a": last, "pass": bool(all(v is not None for v in last) and abs(float(np.mean(last))) <= 4.0)},
            "c4_test_mae": {"before_a": loop["rounds"][0]["test_mae_before_a"], "after_a": mae, "pass": bool(mae <= 2.5)}}
    crit["c2_beats_random_d63"]["pass"] = bool(base[160]["loop_better"] >= 0.95 and base[1160]["loop_better"] >= 0.90)
    out = {"criteria": crit, "passed": int(sum(c["pass"] for c in crit.values())), "of": len(crit), "reference": {k: ref[k] for k in ("n", "feasible", "by_rule", "best", "diverged")},
           "loop_best": loop["best"], "d63_designs": loop["rounds"][-1]["d63_designs_so_far"], "surrogate_vs_d63": {"a120": before, "after_loop": after},
           "per_round": [{k: r[k] for k in ("round", "surrogate_feasible_finals", "d63_feasible_picks", "margin_optimism_a", "best_d63_f1", "test_mae_after_a")} for r in loop["rounds"]],
           "provenance": loop["provenance"], "settings": loop["settings"]}
    (HERE / "a203_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    ok = lambda c: "PASS" if crit[c]["pass"] else "FAIL"
    b, lb = ref["best"], loop["best"]
    print(f"A203: {out['passed']} of {out['of']} criteria pass; loop from commit {loop['provenance']['commit']}{' (MODIFIED)' if loop['provenance']['modified'] else ''}")
    print(f"D63 on {ref['n']} random designs: {ref['feasible']} feasible, best {b['f1']:.2f} A ({b['rule']} pct {b['pct']:.2f} Cs {b['cs_uf']:.2f} fc {b['fc_khz']:.1f} floor {b['floor_a']:.2f})")
    if lb:
        d = lb["design"]
        print(f"loop, {out['d63_designs']} D63 designs: best {lb['d63_f1']:.2f} A in round {lb['round']} ({d['rule']} pct {d['pct']:.2f} Cs {d['cs_uf']:.2f} fc {d['fc_khz']:.1f} floor {d['floor_a']:.2f})")
    print(f"C1 {ok('c1_reaches_reference')} loop best vs reference + 1.5 A; first round within: {first_hit}")
    for n in BUDGETS:
        m = base[n]["median_best_a"]
        print(f"  random D63, {n} designs: finds a feasible one in {base[n]['found_feasible']:.0%}, median best {'none' if m is None else format(m, '.1f')} A; loop better in {base[n]['loop_better']:.1%}")
    print(f"C2 {ok('c2_beats_random_d63')} | C3 {ok('c3_optimism_last_rounds')} margin optimism, last three rounds {[None if v is None else round(v, 1) for v in last]} A"
          f" | C4 {ok('c4_test_mae')} test MAE {crit['c4_test_mae']['before_a']:.2f} -> {mae:.2f} A")
    print("per round, best D63 worst peak: " + " ".join("-" if r["best_d63_f1"] is None else f"{r['best_d63_f1']:.1f}" for r in loop["rounds"]))
    print("per round, margin optimism:     " + " ".join("-" if r["margin_optimism_a"] is None else f"{r['margin_optimism_a']:+.1f}" for r in loop["rounds"]))
    for nm, t in (("A120's surrogate", before), ("after the loop", after)):
        print(f"{nm} on the {ref['n']}: says {t['surrogate_feasible']} feasible, {t['both']} are; precision {t['precision']:.2f}, recall {t['recall']:.2f}; "
              f"worst-peak MAE on D63's feasible {t['peak_mae_on_d63_feasible_a']:.1f} A (bias {t['peak_bias_on_d63_feasible_a']:+.1f})")


if __name__ == "__main__":
    main()
