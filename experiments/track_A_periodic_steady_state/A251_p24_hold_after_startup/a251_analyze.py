"""A251 analysis (BOUNDARY Section 2). Arm z against the final configuration: A246's records on its matrix (stage 1:
A246's one1, A240's q1-q5; stage 2: A236's row, A246's g9 tolerances), arm h on A245's start-ups (A245's one and
g1-g3). z3: before the hold, arm z equals its reference turn-on for turn-on (master module). Also arm h on the
start-ups against A245's run_r_ (the floor on start-ups, never run before). g0: unit tests and regression logs.
  python3 a251_analyze.py -> a251_summary.json"""
from __future__ import annotations

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


MC = _load("a251_make_cfgs", HERE / "make_cfgs.py")
A46 = _load("a246_analyze", TA / "A246_p24_held_report_floor" / "a246_analyze.py")
A45 = _load("a245_analyze", TA / "A245_p24_reverse_conduction_delay" / "a245_analyze.py")
A36, H46, R45 = A46.A36, TA / "A246_p24_held_report_floor" / "cosim", TA / "A245_p24_reverse_conduction_delay" / "cosim"
PK_TOL, Q4_N0, UNIT_N, I_LIM = 2.0, 171.5, 144, 200.0


def t_hold(d):
    """The HOLD_N-th phase-1 turn-on after mode P's entry (s), or None."""
    on = sorted(x["t_s"] for x in d["turnons_last"] if x["phase"] == 1 and x["t_s"] > d["t_mode_p_s"])
    return on[MC.HOLD_N - 1] if len(on) >= MC.HOLD_N else None


def identical_before(fz, fref):
    dz, dr = json.loads(Path(fz).read_text()), json.loads(Path(fref).read_text())
    th = t_hold(dz)
    lim = (th if th is not None else dz["t_end_s"]) - 0.5e-6
    a = [(x["t_s"], x["phase"]) for x in dz["turnons_last"] if x["t_s"] < lim]
    b = [(x["t_s"], x["phase"]) for x in dr["turnons_last"] if x["t_s"] < lim]
    return {"t_hold_us": None if th is None else th * 1e6, "z3": a == b, "n": len(a),
            "dt_final_ns": dz["dt_pred_final_ns"], "dt_final_ref_ns": dr["dt_pred_final_ns"]}


def stage1(row, fz, fh):
    (z, qz), (h, qh) = A46.one1(fz, row.split("_k")[0] if "_k" in row[-3:] else row), \
        A46.one1(fh, row.split("_k")[0] if "_k" in row[-3:] else row)
    c = {"z2": bool(z["peak_after_t0"] <= h["peak_after_t0"] + PK_TOL and z["vo_min_v"] >= h["vo_min_v"] - 1e-3)}
    if row.startswith("p_N0_100k"):
        c["z1"] = bool(z["peak_after_t0"] <= Q4_N0)
    if row.endswith("_1000k"):
        c["z4"] = bool(qz["q1"] and qz["q2"])
    keep = ("peak_after_t0", "peak_whole", "vo_min_v")
    return {"z": {k: z.get(k) for k in keep} | {"q": qz}, "h": {k: h.get(k) for k in keep} | {"q": qh}, "criteria": c}


def stage2(row, fz, fh):
    z, h = A36.row(row, fz), A36.row(row, fh)
    if row in A36.SKIP:
        c = {"z2": bool(abs(z["vmin_a"] - h["vmin_a"]) <= 1.0 and abs(z["vmax_a"] - h["vmax_a"]) <= 1.0)}
        keep = ("vmin_a", "vmax_a")
    else:
        tol = 10.0 if row in A46.WIDE else PK_TOL
        c = {"z2": bool(z["post_pk"] <= h["post_pk"] + tol and z["new_after"] <= h["new_after"]
                        and (row in A46.WIDE or abs(z["vo_ext_mv"]) <= abs(h["vo_ext_mv"]) + 1.0))}
        keep = ("post_pk", "new_after", "vo_ext_mv", "peak_whole")
    return {"z": {k: z.get(k) for k in keep}, "h": {k: h.get(k) for k in keep}, "criteria": c}


def start_crit(x, ref):
    return {"in_band": bool(x["dev_end_v"] <= A45.BAND_V and max(x["runs_tail"][1:]) < A45.MC.REV_N),
            "limits": bool(x["peak_a"] <= I_LIM and x["vds_max_v"] <= 40.0 and x["overlaps"] == 0),
            "vo": bool(x["vo_min"] >= min(A45.VO_LO, ref["vo_min"]) and x["vo_max"] <= max(A45.VO_HI, ref["vo_max"]))}


def start(row):
    fz, fh, fr = COS / f"run_z_{row}.json", COS / f"run_h_{row}.json", R45 / f"run_r_{row}.json"
    if not fh.exists():
        return None
    h, r = A45.one(fh), A45.one(fr)
    keep = ("dev_end_v", "t_in_band_us", "peak_a", "vds_max_v", "vo_min", "vo_max", "late", "new", "dt_final_ns")
    ch = start_crit(h, r)
    if not fz.exists():                                   # arm z stopped (RESULTS): arm h alone, against A245's run_r_
        return {"h": {k: h[k] for k in keep} | {"crit": ch}, "r": {k: r[k] for k in keep}, "criteria": {"h_ok": all(ch.values())}}
    z = A45.one(fz)
    cz = start_crit(z, r)
    c = {"z2": bool(all(cz.values()) or not all(ch.values())) and bool(z["peak_a"] <= h["peak_a"] + PK_TOL
                                                                      and z["dev_end_v"] <= max(h["dev_end_v"] + 0.2, A45.BAND_V)),
         "h_ok": all(ch.values())}
    return {"z": {k: z[k] for k in keep} | {"crit": cz}, "h": {k: h[k] for k in keep} | {"crit": ch},
            "r": {k: r[k] for k in keep}, "identity": identical_before(fz, fh), "criteria": c}


def matrix():
    out = {}
    for row in MC.STAGE1 + MC.STAGE2:
        fz, fh = COS / f"run_z_{row}.json", H46 / f"run_h_{row}.json"
        if not fz.exists():
            out[row] = None; continue
        x = stage1(row, fz, fh) if row in MC.STAGE1 else stage2(row, fz, fh)
        x["identity"] = identical_before(fz, fh)
        out[row] = x
    for row, ks in MC.POS.items():
        for k in ks:
            fz, fh = COS / f"run_cz_{row}_k{k}.json", H46 / f"run_ch_{row}_k{k}.json"
            name = f"{row}_k{k}"
            if not fz.exists():
                out[name] = None; continue
            x = stage1(row, fz, fh)
            x["identity"] = identical_before(fz, fh)
            out[name] = x
    return out


def identity_logs():
    logs = PROJECT / "tmp" / "logs"
    u = re.findall(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+)", (logs / "a251_unit.log").read_text())
    n_pass, n_fail = sum(int(p) for _, p, _ in u), sum(int(f) for _, _, f in u)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a251_reg_{k}.log").read_text())) for k in ("quick", "full")}
    return {"unit_pass": n_pass, "unit_fail": n_fail, "regression": reg,
            "g0": bool(n_pass == UNIT_N and n_fail == 0 and all(reg.values()))}


def main():
    res = {"g0": identity_logs(), "matrix": matrix(), "start": {r: start(r) for r in MC.START}}
    rows = [x for x in list(res["matrix"].values()) + list(res["start"].values()) if x]
    crit = {"g0": res["g0"]["g0"]}
    for k in ("z1", "z2", "z4", "h_ok"):
        v = [x["criteria"][k] for x in rows if k in x["criteria"]]
        crit[k] = all(v) if v else None
    crit["z3"] = all(x["identity"]["z3"] for x in rows if "identity" in x)
    crit["complete"] = len(rows) == len(res["matrix"]) + len(res["start"])
    crit["z_rows"] = sum("z" in x for x in rows)
    res["criteria"] = crit
    (HERE / "a251_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for name, x in list(res["matrix"].items()) + list(res["start"].items()):
        if not x:
            continue
        bad = [k for k, v in x["criteria"].items() if v is False] + ([] if x.get("identity", {}).get("z3", True) else ["z3"])
        h, key = x["h"], next(k for k in ("peak_after_t0", "post_pk", "dev_end_v", "vmin_a") if k in x["h"])
        z = f"{x['z'][key]:.4g}" if "z" in x else "-"
        print(f"{name:20s} {key} {z} (h {h[key]:.4g}) " + " ".join(bad))
    print("criteria", crit)


if __name__ == "__main__":
    main()
