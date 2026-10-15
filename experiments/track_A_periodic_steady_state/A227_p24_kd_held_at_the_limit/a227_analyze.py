"""A227 analysis (BOUNDARY Section 2). Skipping rows (held arm and z_N0_10_d0): a221_analyze.skip_row on a copy that
carries A221's circuit snapshot of the same row (a224_analyze.with_snap's reason) - h1. Re-applications: a223_analyze.one
against A224's d355 record of the row - h2. j1 from the unit and regression logs.
  python3 a227_analyze.py -> a227_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A24 = _load("a224_analyze", "A224_p24_damped_loop/a224_analyze.py")
A23, A21 = A24.A23, A24.A21
COS, R24 = HERE / "cosim", TA / "A224_p24_damped_loop" / "cosim"
NOLOAD_D0_A, TOL_POST = -22.8, 5.0                     # A226's d0 minimum; h2's tolerance against A224


def with_snap(f, row):
    r = json.loads(Path(f).read_text())
    src = json.loads((TA / "A221_p24_core_loss_and_pause" / "cosim" / f"run_{A24.Z_SRC[row]}.json").read_text())
    assert src["cfg"]["circuit"] == r["cfg"]["circuit"] and src["cfg"]["gate"] == r["cfg"]["gate"]
    r["snap_circuit"] = src["snap_circuit"]
    out = PROJECT / "tmp" / "a227_skip" / Path(f).name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r))
    return out


def identity():
    logs = PROJECT / "tmp" / "logs"
    u = re.findall(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+)", (logs / "a227_unit.log").read_text())
    n_pass, n_fail = sum(int(p) for _, p, _ in u), sum(int(f) for _, _, f in u)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a227_reg_{k}.log").read_text())) for k in ("quick", "full")}
    return {"unit_pass": n_pass, "unit_fail": n_fail, "regression": reg, "j1": bool(n_pass == 108 and n_fail == 0 and all(reg.values()))}


def main():
    res = {"identity": identity(), "skip": {}, "w": {}}
    for f in sorted(COS.glob("run_*.json")):
        name = f.stem[4:]
        row, arm = name.rsplit("_", 1)
        if name.startswith("z_"):
            v = A21.skip_row(with_snap(f, row))
            va = [y for p in v["true_valleys_a"].values() for y in p]
            c = v["criteria"]
            if row == "z_N0_0":
                c["h1"] = bool(c["s1"] and c["s2"] and va and min(va) >= NOLOAD_D0_A - 1.0)
            else:
                c["h1"] = bool(c["s1"] and c["s2"] and c["s3t"] and c["z1r"])
            v["true_valley_range_a"] = [min(va), max(va)] if va else None
            res["skip"][name] = v
        else:
            m, ref = A23.one(f), A23.one(R24 / f"run_{row}_d355.json")
            e1 = bool(m["status"] == "COMPLETED" and m["peak_whole"] <= A23.I_LIM and not m["overlaps"] and not m["shoot_on"]
                      and m["vds_whole"] <= A23.V_LIM and abs(m["vo_last_min_v"] - 1) <= A23.VO_BAND and abs(m["vo_last_max_v"] - 1) <= A23.VO_BAND)
            res["w"][name] = {"held": m, "a224": ref, "d_post_pk_a": m["post_pk"] - ref["post_pk"],
                              "criteria": {"h2": bool(e1 and abs(m["post_pk"] - ref["post_pk"]) <= TOL_POST)}}
    (HERE / "a227_summary.json").write_text(json.dumps(A23.A16.clean(res), indent=1) + "\n")
    print("j1", res["identity"])
    for n, v in res["skip"].items():
        print(f"{n:12s} Vo {v['vo_end_min_v']:.4f}..{v['vo_end_max_v']:.4f} true valleys {v['true_valley_range_a']} "
              f"({v['true_valleys_window_us']:.0f} us) resume {v['resume_i0_max_a']} | {v['criteria']}")
    for n, v in res["w"].items():
        m, ref = v["held"], v["a224"]
        print(f"{n:12s} post {ref['post_pk']:6.1f} -> {m['post_pk']:6.1f} A | whole {m['peak_whole']:.1f} | Vo {ref['vo_ext_mv']:+.1f} -> "
              f"{m['vo_ext_mv']:+.1f} mV | late {sum(ref['late_after'])} -> {sum(m['late_after'])} | {v['criteria']}")


if __name__ == "__main__":
    main()
