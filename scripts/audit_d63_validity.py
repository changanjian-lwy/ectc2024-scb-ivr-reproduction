"""D81 check 2: what D63's validity flags find in the archived valley-map outputs.

Reruns the archived D63-family outputs (D63's validation + design map, A117, A118, A124, A134, A135 predictions)
with the current code, writing into tmp/d81_d63/ (the archive is not touched), and reports:
  A  value check: every archived value reproduced? the rows that differ, and whether those runs had diverged;
     per simulate() run the flags (ith_rail, past_level, ...) and the warm-up check (steady_check);
  B  the I_th table below 8 V: D57's threshold at 5.0-7.5 V (cached in diagnostics/D81_ith_below_8v.json, ~2 min),
     prepended to every table that starts at 8 V (a table scaled as A132's d63_design gets the same scale); the
     outputs rerun and compared with A on outcome-level fields;
  C  A134 / A135 (their own warm-up loops): is the state periodic over the recorded periods before the step?

    python3 -m scripts.audit_d63_validity      (writes diagnostics/D81_d63_validity.json; ~15 min)
"""
from __future__ import annotations

import collections
import contextlib
import importlib.util
import io
import json
import pathlib
import sys
from multiprocessing import Pool

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np  # noqa: E402

import scb_ivr.p24_valley_map as vm  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
TMP = ROOT / "tmp" / "d81_d63"
TA = "experiments/track_A_periodic_steady_state/"
JOBS = {"D63": ("scripts/p24_valley_map.py", "symbolic_derivations/03_P24_native/diagnostics/D63_valley_map.json"),
        "A117": (TA + "A117_p24_one_mhz_line_slew_cs/a117_predict.py", TA + "A117_p24_one_mhz_line_slew_cs/a117_predictions.json"),
        "A118": (TA + "A118_p24_floor_turn_off/a118_predict.py", TA + "A118_p24_floor_turn_off/a118_predictions.json"),
        "A124": (TA + "A124_p24_two_point_five_mhz/a124_predict.py", TA + "A124_p24_two_point_five_mhz/a124_predictions.json"),
        "A134": (TA + "A134_p24_inductance_cap_lock/a134_predict.py", TA + "A134_p24_inductance_cap_lock/a134_predictions.json"),
        "A135": (TA + "A135_p24_relative_cap/a135_predict.py", TA + "A135_p24_relative_cap/a135_predictions.json")}
BASE_L = (7.3333333e-9 / 2.5, 7.3333333e-9, 1.4666667e-9)       # 2.5 MHz, 1 MHz, 5 MHz designs
OUTK = ("outcome", "peak_max_a", "peak_a", "extreme_mv", "back_us", "ph1_depth_a", "ph1_crossing_periods", "ph1_periods",
        "diverged_us")

_write = pathlib.Path.write_text


def run_script(name, out_dir):
    """The archived script's main() with its project JSON outputs redirected to out_dir; returns the new output."""
    path, arch = JOBS[name]

    def wt(self, data, *a, **k):
        if self.suffix == ".json" and ROOT in self.parents:
            return _write(out_dir / self.name, data, *a, **k)
        return _write(self, data, *a, **k)

    out_dir.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location(f"d81_{name}", ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str((ROOT / path).parent))
    pathlib.Path.write_text = wt
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(mod)
            mod.main()
    finally:
        pathlib.Path.write_text = _write
    return json.loads((out_dir / pathlib.Path(arch).name).read_text()), mod


def diff_values(old, new, path=""):
    """Paths whose archived value differs (new keys are ignored)."""
    if isinstance(old, dict):
        for k, v in old.items():
            yield from diff_values(v, new.get(k) if isinstance(new, dict) else None, f"{path}.{k}")
    elif isinstance(old, list) and isinstance(new, list) and len(old) == len(new):
        for i, (a, b) in enumerate(zip(old, new)):
            yield from diff_values(a, b, f"{path}[{i}]")
    elif old != new:
        yield path


def outcome_rows(x, path=""):
    if isinstance(x, dict):
        if any(k in x for k in OUTK):
            yield path, {k: x[k] for k in OUTK if k in x}
        for k, v in x.items():
            if isinstance(v, (dict, list)):
                yield from outcome_rows(v, f"{path}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from outcome_rows(v, f"{path}[{i}]")


def pass_a():
    runs, periods = [], collections.Counter()
    sim, per = vm.simulate, vm.ValleyMap.period

    def simulate(d, *a, **k):
        out = sim(d, *a, **k)
        fl = collections.Counter(f for r in out for f in r.get("flags", ()))
        runs.append({"flags": dict(fl), "diverged": bool(out[-1].get("diverged")),
                     "first_flag_us": {f: next(r["t"] for r in out if f in r["flags"]) * 1e6 for f in fl},
                     "t_end_us": out[-1]["t"] * 1e6, "warm": out[0].get("warm")})
        return out

    def period(self, *a, **k):
        r = per(self, *a, **k)
        periods["all"] += 1
        for f in r["flags"]:
            periods[f] += 1
        return r

    vm.simulate, vm.ValleyMap.period = simulate, period
    rep = {}
    try:
        for name in JOBS:
            runs.clear(); periods.clear()
            new, _ = run_script(name, TMP / "A")
            old = json.loads((ROOT / JOBS[name][1]).read_text())
            bad = sorted(set(p.split(".model")[0] for p in diff_values(old, new)))
            olds = dict(outcome_rows(old))
            rep[name] = {
                "values_identical": not bad,
                "differing_rows": [{"row": p, "archived_diverged_us": (olds.get(p + ".model") or olds.get(p) or {}).get("diverged_us"),
                                    "archived_outcome": (olds.get(p) or {}).get("outcome")} for p in bad],
                "periods": dict(periods),
                "simulate_runs": len(runs),
                "runs_flagged": sum(1 for r in runs if r["flags"]),
                "runs_flagged_not_diverged": [{"flags": r["flags"], "first_flag_us": r["first_flag_us"]}
                                              for r in runs if r["flags"] and not r["diverged"]],
                "flags_in_diverged_runs_us_before_end": sorted(round(r["t_end_us"] - min(r["first_flag_us"].values()), 2)
                                                               for r in runs if r["flags"] and r["diverged"]),
                "warm_cycles": dict(collections.Counter(str(r["warm"]["cycle"]) for r in runs if r["warm"])),
                "warm_unsettled": [r["warm"]["drift"] for r in runs if r["warm"] and not r["warm"]["settled"]]}
            print(f"A {name}: identical {rep[name]['values_identical']}, rows differing {len(bad)}, periods {dict(periods)}",
                  flush=True)
    finally:
        vm.simulate, vm.ValleyMap.period = sim, per
    return rep


def _ext_job(lf):
    r, a, b = vm.thresholds(lf, rails=np.arange(5.0, 7.51, 0.5))
    _, a8, b8 = vm.thresholds(lf, rails=np.array([8.0, 8.5]))
    return {"lf": lf, "rails": [float(x) for x in r], "t13": list(a), "t4": list(b), "t13_8": list(a8), "t4_8": list(b8)}


def ith_below_8v():
    path = DIAG / "D81_ith_below_8v.json"
    if path.exists():
        return json.loads(path.read_text())
    with Pool(3) as p:
        ext = p.map(_ext_job, BASE_L)
    path.write_text(json.dumps(ext, indent=1) + "\n")
    return ext


def pass_b(ext):
    init = vm.ValleyMap.__init__
    unmatched = []

    def patched(self, d):
        init(self, d)
        rails, t13, t4 = self._ith
        if rails[0] != 8.0:
            return
        err, e, s = min(((abs(t13[0] / e["t13_8"][0] - t4[0] / e["t4_8"][0])
                          + abs(t13[1] / t13[0] - e["t13_8"][1] / e["t13_8"][0]), e, t13[0] / e["t13_8"][0]) for e in ext),
                        key=lambda x: x[0])
        if err > 1e-6:
            unmatched.append(err)
            return
        self._ith = (np.concatenate([e["rails"], rails]), np.concatenate([np.array(e["t13"]) * s, t13]),
                     np.concatenate([np.array(e["t4"]) * s, t4]))

    vm.ValleyMap.__init__ = patched
    rep = {}
    try:
        for name in JOBS:
            unmatched.clear()
            new, _ = run_script(name, TMP / "B")
            ref = dict(outcome_rows(json.loads((TMP / "A" / pathlib.Path(JOBS[name][1]).name).read_text())))
            ext_rows = dict(outcome_rows(new))
            ch = {}
            for p, a in ref.items():
                b = ext_rows.get(p, {})
                d = {k: [a[k], b.get(k)] for k in a if a[k] != b.get(k)}
                if d:
                    ch[p] = d
            rep[name] = {"rows": len(ref), "changed": ch, "tables_not_matched": len(unmatched)}
            print(f"B {name}: rows {len(ref)}, changed {len(ch)}, tables not matched {len(unmatched)}", flush=True)
    finally:
        vm.ValleyMap.__init__ = init
    return rep


def pass_c():
    hist, per = [], vm.ValleyMap.period

    def period(self, s, vin, i_step, *a, **k):
        t0 = s["t"]
        r = per(self, s, vin, i_step, *a, **k)
        hist.append((t0, vm.steady_record(s, r)))           # the state steady_check compares (control memory included)
        return r

    def lag(h):
        return vm.steady_lag(h, len(h) // 2)

    vm.ValleyMap.period = period
    rep = {}
    try:
        for name in ("A134", "A135"):
            path, arch = JOBS[name]
            spec = importlib.util.spec_from_file_location(f"d81c_{name}", ROOT / path)
            mod = importlib.util.module_from_spec(spec)
            with contextlib.redirect_stdout(io.StringIO()):
                spec.loader.exec_module(mod)
            lags, bad = collections.Counter(), {}
            for key in json.loads((ROOT / arch).read_text())["runs"]:
                arm, row = key.split("_", 1)
                m = int(arm[1:]) / 100
                hist.clear()
                mod.run(m, mod.ARMS[arm[0]](m) if name == "A134" else mod.VffRTL(**mod.ARMS[arm[0]](m)), row)
                start = max(i for i, (t, _) in enumerate(hist) if t == 0.0)       # the recorded segment
                pre = [h for t, h in hist[start:] if t < 20e-6]                  # both step at 20 us
                p = lag(pre)
                lags[str(p)] += 1
                if p is None:
                    d1 = {k: max(abs(a - b) for j in range(1, len(pre)) for a, b in zip(pre[j][k], pre[j - 1][k]))
                          for k in vm.STEADY_TOL}
                    bad.setdefault(arm, {"rows": 0, "periods_before_step": len(pre), "drift_lag1": d1})["rows"] += 1
            rep[name] = {"lags": dict(lags), "unsettled_by_arm": bad}
            print(f"C {name}: lags {dict(lags)}, unsettled arms {list(bad)}", flush=True)
    finally:
        vm.ValleyMap.period = per
    return rep


def main():
    out = {"what": "D81 check 2: D63 validity flags on the archived valley-map outputs (tmp/d81_d63 holds the reruns)",
           "A_current_code": pass_a()}
    ext = ith_below_8v()
    out["ith_below_8v"] = {f"{e['lf'] * 1e9:.4f} nH": {"rails": e["rails"], "t13": e["t13"], "t13_at_8v": e["t13_8"][0]}
                           for e in ext}
    out["B_threshold_below_8v"] = pass_b(ext)
    out["C_prestep_periodicity"] = pass_c()
    (DIAG / "D81_d63_validity.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("wrote", (DIAG / "D81_d63_validity.json").relative_to(ROOT))


if __name__ == "__main__":
    main()
