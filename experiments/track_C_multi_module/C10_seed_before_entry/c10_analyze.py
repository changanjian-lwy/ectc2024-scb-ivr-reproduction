"""C10 analysis against BOUNDARY Section 2, on whatever records exist (the gate rows first, then all 18):
- S: single-module s<mmm>_<row> records against A137's (every field but cfg, provenance, wall_s);
- G1 rails: every slave's rail 1 (vin - vcs[0], sections in mode P before 242 us) at most 13.5 V and above 13.3 V for at
  most 5 us; G2 whole-run peak <= max(185 A, C06's row + 3 A) on rows without a step; G3 late fires <= 1.5 x C06 + 6;
- C09's criteria 1-3 (c09_analyze's rules: hard limits / no new failure with the limit-cycle reading of sd_band, late
  fires, post-step peak within 7 A of C06 or of cosim/run_c06al10_<row>.json when present);
- each stepped row's post-step peak period: module, phase, and whether that phase turned off low twice within 20 ns
  before it (the double low-off seen in C09's and C06's l_p48_5us peaks).
Writes c10_summary.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TC = HERE.parent
A137 = TC.parent / "track_A_periodic_steady_state" / "A137_p24_vff_restart_at_handover" / "cosim"
spec = importlib.util.spec_from_file_location("c09_analyze", TC / "C09_seed_four_modules" / "c09_analyze.py")
C9 = importlib.util.module_from_spec(spec); spec.loader.exec_module(C9)
C6 = C9.C6
C6.HERE = HERE                                                             # analyse() reads HERE / cosim
C06_SUM = C9.C06_SUM
T_HAND = 242e-6
RAIL_MAX, RAIL_HI, RAIL_HI_US = 13.5, 13.3, 5.0


def identity(name):
    a, b = (json.loads(p.read_text()) for p in (A137 / f"run_{name}.json", HERE / "cosim" / f"run_{name}.json"))
    return sorted(k for k in set(a) | set(b) if k not in ("cfg", "provenance", "wall_s") and a.get(k) != b.get(k))


def rails(d):
    """Per module: max rail 1 and time above RAIL_HI, sections in mode P before T_HAND."""
    out = []
    for r in [d] + d["modules_rest"]:
        s = [q for q in r["sections"] if q["t_s"] <= T_HAND and q["mode_p"]]
        v = [q["vin_v"] - q["vcs_v"][0] for q in s]
        hi = sum(b["t_s"] - a["t_s"] for a, b, x in zip(s, s[1:], v) if x > RAIL_HI)
        out.append({"max_v": max(v), "hi_us": hi * 1e6})
    return out


def peak_period(d, ts):
    """The post-step peak's module and phase, and whether that phase turned off low twice within 20 ns before it."""
    ia, m, q = max(((e["i_a"], m, e) for m, r in enumerate([d] + d["modules_rest"]) for e in r["highoffs_last"]
                    if e["t_s"] >= ts), key=lambda x: x[0])
    r = ([d] + d["modules_rest"])[m]
    lo = sorted(e["t_s"] for e in r["lowoffs_last"] if e["phase"] == q["phase"] and 0 <= q["t_s"] - e["t_s"] <= 0.3e-6)
    return {"i_a": ia, "module": m, "phase": q["phase"], "t_after_us": (q["t_s"] - ts) * 1e6,
            "double_lowoff": any(b - a <= 20e-9 for a, b in zip(lo, lo[1:]))}


def main():
    res, crit = {}, {}
    single = sorted(p.stem[4:] for p in (HERE / "cosim").glob("run_s[01]*_*.json"))
    ident = {n: identity(n) for n in single}
    if single:
        crit["S_s100_identical"] = all(not v for n, v in ident.items() if n.startswith("s100_"))
        if any(not n.startswith("s100_") for n in single):
            crit["S_all_identical"] = all(not v for v in ident.values())
    rows = [r for r in list(C6.ROW_LIST) + list(C6.LS) if (HERE / "cosim" / f"run_{r}.json").exists()]
    for row in rows:
        x = C6.analyse(row)
        c = x["criteria"]
        c.pop("identity_without_fires", None)
        c["peak_200a"] = max(x["ipk_a"]) <= 200.0
        d = C6.load(HERE / "cosim" / f"run_{row}.json")
        if "sd_band" in c:
            x["limit_cycle"] = C9.limit_cycle(d)
        x["rails"] = rails(d)
        c["G1_rails"] = all(q["max_v"] <= RAIL_MAX and q["hi_us"] <= RAIL_HI_US for q in x["rails"][1:])
        c["late_c06"] = sum(x["late_fires"]) <= 1.5 * sum(C06_SUM[row]["late_fires"]) + 6
        if "peak_after_a" in x:
            x["c06_peak_after_a"] = C06_SUM[row]["peak_after_a"]
            x["step_offset_ns"] = C9.step_offset(d, C6.T_STEP) * 1e9
            x["peak_period"] = peak_period(d, C6.T_STEP)
            ref, rr = max(x["c06_peak_after_a"]), HERE / "cosim" / f"run_c06al10_{row}.json"
            if rr.exists():
                r = C6.load(rr)
                ref = x["c06al10_peak_after_a"] = C9.peak_after(r, C9.t_step(r))
                x["c06al10_peak_period"] = peak_period(r, C9.t_step(r))
            c["c06_within_7a"] = max(x["peak_after_a"]) <= ref + 7.0
        else:
            c["G2_peak"] = max(x["ipk_a"]) <= max(185.0, max(C06_SUM[row]["ipk_a"]) + 3.0)
        x["c06_failed"] = [k for k, v in C06_SUM[row]["criteria"].items() if not v]
        lc = x.get("limit_cycle", {}).get("cycle", False)
        x["new_fail"] = [k for k, v in c.items() if not v and k not in x["c06_failed"]
                         and k not in ("late_c06", "c06_within_7a", "G1_rails", "G2_peak") and not (k == "sd_band" and lc)]
        res[row] = x
    gate = [r for r in ("n0", "m1n", "m3n") if r in res]
    for k, key in (("G1_rails", "G1_rails"), ("G2_peak", "G2_peak"), ("G3_late", "late_c06")):
        crit[k] = all(res[r]["criteria"][key] for r in gate)
    if len(rows) == 18:
        hard = ("no_overlap", "peak_200a", "locked", "peak_after_200a")
        crit["1_hard"] = all(res[r]["criteria"].get(k, True) for r in rows for k in hard)
        crit["1_no_new_fail"] = all(not res[r]["new_fail"] for r in rows)
        crit["2_late_c06"] = all(res[r]["criteria"]["late_c06"] for r in rows)
        crit["3_c06_within_7a"] = all(res[r]["criteria"].get("c06_within_7a", True) for r in rows)
        crit["4_rails_peak"] = all(res[r]["criteria"]["G1_rails"] and res[r]["criteria"].get("G2_peak", True) for r in rows)
    out = {"criteria": crit, "identity": ident, "rows": res}
    (HERE / "c10_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("criteria:", " ".join(f"{k}={'P' if v else 'F'}" for k, v in crit.items()))
    bad = {n: v for n, v in ident.items() if v}
    print(f"single-module identity: {len(ident) - len(bad)}/{len(ident)} identical" + (f"; differ {bad}" if bad else ""))
    for row in rows:
        x = res[row]
        fails = [k + ("*" if k in x["new_fail"] else "") for k, v in x["criteria"].items() if not v]
        rl = " ".join(f"{q['max_v']:.2f}/{q['hi_us']:.0f}" for q in x["rails"])
        pa = ""
        if "peak_after_a" in x:
            p = x["peak_period"]
            pa = (f" after {max(x['peak_after_a']):.1f} (C06 {max(x['c06_peak_after_a']):.1f}, off {x['step_offset_ns']:.0f} ns,"
                  f" m{p['module']}p{p['phase']}{' 2lo' if p['double_lowoff'] else ''})")
        print(f"{row:10s} pk {max(x['ipk_a']):5.1f} (C06 {max(C06_SUM[row]['ipk_a']):5.1f}){pa} late {sum(x['late_fires'])}"
              f" (C06 {sum(C06_SUM[row]['late_fires'])}) rail1 {rl} fail {','.join(fails) or '-'}")


if __name__ == "__main__":
    main()
