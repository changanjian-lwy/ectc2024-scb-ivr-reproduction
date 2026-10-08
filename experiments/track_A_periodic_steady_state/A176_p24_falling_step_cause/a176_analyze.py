"""A176 analysis (BOUNDARY Section 2): post-step oracle events (a142_oracles), peaks / Vo (a168_analyze.safe_stats),
phase 2-4 valley maxima over the step + 45 us and interlock holds, for each variant and the final plant's run of
the row. Writes a176_summary.json; one line per run."""
from __future__ import annotations

import collections
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


O = _load("a142_oracles", TA / "A142_p24_random_stimulus" / "a142_oracles.py")
A8 = _load("a168_analyze", TA / "A168_p24_gate_loop_bound" / "a168_analyze.py")
FILES = {"final_nom_l_m48_1us": TA / "A175_p24_final_plant_a152_matrix" / "cosim" / "run_nom_l_m48_1us.json",
         "final_ff_l_m80_10us": TA / "A173_p24_final_plant_coverage" / "cosim" / "run_ff_l_m80_10us.json",
         "A164_ff_l_m80_10us": TA / "A164_p24_gate_drive_spread" / "cosim" / "run_ff_l_m80_10us.json",
         **{f.stem[4:]: f for f in sorted((HERE / "cosim").glob("run_*.json"))}}


def one(f):
    res = O.check(str(f))
    t0 = res["t_dist_us"] * 1e-6
    ev = collections.Counter(e["cls"] for e in res["events"] if e["t_s"] >= t0)
    st = A8.safe_stats(str(f))
    r = json.loads(Path(f).read_text())
    lo = r["lowoffs_last"]
    vmax = [max(x["i_a"] for x in lo if x["phase"] == ph and t0 <= x["t_s"] <= t0 + 45e-6) for ph in (2, 3, 4)]
    return {"events": dict(ev), "post": st["peak_post"], "late": st["late"], "extreme_mv": st["extreme_mv"],
            "back_us": st["back_within_1pct_us"], "vds": st["vds"]["whole"], "valley_max_ph234": vmax,
            "holds": sum(r["gate_stats"].get("il_holds", [0]))}


def main():
    out = {k: one(f) for k, f in FILES.items()}
    ev = {k: bool(v["events"].get("K3") or v["events"].get("NEW")) for k, v in out.items()}
    rows = ("nom_l_m48_1us", "ff_l_m80_10us")
    out["criteria"] = {"1_lead_sufficient": all(ev[f"v2lead_{r}"] for r in rows),
                       "2_low_sides_sufficient": all(ev[f"v5nolead_{r}"] for r in rows),
                       "3_combination": all(ev[f"final_{r}"] and not ev[f"v2lead_{r}"] and not ev[f"v5nolead_{r}"]
                                            for r in rows)}
    (HERE / "a176_summary.json").write_text(json.dumps(out, indent=1, default=float))
    for k, v in out.items():
        if k != "criteria":
            print(f"{k:24s} events {v['events']} post {v['post']:.1f} ext {v['extreme_mv']:.1f} "
                  f"valley {[round(x, 1) for x in v['valley_max_ph234']]} holds {v['holds']}")
    print(out["criteria"])


if __name__ == "__main__":
    main()
