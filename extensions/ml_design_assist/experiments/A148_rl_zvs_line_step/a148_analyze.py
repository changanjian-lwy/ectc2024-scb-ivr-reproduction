"""A148 cosim analysis: criteria 3-7 against the option-off records (A143 K 4 rows, A145 e72 loop rows, this
experiment's o_ falling rows). Per run: every phase's largest turn-on V_DS and hard turn-ons (> 6 V) in the 60 us
after the step, phase 1's largest low-side turn-off current, the peak after the step, late fires, Vo's extreme and
last exit from 1 %, and with vds_win the 8 switches' largest V_DS at start-up (< 300 us), in steady state (600 us to
the step), after the step (100 us) and over the whole run; A142's oracles with A148's zero-voltage class (hard turn-ons over the whole
mode-P window). Writes a148_summary.json; prints <= 15 lines."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from scb_ivr.cosim.matrix import step_stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "experiments" / "track_A_periodic_steady_state" / "A142_p24_random_stimulus"))
import a142_oracles as O  # noqa: E402
COS = HERE / "cosim"
TA = HERE.parents[3] / "experiments" / "track_A_periodic_steady_state"
A143C = TA / "A143_p24_short_comparator_phase" / "cosim"
A145C = TA / "A145_p24_finite_switching_edges" / "cosim"
ROWS = ("n0", "l_p48_1us", "l_p48_5us", "l_m48_1us", "l_m48_5us", "l_m80_10us", "s_p62", "s_m62")
WIN = 60e-6


def load(p):
    return json.loads(Path(p).read_text())


def t_step(r):
    c = r["cfg"]
    return 1e-6 * ((c.get("line_step") or c.get("load_step") or {}).get("t_us", 1000.0))


def stats(r, name=""):
    t0 = t_step(r)
    chk = O.check_dict(r, name)
    ons = [e for e in r["turnons_last"] if t0 <= e["t_s"] < t0 + WIN]
    los = [e for e in r["lowoffs_last"] if e["phase"] == 1 and t0 <= e["t_s"] < t0 + WIN]
    pre = [e["vds_v"] for e in r["turnons_last"] if e["phase"] == 1 and 600e-6 <= e["t_s"] < t0]
    out = {"status": r.get("status"), "src_modified": r["provenance"].get("cosim_sources_modified"),
           "late": r["late_fires"], "overlaps": r["overlaps"],
           "von_max": [max((e["vds_v"] for e in ons if e["phase"] == k), default=0.0) for k in range(1, 5)],
           "hard": [sum(1 for e in ons if e["phase"] == k and e["vds_v"] > 6.0) for k in range(1, 5)],
           "ioff1_max": max((e["i_a"] for e in los), default=0.0),
           "peak_post": max((e["i_a"] for e in r["highoffs_last"] if e["t_s"] >= t0), default=0.0),
           "von1_pre_mean": float(np.mean(pre)) if pre else None, **step_stats(r, t0),
           "oracle_new": sum(1 for e in chk["events"] if e["cls"] == "NEW"),
           "zvs": {k: chk["zvs"][k] for k in ("n", "vds_max", "per_phase", "positive_valley")}}
    secs = r["sections"]
    out["vo_mean_pre_mv"] = float(1e3 * (np.mean([s["vo"] for s in secs if 600e-6 <= s["t_s"] < t0]) - 1.0))
    if any("vds_win_v" in s for s in secs):
        w = lambda a, b: max((max(s["vds_win_v"]) for s in secs if "vds_win_v" in s and a <= s["t_s"] < b), default=0.0)
        out["vds"] = {"start": w(0, 300e-6), "steady": w(600e-6, t0), "post": w(t0, t0 + 100e-6), "whole": w(0, 1.0)}
    return out


def off_path(name):
    """The option-off record for an A148 run name."""
    if name.startswith("o_"):
        return None
    base = name.split("_", 1)[1]
    if base.startswith("e72_"):
        return A145C / f"run_{base}.json" if "l_m48" not in base else COS / f"run_o_{base}.json"
    for s in ("s070", "s130"):
        if base.startswith(s + "_"):
            return A143C / f"run_g4_{s}_{base[5:]}_k4.json"
    return A143C / ("run_g3_s100_n0_k4.json" if base == "n0" else f"run_g4_s100_{base}_k4.json")


def identity():
    a, b = load(COS / "run_id_l_p48_1us.json"), load(A143C / "run_g4_s100_l_p48_1us_k4.json")
    skip = {"provenance", "wall_s", "cfg"}
    diff = [k for k in set(a) | set(b) if k not in skip and a.get(k) != b.get(k)]
    return {"equal": not diff, "diff_fields": sorted(diff)}


def main():
    runs = {}
    for p in sorted(COS.glob("run_*.json")):
        name = p.stem[4:]
        if name.startswith("id_"):
            continue
        r = stats(load(p))
        op = off_path(name)
        if op is not None and op.exists():
            r["off"] = stats(load(op))
        runs[name] = r
    ident = identity()
    c = {}
    n0 = runs.get("v075_n0")
    c[3] = ident["equal"] and all(not x["src_modified"] for x in runs.values())
    c[4] = bool(n0) and (abs(n0["vo_mean_pre_mv"] - n0["off"]["vo_mean_pre_mv"]) <= 0.5
                         and abs(n0["peak_post"] - n0["off"]["peak_post"]) <= 1.0
                         and abs(n0["von1_pre_mean"] - n0["off"]["von1_pre_mean"]) <= 0.3)
    c[5] = all(runs[f"v075_{r}"]["von_max"][0] <= 12.0 for r in ("l_p48_1us", "l_p48_5us")) and max(runs["v075_s_p62"]["von_max"]) <= 7.0
    reg = [k for k in runs if k.startswith("v075_") and "e72" not in k]
    fall = ("l_m48_1us", "l_m48_5us", "l_m80_10us")
    c[6] = all(runs[k]["peak_post"] <= 200.0 and runs[k]["late"] <= runs[k]["off"]["late"]
               and runs[k]["back_within_1pct_us"] <= runs[k]["off"]["back_within_1pct_us"] + 20.0
               and (not k.endswith(fall) or max(runs[k]["von_max"]) <= max(runs[k]["off"]["von_max"]) + 1.0) for k in reg)
    lp = [runs.get(f"v075_e72_l{l}_l_p48_1us") for l in (50, 100)]
    c[7] = all(x and x["vds"]["post"] <= x["vds"]["start"] for x in lp) and bool(lp[0]) and lp[0]["vds"]["whole"] <= 40.0
    out = {"identity": ident, "criteria": c, "runs": runs}
    (HERE / "a148_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("criteria", {k: ("PASS" if v else "FAIL") for k, v in c.items()}, "| identity diff", ident["diff_fields"])
    for k in ("v075_l_p48_1us", "v075_l_p48_5us", "v075_s_p62", "v075_l_m48_1us", "v100_l_p48_1us", "v100_s_p62"):
        if k in runs:
            x = runs[k]
            print(f"{k:16s} von {[round(v, 1) for v in x['von_max']]} (off {[round(v, 1) for v in x['off']['von_max']]})"
                  f" pk {x['peak_post']:.1f} ({x['off']['peak_post']:.1f}) vo {x['extreme_mv']:.1f} mV back {x['back_within_1pct_us']:.0f} us")
    for k in sorted(runs):
        if "e72" in k:
            x = runs[k]
            o = x.get("off", {}).get("vds", {})
            print(f"{k:24s} V_DS start {x['vds']['start']:.1f} post {x['vds']['post']:.1f} (off {o.get('post', float('nan')):.1f}) whole {x['vds']['whole']:.1f} von1 {x['von_max'][0]:.1f}")


if __name__ == "__main__":
    main()
