"""Regression gate of the shared co-simulation (src/scb_ivr/cosim) against archived runs, bit for bit.

    python3 scripts/cosim_regression.py --quick      # each case to 100 us (start-up, handover, early mode P); ~3 min
    python3 scripts/cosim_regression.py --full       # each case to its end (388.61 us); ~10 min
    [--plant kernel|fast|reference] [--jobs 4]

The archived configurations are read in place (nothing is written into experiment folders); outputs go to
tmp/regression/<mode>/. Quick: every section up to the stop time must equal the archived run's. Full: A89's gate()
(all sections, final registers, steps, peaks) and every recorded edge list on the archived run's fields; keys and
record fields that only the newer bridge writes are listed as format additions. Exit code 0 only if all pass.
Run it after any change to src/scb_ivr/cosim.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TA = PROJECT / "experiments" / "track_A_periodic_steady_state"
sys.path.insert(0, str(TA / "A89_verilog_predicted_low_side"))
from a89_analyze import gate  # noqa: E402

CASES = {   # name: (archived configuration, archived run)
    "a89_r2": ("A92_verilog_error_based_correctors/cosim/cfg_g0_gate_a89r2.json",
               "A89_verilog_predicted_low_side/cosim/run_r2_device_low_pred_blank.json"),
    "a92_j100": ("A92_verilog_error_based_correctors/cosim/cfg_j100_jitter_100ps.json",
                 "A92_verilog_error_based_correctors/cosim/run_j100_jitter_100ps.json"),
    "a92_m3p": ("A92_verilog_error_based_correctors/cosim/cfg_m3p_mismatch_plus3p4ns.json",
                "A92_verilog_error_based_correctors/cosim/run_m3p_mismatch_plus3p4ns.json"),
    "a93_m3n_both": ("A93_verilog_period_following_slots/cosim/cfg_m3n_both.json",
                     "A93_verilog_period_following_slots/cosim/run_m3n_both.json"),
}
RECORDS = ("turnons_last", "lowoffs_last", "lowons_last", "late_fires", "trim_final", "dt_pred_final_ns", "dtl_final_ns",
           "async_fires", "t_mode_p_s", "ton_final_lsb", "t_end_s", "first_overlap", "overlaps", "status", "edges_log")


def compare_full(ref_path: Path, new_path: Path) -> dict:
    r, d = json.loads(ref_path.read_text()), json.loads(new_path.read_text())
    g = gate(ref_path, new_path)
    eq, added = {}, sorted(set(d) - set(r))
    for k in RECORDS:
        if k not in r:
            continue
        a, b = r[k], d.get(k)
        if isinstance(a, list) and a and isinstance(a[0], dict):
            keys = set(a[0])
            eq[k] = b is not None and len(a) == len(b) and all({q: x[q] for q in keys} == {q: y[q] for q in keys}
                                                              for x, y in zip(a, b))
            more = sorted(set(b[0]) - keys) if b else []
            if more:
                added.append(f"{k}: " + ", ".join(more))
        else:
            eq[k] = a == b
    return {"pass": bool(g["pass"] and all(eq.values())), "gate": g, "records": eq, "format_additions": added,
            "wall_s": d["wall_s"]}


def compare_quick(ref_path: Path, new_path: Path) -> dict:
    r, d = json.loads(ref_path.read_text()), json.loads(new_path.read_text())
    n = len(d["sections"])
    return {"pass": n > 0 and r["sections"][:n] == d["sections"], "sections_compared": n, "wall_s": d["wall_s"],
            "t_end_s": d["t_end_s"]}


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")
    ap.add_argument("--plant", default=None, help="override cfg plant_impl (default: the bridge's default, kernel)")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    name = "quick" if a.quick else "full"
    out_dir = PROJECT / "tmp" / "regression" / (name + (f"_{a.plant}" if a.plant else ""))
    out_dir.mkdir(parents=True, exist_ok=True)
    cfgs = []
    for case, (cfg_rel, _) in CASES.items():
        cfg = json.loads((TA / cfg_rel).read_text())
        if a.plant:                                   # a copy with the plant override, init_run made absolute
            cfg["plant_impl"] = a.plant
            cfg["init_run"] = str(((TA / cfg_rel).parent / cfg["init_run"]).resolve())
            path = out_dir / f"cfg_{case}.json"
            path.write_text(json.dumps(cfg, indent=1))
        else:
            path = TA / cfg_rel
        cfgs.append((case, path, cfg["out"]))
    cmd = [sys.executable, "-m", "scb_ivr.cosim.run", *[str(p) for _, p, _ in cfgs], "--jobs", str(a.jobs),
           "--out-dir", str(out_dir)] + (["--t-end-us", "100"] if a.quick else [])
    env = {**__import__("os").environ, "PYTHONPATH": str(PROJECT / "src")}
    subprocess.run(cmd, check=False, env=env)
    summary, ok = {}, True
    for case, _, out_name in cfgs:
        ref = TA / CASES[case][1]
        new = out_dir / out_name
        if not new.exists():
            summary[case] = {"pass": False, "error": "no output"}
        else:
            summary[case] = (compare_quick if a.quick else compare_full)(ref, new)
        ok &= summary[case]["pass"]
        print(f"{case:14s} {'PASS' if summary[case]['pass'] else 'FAIL'}",
              {k: v for k, v in summary[case].items() if k in ("sections_compared", "format_additions", "wall_s", "error")})
    (out_dir / "regression_summary.json").write_text(json.dumps(summary, indent=1, default=float))
    print("REGRESSION", name, "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
