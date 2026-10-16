"""A236 analysis (BOUNDARY Section 2): arm h against each row's reference record, the identity row, and the unit /
regression logs.
  python3 a236_analyze.py          -> a236_summary.json
  python3 a236_analyze.py --refs   -> the reference rows' numbers only (printed)"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
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


MC = _load("a236_make_cfgs", HERE / "make_cfgs.py")
A34 = _load("a234_analyze", TA / "A234_p24_four_modules_v7" / "a234_analyze.py")
A29 = _load("a229_analyze", TA / "A229_p24_kd_band" / "a229_analyze.py")
ORA = A34.ORA
FALLING = ("f_N0_k0", "f_N0_k4", "f_N75_k0", "f_N75_k2", "f_N75_k4", "f_S75_k0", "r_N13_lm48", "r_F0_lm48", "r_F0_lm80",
           "l_N0_m80", "m4_l_m80_10us")
WIDE = ("w5_N0", "w20_N0", "w5_N75", "w30_S75h", "u_N0")      # re-applications: A229 saw up to 10 A between near-equal arms
ITEM2 = ("a_S75h_d2", "a_S75h_d20", "a_S75_d20")   # inside item 2's 40 us hold-off: above 200 A in the reference
SKIP = {"z_N0_10_t0": "z_N0_10", "z_N75_10_t0": "z_N75_10"}
KEYS = ("sections", "highoffs_last", "lowoffs_last", "turnons_last", "late_fires", "overlaps", "ipk_a")


def ev_row(f):
    m = A34.one(f)
    r = json.loads(Path(f).read_text())
    ev = r["cfg"].get("line_step") or r["cfg"].get("load_step")
    t0 = ev["t_us"] * 1e-6
    mods = [r] + r.get("modules_rest", [])
    on = [x for md in mods for x in md["turnons_last"] if x["t_s"] >= t0]
    m["k3_after"] = m["oracle_after"].get("K3", 0)
    m["new_after"] = m["oracle_after"].get("NEW", 0)
    m["on_vds_max_after_v"] = max((x["vds_v"] for x in on if x.get("vds_v") is not None), default=None)
    m["held"] = sum(bool(x.get("lo_pos")) and bool(x.get("early")) for x in on)
    s2 = r["cfg"].get("load_step2")
    t2 = s2["t_us"] * 1e-6 if s2 else t0            # re-applications: post_pk and Vo from the second step
    g = [e for md in mods for e in md.get("gate_offs_last", [])]
    if g:                                           # the gate-level peak (A229 / A235's measure), else A234's
        m["post_pk"] = max(e["i_max_a"] for e in g if e["t_s"] >= t2)
        m["peak_whole"] = max(e["i_max_a"] for e in g)
    elif s2:
        m["post_pk"] = max(e["i_a"] for md in mods for e in md["highoffs_last"] if e["t_s"] >= t2)
    if s2:
        m["vo_ext_mv"] = 1e3 * max((q["vo"] - 1.0 for q in r["sections"] if q["t_s"] >= t2), key=abs)
    return m


def skip_row(f, z):
    v = A29.skip_file(f, z)
    return {k: v[k] for k in ("vmin_a", "vmax_a", "in_band", "q1_run", "vo_end_v")}


def same(fa, fb):
    a, b = json.loads(Path(fa).read_text()), json.loads(Path(fb).read_text())
    return {k: a.get(k) == b.get(k) for k in KEYS}


def identity():
    logs = PROJECT / "tmp" / "logs"
    u = re.findall(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+)", (logs / "a236_unit.log").read_text())
    n_pass, n_fail = sum(int(p) for _, p, _ in u), sum(int(f) for _, _, f in u)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a236_reg{k[0]}.log").read_text())) for k in ("quick", "full")}
    o = {row: same(COS / f"run_o_{row}.json", MC.ref(row)) for row in MC.IDENT}
    return {"unit_pass": n_pass, "unit_fail": n_fail, "regression": reg, "o_rows": o,
            "e0": bool(n_pass == 111 and n_fail == 0 and all(reg.values()) and all(all(v.values()) for v in o.values()))}


def row(name, f):
    return skip_row(f, SKIP[name]) if name in SKIP else ev_row(f)


def refs():
    for name in MC.ROWS:
        v = row(name, MC.ref(name))
        print(name, {k: (round(x, 2) if isinstance(x, float) else x) for k, x in v.items()
                     if k in ("post_pk", "peak_whole", "vo_ext_mv", "oracle_after", "vds_v", "on_vds_max_after_v", "vmin_a", "vmax_a", "q1_run")})


def main():
    res = {"identity": identity(), "rows": {}}
    for name in MC.ROWS:
        h, ref = row(name, COS / f"run_h_{name}.json"), row(name, MC.ref(name))
        c = {}
        if name in SKIP:
            c["e4"] = bool(h["q1_run"] and abs(h["vmin_a"] - ref["vmin_a"]) <= 1.0 and abs(h["vmax_a"] - ref["vmax_a"]) <= 1.0)
        else:
            i_lim = ref["peak_whole"] + 2.0 if name in ITEM2 else A34.I_LIM
            c["e2"] = bool(A34_limits(h, i_lim) and (h["n_mod"] == 1 or h["f3"]))
            if name in FALLING:
                c["e1"] = bool(h["k3_after"] == 0 and h["new_after"] == 0)
            tol = 10.0 if name in WIDE else 2.0
            c["e3"] = bool(h["post_pk"] <= ref["post_pk"] + tol and h["new_after"] <= ref["new_after"]
                           and (name in WIDE or abs(h["vo_ext_mv"]) <= abs(ref["vo_ext_mv"]) + 1.0))
        res["rows"][name] = {"h": h, "ref": ref, "ref_record": str(MC.ref(name).relative_to(TA)), "criteria": c}
    res["criteria_main"] = {k: all(v["criteria"][k] for v in res["rows"].values() if k in v["criteria"])
                            for k in ("e1", "e2", "e3", "e4")}
    res["criteria_main"]["e0"] = res["identity"]["e0"]
    (HERE / "a236_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for n, v in res["rows"].items():
        h, r = v["h"], v["ref"]
        if n in SKIP:
            print(f"{n:14s} valleys {h['vmin_a']:+.2f}/{h['vmax_a']:+.2f} (ref {r['vmin_a']:+.2f}/{r['vmax_a']:+.2f}) | {v['criteria']}")
        else:
            print(f"{n:14s} post {h['post_pk']:.1f} (ref {r['post_pk']:.1f}) A | Vo {h['vo_ext_mv']:+.1f} ({r['vo_ext_mv']:+.1f}) mV | "
                  f"held {h['held']} | on V_DS {h['on_vds_max_after_v']:.1f} ({r['on_vds_max_after_v']:.1f}) | "
                  f"oracle {h['oracle_after']} (ref {r['oracle_after']}) | {v['criteria']}")
    print("identity", res["identity"]["e0"], "main", res["criteria_main"])


def A34_limits(h, i_lim):
    """A234's f1 without its NEW clause (NEW is e1 / e3's), with the peak limit i_lim."""
    return bool(all(s == "COMPLETED" for s in h["status"]) and h["peak_whole"] <= i_lim and h["vds_v"] <= A34.V_LIM
                and not h["overlaps"] and not h["shoot_on"] and all(abs(v - 1) <= A34.BAND for v in h["vo_end_v"]))


if __name__ == "__main__":
    refs() if "--refs" in sys.argv else main()
