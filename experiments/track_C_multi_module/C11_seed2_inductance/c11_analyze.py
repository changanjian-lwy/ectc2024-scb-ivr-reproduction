"""C11 analysis against BOUNDARY Section 2, per run: every module's handover rail 1 (c10_analyze.rails: mode P, before
242 us); whole-run peak; A134's lock rule on every module against C10's same row at L0 (ladder deviation over the last
200 sections more than 0.5 points above it, or Vo outside 1 %); post-step peak (t >= 1000 us); late fires. l120_s_p62 is
compared with C08's l12q_s_p62 (A136's cap without the restart, same cfg but for seed). Writes c11_summary.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TC = HERE.parent


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


C10 = _load_module("c10_analyze", TC / "C10_seed_before_entry" / "c10_analyze.py")
A134 = _load_module("a134_analyze", TC.parent / "track_A_periodic_steady_state" / "A134_p24_inductance_cap_lock" / "a134_analyze.py")
C08 = TC / "C08_relative_cap_four_modules" / "cosim" / "run_l12q_s_p62.json"
T_STEP = 1000e-6


def load(p):
    return json.loads(Path(p).read_text())


def stats(d, row):
    mods = [d] + d["modules_rest"]
    ref = load(TC / "C10_seed_before_entry" / "cosim" / f"run_{row}.json")
    x = {"rails": C10.rails(d), "ipk_a": [r["ipk_a"] for r in mods], "late_fires": [sum(r["late_fires"]) for r in mods],
         "overlaps": [r["overlaps"] for r in mods],
         "lock": [A134.lock(m, dev_ref=A134.lock(r)["ladder_dev"]) for m, r in zip(mods, [ref] + ref["modules_rest"])]}
    if d["cfg"].get("load_step") or d["cfg"].get("line_step"):
        x["peak_after_a"] = [max(q["i_a"] for q in r["highoffs_last"] if q["t_s"] >= T_STEP) for r in mods]
    return x


def main():
    res, crit = {}, {}
    names = (HERE / "cosim" / "ORDER.txt").read_text().split()
    for n in names:
        d = load(HERE / "cosim" / f"run_{n}.json")
        x = stats(d, n.split("_", 1)[1])
        c = {"1_rails": all(q["max_v"] <= C10.RAIL_MAX and q["hi_us"] <= C10.RAIL_HI_US for q in x["rails"]),
             "2_peak_200a": max(x["ipk_a"]) <= 200.0,
             "3_no_lock": not any(m["locked_ph"] for m in x["lock"]),
             "5_late_100": sum(x["late_fires"]) <= 100 and all(o == 0 for o in x["overlaps"])}
        if n == "l120_s_p62":
            x["c08"] = stats(load(C08), "s_p62")
            c["4_c08_within_7a"] = max(x["peak_after_a"]) <= max(x["c08"]["peak_after_a"]) + 7.0
        x["criteria"] = c
        res[n] = x
    for k in ("1_rails", "2_peak_200a", "3_no_lock", "4_c08_within_7a", "5_late_100"):
        crit[k] = all(x["criteria"].get(k, True) for x in res.values())
    (HERE / "c11_summary.json").write_text(json.dumps({"criteria": crit, "runs": res}, indent=1, default=float) + "\n")
    print("criteria:", " ".join(f"{k}={'P' if v else 'F'}" for k, v in crit.items()))
    rows = [(n, x) for n, x in res.items()] + [("C08 l12q", res["l120_s_p62"]["c08"])]
    for n, x in rows:
        pa = f" after {max(x['peak_after_a']):.1f}" if "peak_after_a" in x else ""
        print(f"{n:15s} pk {max(x['ipk_a']):5.1f}{pa} late {sum(x['late_fires'])} rail1 "
              + " ".join(f"{q['max_v']:.2f}/{q['hi_us']:.0f}" for q in x["rails"])
              + " ladder " + " ".join(f"{m['ladder_dev'] * 100:.2f}" for m in x["lock"]) + f" Vo {x['lock'][0]['vo_end']:.4f}"
              + (" LOCK" if any(m["locked_ph"] for m in x["lock"]) else ""))


if __name__ == "__main__":
    main()
