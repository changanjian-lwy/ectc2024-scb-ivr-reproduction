"""C12 analysis against BOUNDARY Section 2, per row: floor-first duplicates (A141 make_cfgs.floor_first, every module),
whole-run and post-step peak vs the reference row (C10; C11 for the L rows), handover rails (c10_analyze.rails), late
fires and overlaps, lock on the L rows (a134_analyze.lock vs the C10 row at L0, as c11_analyze). Writes c12_summary.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TC = HERE.parent
TA = TC.parent / "track_A_periodic_steady_state"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


C10 = _load("c10_analyze", TC / "C10_seed_before_entry" / "c10_analyze.py")
A134 = _load("a134_analyze", TA / "A134_p24_inductance_cap_lock" / "a134_analyze.py")
A141 = _load("a141_make_cfgs", TA / "A141_p24_floor_late_report" / "make_cfgs.py")


def load(p):
    return json.loads(Path(p).read_text())


def ref_path(n):
    c11 = n.startswith(("l120_", "l130_"))
    return TC / ("C11_seed2_inductance" if c11 else "C10_seed_before_entry") / "cosim" / f"run_{n}.json"


def stats(d):
    mods = [d] + d["modules_rest"]
    x = {"ipk_a": [r["ipk_a"] for r in mods], "late": sum(sum(r["late_fires"]) if isinstance(r["late_fires"], list)
                                                           else r["late_fires"] for r in mods),
         "overlaps": [r["overlaps"] for r in mods], "ff": [len(A141.floor_first(r)[0]) for r in mods]}
    cfg = d["cfg"]
    key = "load_step" if cfg.get("load_step") else "line_step" if cfg.get("line_step") else None
    if key:
        ts = cfg[key]["t_us"] * 1e-6
        x["peak_after_a"] = [max(q["i_a"] for q in r["highoffs_last"] if q["t_s"] >= ts) for r in mods]
    return x


def main():
    res, crit = {}, {}
    for n in (HERE / "cosim" / "ORDER.txt").read_text().split():
        p = HERE / "cosim" / f"run_{n}.json"
        if not p.exists():
            continue
        d, r = load(p), load(ref_path(n))
        x, y = stats(d), stats(r)
        x["ref"] = {k: y[k] for k in ("ipk_a", "late", "ff") + (("peak_after_a",) if "peak_after_a" in y else ())}
        x["rails"] = C10.rails(d)
        c = {"1_floor_first": sum(x["ff"]) == 0,
             "2_peak": max(x["ipk_a"]) <= max(max(y["ipk_a"]) + 2.0, 189.0) and max(x["ipk_a"]) <= 200.0,
             "3_rails": all(q["max_v"] <= C10.RAIL_MAX and q["hi_us"] <= C10.RAIL_HI_US for q in x["rails"][1:]),
             "4_late_overlap": x["late"] <= 2 * y["late"] + 3 and all(o == 0 for o in x["overlaps"])}
        if "peak_after_a" in x:
            c["2_peak_after"] = max(x["peak_after_a"]) <= max(max(y["peak_after_a"]) + 2.0, 189.0)
        if n.startswith(("l120_", "l130_")):
            ref0 = load(TC / "C10_seed_before_entry" / "cosim" / f"run_{n.split('_', 1)[1]}.json")
            x["lock"] = [A134.lock(m, dev_ref=A134.lock(q)["ladder_dev"]) for m, q in
                         zip([d] + d["modules_rest"], [ref0] + ref0["modules_rest"])]
            c["5_no_lock"] = not any(m["locked_ph"] for m in x["lock"])
        x["criteria"] = c
        res[n] = x
    for k in ("1_floor_first", "2_peak", "2_peak_after", "3_rails", "4_late_overlap", "5_no_lock"):
        crit[k] = all(x["criteria"].get(k, True) for x in res.values())
    (HERE / "c12_summary.json").write_text(json.dumps({"n_rows": len(res), "criteria": crit, "rows": res}, indent=1, default=float) + "\n")
    print(f"{len(res)} rows; criteria:", " ".join(f"{k}={'P' if v else 'F'}" for k, v in crit.items()))
    for n, x in res.items():
        pa = f" after {max(x['peak_after_a']):.1f} (ref {max(x['ref']['peak_after_a']):.1f})" if "peak_after_a" in x else ""
        fails = [k for k, v in x["criteria"].items() if not v]
        print(f"{n:15s} pk {max(x['ipk_a']):5.1f} (ref {max(x['ref']['ipk_a']):5.1f}){pa} late {x['late']} (ref {x['ref']['late']}) "
              f"ff {sum(x['ff'])} (ref {sum(x['ref']['ff'])}) rail1 " + " ".join(f"{q['max_v']:.2f}/{q['hi_us']:.0f}" for q in x["rails"])
              + (" FAIL " + ",".join(fails) if fails else ""))


if __name__ == "__main__":
    main()
