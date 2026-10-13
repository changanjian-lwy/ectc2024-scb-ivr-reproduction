"""A212 analysis (BOUNDARY Section 2). Per row: c6 from a206_analyze.whole, c7 (Vo within 1 V +- 10 mV over the last
20 us), and after the stimulus: the peak (against V5's figure of the coverage table), Vo's extremes, late fires, the
lowest Ton register (below the old 22.25 ns limit the row depends on A208's), the oracle's events by class
(a142_oracles.check; events from the stimulus on).
  python3 a212_analyze.py -> a212_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A6 = _load("a206_analyze", TA / "A206_p24_low_side_zvs_turn_on" / "a206_analyze.py")
ORA = _load("a142_oracles", TA / "A142_p24_random_stimulus" / "a142_oracles.py")
COS = HERE / "cosim"
V5 = {"n_l_p48_2us": 182.9, "n_l_p48_3us": 181.8, "n_l_p48_4us": 182.5, "n_l_p48_5us": 182.3, "n_l_p48_10us": 183.7,
      "n_l_m48_1us": 172.4, "n_l_m80_10us": 166.7, "n_s_p62": 181.4}          # A, FINAL_SPEC_COVERAGE Section 3 (A173, A175)
OLD_LIMIT_NS, BAND_END, T_WIN = 22.25, 0.010, 20e-6


def one(path):
    w = A6.whole(path)
    r = json.loads(Path(path).read_text())
    cfg = r["cfg"]
    ev = cfg.get("line_step") or cfg.get("load_step")
    t_ev = ev["t_us"] * 1e-6
    ts = np.array([q["t_s"] for q in r["sections"]]); vo = np.array([q["vo"] for q in r["sections"]])
    tl = np.array([q["ton_lsb"] for q in r["sections"]], float) * r["lsb_s"] * 1e9
    aft, last = ts >= t_ev, ts >= ts[-1] - T_WIN
    g = max((e for e in r["gate_offs_last"] if e["t_s"] >= t_ev), key=lambda e: e["i_max_a"])
    k = int(np.searchsorted(ts, t_ev, side="right")) - 1
    o = ORA.check(path)
    cls = {}
    for e in o["events"]:
        if e["t_s"] >= t_ev:
            cls[e["cls"]] = cls.get(e["cls"], 0) + 1
    out = {k2: w[k2] for k2 in ("status", "commit", "sources_modified", "wall_s", "shoot_on", "overlaps", "forced", "il_holds", "start_pk",
                                "hand_pk", "peak_whole", "vds_whole", "vo_max_to_300us", "vo_dev_max_mv")}
    out.update(post_pk=g["i_max_a"], post_pk_phase=g["phase"], post_pk_dt_us=1e6 * (g["t_s"] - t_ev), v5_post_pk=V5.get(Path(path).stem[4:]),
               vo_after_min_mv=1e3 * float(vo[aft].min() - 1.0), vo_after_max_mv=1e3 * float(vo[aft].max() - 1.0),
               vo_end_mv=[1e3 * float(vo[last].min() - 1.0), 1e3 * float(vo[last].max() - 1.0)],
               late_after=(np.array(r["sections"][-1]["late"]) - np.array(r["sections"][k]["late"])).tolist(),
               ton_reg_min_after_ns=float(tl[aft].min()), ton_reg_max_after_ns=float(tl[aft].max()),
               uses_new_limit=bool(tl[aft].min() < OLD_LIMIT_NS), ton_min_ns=cfg.get("ton_min_ns"), oracle_after=cls,
               oracle_new_after=cls.get("NEW", 0))
    out["criteria"] = {"c6": w["criteria"]["c6"], "c7": bool(max(abs(x) for x in out["vo_end_mv"]) <= 1e3 * BAND_END)}
    return out


def main():
    res = {"runs": {f.stem[4:]: one(f) for f in sorted(COS.glob("run_n_*.json"))}}
    (HERE / "a212_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for n, m in res["runs"].items():
        print(f"{n:14s} {m['status'][:4]} post {m['post_pk']:.2f} A (ph {m['post_pk_phase']}, +{m['post_pk_dt_us']:.1f} us; V5 {m['v5_post_pk']}) whole {m['peak_whole']:.1f} | "
              f"V_DS {m['vds_whole']:.1f} | Vo after {m['vo_after_min_mv']:+.1f} / {m['vo_after_max_mv']:+.1f} mV, end {m['vo_end_mv'][0]:+.2f}..{m['vo_end_mv'][1]:+.2f} | "
              f"late {m['late_after']} holds {m['il_holds']} | register {m['ton_reg_min_after_ns']:.2f}..{m['ton_reg_max_after_ns']:.2f} ns "
              f"(below old limit: {m['uses_new_limit']}) | oracle {m['oracle_after']} | {m['criteria']}")


if __name__ == "__main__":
    main()
