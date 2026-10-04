"""C08 analysis against BOUNDARY Section 2: C06's per-row analysis (c06_analyze.analyse, on C08's records) with its
whole-run peak criterion replaced by the peak after the start-up (t >= 600 us; the start-up peak is reported) and its
C05-identity criterion dropped; each stepped row's post-step peak against C06's; the L x 1.2 pair's lock (A134's rule on
every module: ladder deviation over the last 200 periods more than 0.5 points above C06's s_p62 module, or Vo outside
1 %). Writes c08_summary.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TC = HERE.parent
spec = importlib.util.spec_from_file_location("c06_analyze", TC / "C06_slave_floor" / "c06_analyze.py")
C6 = importlib.util.module_from_spec(spec); spec.loader.exec_module(C6)
C6.HERE = HERE                                                             # analyse() reads HERE / cosim
spec = importlib.util.spec_from_file_location("a134_analyze", C6.TA / "A134_p24_inductance_cap_lock" / "a134_analyze.py")
A134 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A134)
C06_SUM = json.loads((TC / "C06_slave_floor" / "c06_summary.json").read_text())
T_SU = 600e-6


def lock_all(d, ref):
    mods, rmods = [d] + d["modules_rest"], [ref] + ref["modules_rest"]
    out = []
    for m, r in zip(mods, rmods):
        x = A134.lock(m, dev_ref=A134.lock(r)["ladder_dev"])
        out.append({k: x[k] for k in ("ladder_dev", "vo_end", "rails_end_v", "locked_ph")})
    return out


def main():
    res, crit = {}, {}
    for row in list(C6.ROW_LIST) + list(C6.LS):
        x = C6.analyse(row)
        c = x["criteria"]
        c.pop("identity_without_fires", None)
        d = C6.load(HERE / "cosim" / f"run_{row}.json")
        mods = [d] + d["modules_rest"]
        x["startup_peak_a"] = [r["ipk_a"] for r in mods]
        x["peak_su_a"] = [max(q["i_a"] for q in r["highoffs_last"] if q["t_s"] >= T_SU) for r in mods]
        c["peak_200a"] = max(x["peak_su_a"]) <= 200.0
        if "peak_after_a" in x:
            ref = C06_SUM[row]["peak_after_a"]
            x["c06_peak_after_a"] = ref
            c["c06_within_7a"] = max(x["peak_after_a"]) <= max(ref) + 7.0           # criterion 2 (not one of C06's)
        res[row] = x
    ref = C6.load(TC / "C06_slave_floor" / "cosim" / "run_s_p62.json")
    for arm in ("a", "q"):
        d = C6.load(HERE / "cosim" / f"run_l12{arm}_s_p62.json")
        mods = [d] + d["modules_rest"]
        res[f"l12{arm}_s_p62"] = {"lock": lock_all(d, ref), "overlaps": [r["overlaps"] for r in mods],
                                  "peak_after_a": [max(q["i_a"] for q in r["highoffs_last"] if q["t_s"] >= 1000e-6) for r in mods],
                                  "late_fires": [C6.late(r) for r in mods]}
    crit["l12a_locks"] = any(m["locked_ph"] for m in res["l12a_s_p62"]["lock"])
    crit["l12q_no_lock"] = not any(m["locked_ph"] for m in res["l12q_s_p62"]["lock"])
    rows = list(C6.ROW_LIST) + list(C6.LS)
    hard = ("no_overlap", "peak_200a", "locked", "peak_after_200a")
    crit["1_hard"] = all(res[r]["criteria"].get(k, True) for r in rows for k in hard)
    for r in rows:
        res[r]["c06_failed"] = [k for k, v in C06_SUM[r]["criteria"].items() if not v]
        res[r]["new_fail"] = [k for k, v in res[r]["criteria"].items() if not v and k not in res[r]["c06_failed"]]
    crit["1_no_new_fail"] = all(not res[r]["new_fail"] for r in rows)
    crit["2_c06_within_7a"] = all(res[r]["criteria"].get("c06_within_7a", True) for r in rows)
    out = {"criteria": crit, "rows": res}
    (HERE / "c08_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("criteria:", " ".join(f"{k}={'P' if v else 'F'}" for k, v in crit.items()))
    for row in list(C6.ROW_LIST) + list(C6.LS):
        x = res[row]
        bad = [k + ("*" if k in x["new_fail"] else "") for k, v in x["criteria"].items() if not v]
        pa = f" after {max(x['peak_after_a']):.1f} (C06 {max(x['c06_peak_after_a']):.1f})" if "peak_after_a" in x else ""
        print(f"{row:10s} pk_su {max(x['peak_su_a']):5.1f} start-up {max(x['startup_peak_a']):5.1f}{pa} late {x['late_fires']} "
              f"fail {','.join(bad) or '-'}")
    for arm in ("a", "q"):
        x = res[f"l12{arm}_s_p62"]
        print(f"l12{arm}_s_p62 peak {max(x['peak_after_a']):.1f} late {x['late_fires']} " +
              " | ".join(f"m{i} dev {m['ladder_dev'] * 100:.2f}% vo {m['vo_end']:.4f} {'LOCK' if m['locked_ph'] else 'ok'}" for i, m in enumerate(x["lock"])))


if __name__ == "__main__":
    main()
