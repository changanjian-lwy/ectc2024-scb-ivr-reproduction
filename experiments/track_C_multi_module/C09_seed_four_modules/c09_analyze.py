"""C09 analysis against BOUNDARY Section 2: C06's per-row analysis (c06_analyze.analyse, on C09's records) with C06's
whole-run peak criterion on every row and its C05-identity criterion dropped; the master's end-window quantisation limit
cycle (>= 2 Ton codes and the sampled Vo beyond vref +- adc_lsb / 2) behind any sd_band miss; each row's late-fire total
against C06's; each stepped row's post-step peak against C06's (or against a rerun of C06's row with the step at C09's
offset, cosim/run_c06al9_<row>.json, when present); c06al_s_m25 against C08's s_m25. Writes c09_summary.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TC = HERE.parent
spec = importlib.util.spec_from_file_location("c06_analyze", TC / "C06_slave_floor" / "c06_analyze.py")
C6 = importlib.util.module_from_spec(spec); spec.loader.exec_module(C6)
C6.HERE = HERE                                                             # analyse() reads HERE / cosim
C06_SUM = json.loads((TC / "C06_slave_floor" / "c06_summary.json").read_text())
C08_SUM = json.loads((TC / "C08_relative_cap_four_modules" / "c08_summary.json").read_text())["rows"]
N_WIN = 200


def limit_cycle(d):
    """Master's last N_WIN sections: Ton codes and the sampled Vo against the ADC's decision levels."""
    s = d["sections"][-N_WIN:]
    vref, half = d["cfg"]["vref_v"], d["cfg"]["adc_lsb_v"] / 2
    tons, vo = sorted({q["ton_lsb"] for q in s}), [q["vo"] for q in s]
    return {"ton_codes": tons, "vo_max_mv": (max(vo) - vref) * 1e3, "vo_min_mv": (min(vo) - vref) * 1e3,
            "cycle": len(tons) >= 2 and (max(vo) > vref + half or min(vo) < vref - half)}


def step_offset(d, t_step):
    """Time from the master's last phase-1 turn-on before the step to the step, s."""
    return t_step - max(q["t_s"] for q in d["turnons_last"] if q["phase"] == 1 and q["t_s"] <= t_step)


def peak_after(d, t_step):
    return max(max(q["i_a"] for q in r["highoffs_last"] if q["t_s"] >= t_step) for r in [d] + d["modules_rest"])


def main():
    res, crit = {}, {}
    rows = list(C6.ROW_LIST) + list(C6.LS)
    for row in rows:
        x = C6.analyse(row)
        c = x["criteria"]
        c.pop("identity_without_fires", None)
        c["peak_200a"] = max(x["ipk_a"]) <= 200.0                               # whole run, every row
        d = C6.load(HERE / "cosim" / f"run_{row}.json")
        if "sd_band" in c:
            x["limit_cycle"] = limit_cycle(d)
        c["late_c06"] = sum(x["late_fires"]) <= 1.5 * sum(C06_SUM[row]["late_fires"]) + 6     # criterion 2
        if "peak_after_a" in x:
            x["c06_peak_after_a"] = C06_SUM[row]["peak_after_a"]
            x["step_offset_ns"] = step_offset(d, C6.T_STEP) * 1e9
            ref, rr = max(x["c06_peak_after_a"]), HERE / "cosim" / f"run_c06al9_{row}.json"
            if rr.exists():                                                     # criterion 3's contingency rerun
                r = C6.load(rr)
                ref = x["c06al9_peak_after_a"] = peak_after(r, r["cfg"]["load_step"]["t_us"] * 1e-6)
            c["c06_within_7a"] = max(x["peak_after_a"]) <= ref + 7.0
        res[row] = x
    for r in rows:
        x = res[r]
        x["c06_failed"] = [k for k, v in C06_SUM[r]["criteria"].items() if not v]
        lc = x.get("limit_cycle", {}).get("cycle", False)
        x["new_fail"] = [k for k, v in x["criteria"].items() if not v and k not in x["c06_failed"]
                         and k not in ("late_c06", "c06_within_7a") and not (k == "sd_band" and lc)]
    hard = ("no_overlap", "peak_200a", "locked", "peak_after_200a")
    crit["1_hard"] = all(res[r]["criteria"].get(k, True) for r in rows for k in hard)
    crit["1_no_new_fail"] = all(not res[r]["new_fail"] for r in rows)
    crit["2_late_c06"] = all(res[r]["criteria"]["late_c06"] for r in rows)
    crit["3_c06_within_7a"] = all(res[r]["criteria"].get("c06_within_7a", True) for r in rows)
    d = C6.load(HERE / "cosim" / "run_c06al_s_m25.json")
    t_al = d["cfg"]["load_step"]["t_us"] * 1e-6
    al = {"peak_after_a": peak_after(d, t_al), "step_offset_ns": step_offset(d, t_al) * 1e9,
          "c08_peak_after_a": max(C08_SUM["s_m25"]["peak_after_a"])}
    crit["4_c06al_2a"] = abs(al["peak_after_a"] - al["c08_peak_after_a"]) <= 2.0
    res["c06al_s_m25"] = al
    out = {"criteria": crit, "rows": res}
    (HERE / "c09_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("criteria:", " ".join(f"{k}={'P' if v else 'F'}" for k, v in crit.items()))
    for row in rows:
        x = res[row]
        bad = [k + ("*" if k in x["new_fail"] else "") for k, v in x["criteria"].items() if not v]
        pa = (f" after {max(x['peak_after_a']):.1f} (C06 {max(x['c06_peak_after_a']):.1f}, off {x['step_offset_ns']:.0f} ns)"
              if "peak_after_a" in x else "")
        lc = x.get("limit_cycle")
        lcs = f" LC {lc['ton_codes']} {lc['vo_min_mv']:+.3f}/{lc['vo_max_mv']:+.3f}" if lc and lc["cycle"] else ""
        print(f"{row:10s} pk {max(x['ipk_a']):5.1f}{pa} late {sum(x['late_fires'])} (C06 {sum(C06_SUM[row]['late_fires'])})"
              f"{lcs} fail {','.join(bad) or '-'}")
    print(f"c06al_s_m25 after {al['peak_after_a']:.1f} (C08 {al['c08_peak_after_a']:.1f}), off {al['step_offset_ns']:.1f} ns")


if __name__ == "__main__":
    main()
