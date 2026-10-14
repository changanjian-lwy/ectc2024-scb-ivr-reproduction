"""A223 analysis (BOUNDARY Section 2). Per run: the whole-run numbers as A206 counts them (gate turn-off records: the
start-up, handover and whole-run peaks; shoot-throughs, forced edges, overlaps, V_DS) and, from the event (w / u rows: the re-application; k / l rows: the step) on: the peak (gate turn-off records),
Vo's extremes, rail 1's maximum (vin - vcs1), the late fires, Vo over the last 20 us, and the high-side on-times per
phase in bins after the event (turn-on to the next high-side turn-off). Per pair: c1-c4; j1 from the unit and
regression logs and k_N0_off against A222's record.
  python3 a223_analyze.py -> a223_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A16 = _load("a216_analyze", "A216_p24_skipped_rounds/a216_analyze.py")
COS = HERE / "cosim"
ARMS = ("off", "g25")
W_ROWS, LOAD_ROWS, LINE_ROWS = ("w0_N0", "w5_N0", "w20_N0", "w5_N75", "w30_S75h"), ("u_N0", "k_N0"), ("l_N0_p48", "l_N0_m80", "k_S75h")
I_LIM, V_LIM, VO_BAND, T_LAST = 200.0, 40.0, 0.01, 20e-6
TOL_A, TOL_MV = 1.0, 1.0
BINS_US = (0, 2, 4, 6, 8, 10, 15, 20)
ID_REF = TA / "A222_p24_v7_startup_trim" / "cosim" / "run_k_n_s_p62.json"
ID_KEYS = ("sections", "highoffs_last", "lowoffs_last", "turnons_last", "gate_offs_last", "late_fires", "ipk_a", "vds_max_v",
           "steps", "trim_final", "ton_final_lsb", "overlaps")


def t_event(cfg):
    for k in ("load_step2", "line_step", "load_step"):
        if cfg.get(k):
            return cfg[k]["t_us"] * 1e-6


def on_times(r, t0):
    """Mean high-side on-time (ns) per phase in the bins after t0: each turn-on to that phase's next high-side turn-off."""
    to, ho = r["turnons_last"], r["highoffs_last"]
    offs = {k: np.array(sorted(h["t_s"] for h in ho if h["phase"] == k)) for k in range(1, 5)}
    out = {}
    for a, b in zip(BINS_US[:-1], BINS_US[1:]):
        row = []
        for k in range(1, 5):
            ons = [x["t_s"] for x in to if x["phase"] == k and t0 + a * 1e-6 <= x["t_s"] < t0 + b * 1e-6]
            d = [(offs[k][j] - t) * 1e9 for t in ons if (j := np.searchsorted(offs[k], t, side="right")) < len(offs[k])]
            row.append(round(float(np.mean(d)), 2) if d else None)
        out[f"{a}-{b}us"] = row
    return out


def one(path):
    r = json.loads(Path(path).read_text())
    g_all, gs, tp = r["gate_offs_last"], r["gate_stats"], r["t_mode_p_s"]
    pk = lambda a, b: max((e["i_max_a"] for e in g_all if a <= e["t_s"] < b), default=None)
    sec = r["sections"]
    ts = np.array([q["t_s"] for q in sec]); vo = np.array([q["vo"] for q in sec])
    rail1 = np.array([q["vin_v"] - q["vcs_v"][0] for q in sec])
    te = t_event(r["cfg"])
    a = ts >= te
    last = ts >= ts[-1] - T_LAST
    k0 = int(np.searchsorted(ts, te, side="right")) - 1
    g = [e["i_max_a"] for e in r["gate_offs_last"] if e["t_s"] >= te]
    dev = vo[a] - 1.0
    return {"status": r["status"], "commit": r["provenance"]["git_commit"][:7],
            "sources_modified": r["provenance"]["cosim_sources_modified"], "wall_s": r["wall_s"],
            "peak_whole": pk(0.0, 1.0), "start_pk": pk(0.0, tp), "hand_pk": pk(tp, tp + 25e-6), "vds_whole": max(r["vds_max_v"]),
            "overlaps": r["overlaps"], "shoot_on": sum(gs["shoot_on"]), "forced": gs["forced"], "t_event_us": te * 1e6,
            "post_pk": max(g) if g else None, "vo_after_min_v": float(vo[a].min()), "vo_after_max_v": float(vo[a].max()),
            "vo_ext_mv": float(1e3 * dev[np.argmax(np.abs(dev))]), "rail1_after_max_v": float(rail1[a].max()),
            "rail1_before_v": float(rail1[k0]), "vo_last_min_v": float(vo[last].min()), "vo_last_max_v": float(vo[last].max()),
            "late_after": (np.array(sec[-1]["late"]) - np.array(sec[k0]["late"])).tolist(), "on_times_ns": on_times(r, te),
            "rel_gate": r["cfg"]["vff"].get("rel_gate")}


def before(off, g25, te):
    """c4: the sections before the event, bit for bit; else the first difference, the peaks and Vo there."""
    a, b = (json.loads(Path(f).read_text()) for f in (off, g25))
    sa = [q for q in a["sections"] if q["t_s"] < te]; sb = [q for q in b["sections"] if q["t_s"] < te]
    if sa == sb:
        return {"identical": True, "sections": len(sa), "c4": True}
    i = next((j for j, (x, y) in enumerate(zip(sa, sb)) if x != y), min(len(sa), len(sb)))
    pk = lambda r: max(e["i_max_a"] for e in r["gate_offs_last"] if e["t_s"] < te)
    va, vb = np.array([q["vo"] for q in sa]), np.array([q["vo"] for q in sb])
    ok = abs(pk(a) - pk(b)) <= TOL_A and vb.min() >= va.min() - 1e-3 and vb.max() <= va.max() + 1e-3
    return {"identical": False, "first_diff_us": sa[i]["t_s"] * 1e6 if i < len(sa) else None, "pk_off": pk(a), "pk_g25": pk(b),
            "vo_off": [float(va.min()), float(va.max())], "vo_g25": [float(vb.min()), float(vb.max())], "c4": bool(ok)}


def identity():
    logs = PROJECT / "tmp" / "logs"
    u = re.findall(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+)", (logs / "a223_unit.log").read_text())
    n_pass, n_fail = sum(int(p) for _, p, _ in u), sum(int(f) for _, _, f in u)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a223_reg_{k}.log").read_text())) for k in ("quick", "full")}
    f = COS / "run_k_N0_off.json"
    same = None
    if f.exists():
        x, y = json.loads(f.read_text()), json.loads(ID_REF.read_text())
        same = {k: x.get(k) == y.get(k) for k in ID_KEYS}
    return {"unit_pass": n_pass, "unit_fail": n_fail, "regression": reg, "k_N0_off_vs_A222": same,
            "j1": bool(n_pass == 106 and n_fail == 0 and all(reg.values()) and same and all(same.values()))}


def main():
    runs = {f.stem[4:]: one(f) for f in sorted(COS.glob("run_*.json"))}
    pairs = {}
    for row in W_ROWS + LOAD_ROWS + LINE_ROWS:
        o, g = runs.get(f"{row}_off"), runs.get(f"{row}_g25")
        if not (o and g):
            continue
        p = {"d_post_pk_a": g["post_pk"] - o["post_pk"], "d_vo_ext_mv": g["vo_ext_mv"] - o["vo_ext_mv"],
             "before": before(COS / f"run_{row}_off.json", COS / f"run_{row}_g25.json", o["t_event_us"] * 1e-6)}
        c = {"c4": p["before"]["c4"]}
        if row in W_ROWS:
            c["c1"] = bool(g["status"] == "COMPLETED" and g["peak_whole"] <= I_LIM and not g["overlaps"] and not g["shoot_on"]
                           and g["vds_whole"] <= V_LIM and abs(g["vo_last_min_v"] - 1) <= VO_BAND and abs(g["vo_last_max_v"] - 1) <= VO_BAND)
        elif row in LOAD_ROWS:
            c["c2"] = bool(g["post_pk"] <= o["post_pk"] + TOL_A and abs(g["vo_ext_mv"]) <= abs(o["vo_ext_mv"]) + TOL_MV)
        else:
            c["c3"] = bool(abs(p["d_post_pk_a"]) <= TOL_A and abs(p["d_vo_ext_mv"]) <= TOL_MV)
        p["criteria"] = c
        pairs[row] = p
    res = {"identity": identity(), "runs": runs, "pairs": pairs}
    (HERE / "a223_summary.json").write_text(json.dumps(A16.clean(res), indent=1) + "\n")
    print("j1", res["identity"])
    for row, p in pairs.items():
        o, g = runs[f"{row}_off"], runs[f"{row}_g25"]
        print(f"{row:9s} whole {o['peak_whole']:6.1f} -> {g['peak_whole']:6.1f} | post {o['post_pk']:6.1f} -> {g['post_pk']:6.1f} A | "
              f"Vo {o['vo_ext_mv']:+6.1f} -> {g['vo_ext_mv']:+6.1f} mV | rail1 {o['rail1_after_max_v']:5.2f} -> {g['rail1_after_max_v']:5.2f} V | "
              f"late {sum(o['late_after'])} -> {sum(g['late_after'])} | before {'same' if p['before']['identical'] else p['before'].get('first_diff_us')} | {p['criteria']}")


if __name__ == "__main__":
    main()
