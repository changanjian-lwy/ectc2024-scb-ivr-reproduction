"""A245 analysis (BOUNDARY Section 2). Stage 1: each start-up row in arms f (final configuration) and r (+ rev_n): the
ladder at the end and when it last enters 1 V, the longest run of reverse-conduction reports per phase (whole run and
last 40 us), whether the rule acted, limits (peak, V_DS, overlaps), late fires, oracle NEW (a142_oracles) and Vo after
mode P's entry, the reverse-conduction and edge losses over the last 50 us; g4: a row whose arm r never reaches rev_n
reports in a row equals arm f bit for bit. Stage 2 and g0: run_i_ rows equal A244's run_w_ bit for bit; unit tests and
regression logs (tmp/logs/a245r_*2.log).
  python3 a245_analyze.py -> a245_summary.json"""
from __future__ import annotations

import bisect
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
COS = HERE / "cosim"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a245_make_cfgs", HERE / "make_cfgs.py")
ORC = _load("a142_oracles", TA / "A142_p24_random_stimulus" / "a142_oracles.py")
KEYS = ("sections", "highoffs_last", "lowoffs_last", "turnons_last", "late_fires", "overlaps", "ipk_a")
UNIT_N, BAND_V, VO_LO, VO_HI, TAIL_S, WIN_S = 132, 1.0, 0.99, 1.05, 40e-6, 1e-6
VO_NAT = 0.9827        # A230 run_u_S75h_30_lead: Vo's minimum 3 us after the same lock released by itself


def same(fa, fb):
    a, b = json.loads(Path(fa).read_text()), json.loads(Path(fb).read_text())
    return all(a.get(k) == b.get(k) for k in KEYS)


def rails(s):
    v = [s["vin_v"]] + list(s["vcs_v"]) + [0.0]
    return [v[q] - v[q + 1] for q in range(len(v) - 1)]


def dev(s):
    return max(abs(r - s["vin_v"] / 4) for r in rails(s))


def runs(on, t0=0.0):
    """Longest run of learned reports with V_DS <= 0 at the command, per phase (1..4), from t0."""
    best, cur = {}, {}
    for x in on:
        if "early" not in x:
            continue
        p = x["phase"]
        c = cur.get(p, 0) + 1 if x["vds_v"] <= 0 else 0
        if x["t_s"] >= t0:
            best[p] = max(best.get(p, 0), c)
        cur[p] = c
    return [best.get(p, 0) for p in (1, 2, 3, 4)]


def first_act(on, n):
    """Time of the first report that is the n-th in a row with V_DS <= 0 on phases 2-4 (the rule's first act), or None."""
    cur = {}
    for x in on:
        if "early" not in x or x["phase"] == 1:
            continue
        p = x["phase"]
        cur[p] = cur.get(p, 0) + 1 if x["vds_v"] <= 0 else 0
        if cur[p] == n:
            return x["t_s"]
    return None


def one(f):
    d = json.loads(Path(f).read_text())
    S, te, tmp = d["sections"], d["sections"][-1]["t_s"], d["t_mode_p_s"]
    last_out = max((s["t_s"] for s in S if s["t_s"] > tmp and dev(s) > BAND_V), default=None)
    vo = [s["vo"] for s in S if s["t_s"] > tmp]
    t_vmin = min((s for s in S if s["t_s"] > tmp), key=lambda s: s["vo"])["t_s"]
    o = ORC.check_dict(d, Path(f).name)
    tail = [s for s in S if s["t_s"] > te - 50e-6]
    loss = {k: sum(sum(s[k]) for s in tail[1:]) / (tail[-1]["t_s"] - tail[0]["t_s"]) for k in ("rev_energy_j", "edge_energy_j")}
    new = [e for e in o["events"] if not str(e.get("cls", "")).startswith("K")]
    t_act = first_act(d["turnons_last"], MC.REV_N)
    win = (t_act, (last_out or t_act or 0.0) + WIN_S) if t_act is not None else None
    inside = [e for e in new if win and win[0] <= e["t_s"] <= win[1]]
    return {"dev_end_v": dev(S[-1]), "rails_end_v": [round(r, 2) for r in rails(S[-1])],
            "t_in_band_us": None if last_out is None else last_out * 1e6, "runs": runs(d["turnons_last"]),
            "runs_tail": runs(d["turnons_last"], te - TAIL_S), "dt_final_ns": d["dt_pred_final_ns"],
            "peak_a": max(h["i_a"] for h in d["highoffs_last"]), "vds_max_v": max(d["vds_max_v"]),
            "overlaps": d["overlaps"], "late": sum(d["late_fires"]), "new": len(new), "new_out": len(new) - len(inside),
            "new_in_not_spike": sum(1 for e in inside if e["kind"] != "spike"), "zvs_hits": o["zvs"]["n"],
            "t_act_us": None if t_act is None else t_act * 1e6,
            "rev_w_tail": loss["rev_energy_j"], "edge_w_tail": loss["edge_energy_j"],
            "vo_min": min(vo), "vo_max": max(vo), "t_vo_min_us": t_vmin * 1e6, "t_mode_p_us": tmp * 1e6,
            "status": d["status"], "src_modified": d["provenance"].get("cosim_sources_modified")}


def stage1():
    res = {}
    for row in MC.STAGE1:
        ff, fr = COS / f"run_f_{row}.json", COS / f"run_r_{row}.json"
        if not (ff.exists() and fr.exists()):
            res[row] = None
            continue
        f, r = one(ff), one(fr)
        acted = r["t_act_us"] is not None
        c = {"g1": bool(r["dev_end_v"] <= BAND_V and max(r["runs_tail"][1:]) < MC.REV_N),
             "g2": bool(r["peak_a"] <= 200.0 and r["vds_max_v"] <= 40.0 and r["overlaps"] == 0
                        and r["new_out"] <= f["new"] and r["new_in_not_spike"] == 0),
             "g3": bool(r["vo_min"] >= min(VO_LO, f["vo_min"]) and r["vo_max"] <= max(VO_HI, f["vo_max"])),
             "g4": True if acted else same(ff, fr)}
        t_win = (r["t_act_us"], (r["t_in_band_us"] or 0.0) + WIN_S * 1e6) if acted else None
        res[row] = {"f": f, "r": r, "acted": acted, "criteria": c,
                    "g3_release": bool(not c["g3"] and acted and r["vo_min"] >= VO_NAT and t_win[0] <= r["t_vo_min_us"]
                                       <= t_win[1] and r["vo_max"] <= max(VO_HI, f["vo_max"]))}
    return res


def stage2():
    a244 = TA / "A244_p24_holds_after_handover" / "cosim"
    return {row: (same(COS / f"run_i_{row}.json", a244 / f"run_w_{row}.json")
                  if (COS / f"run_i_{row}.json").exists() else None) for row in MC.STAGE2}


def identity(s2):
    logs = PROJECT / "tmp" / "logs"
    u = re.findall(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+)", (logs / "a245r_unit2.log").read_text())
    n_pass, n_fail = sum(int(p) for _, p, _ in u), sum(int(f) for _, _, f in u)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a245r_reg_{k}2.log").read_text())) for k in ("quick", "full")}
    return {"unit_pass": n_pass, "unit_fail": n_fail, "regression": reg, "stage2": s2,
            "g0": bool(n_pass == UNIT_N and n_fail == 0 and all(reg.values()) and all(v is True for v in s2.values()))}


def main():
    s1, s2 = stage1(), stage2()
    res = {"identity": identity(s2), "stage1": s1}
    done = [x for x in s1.values() if x]
    res["all"] = {g: all(x["criteria"][g] for x in done) for g in ("g1", "g2", "g3", "g4")} | {
        "g0": res["identity"]["g0"], "rows_done": len(done), "rows": len(s1),
        "g3_misses_all_at_release": all(x["criteria"]["g3"] or x["g3_release"] for x in done)}
    (HERE / "a245_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    print("g0", res["identity"]["g0"], {k: v for k, v in res["identity"].items() if k != "stage2"}, "stage2", s2)
    for row, x in s1.items():
        if not x:
            print(f"{row:12s} missing"); continue
        f, r = x["f"], x["r"]
        print(f"{row:12s} dev {f['dev_end_v']:.1f}->{r['dev_end_v']:.1f} V  in band {f['t_in_band_us'] or 0:.0f}->"
              f"{r['t_in_band_us'] or 0:.0f} us  pk {f['peak_a']:.0f}->{r['peak_a']:.0f}  Vo {f['vo_min']:.4f}->{r['vo_min']:.4f}"
              f"  NEW {f['new']}->{r['new']}  acted {x['acted']}  {x['criteria']}")
    print("all", res["all"])


if __name__ == "__main__":
    main()
