"""A205 analysis (registered as A199, see BOUNDARY): LTspice replays (scripts/p24_replay.py) of the three snapshot records, by the registered rule.
- N0_steady: mode S window, snapshots 0-3; settled mode P window, snapshots 0-5 (and 0-2 again with rph "zero").
- N0_step / N75_step: S and S + 1 (S = the last snapshot before the step) and P - 2, P - 1, P (P = the last snapshot
  at or before the plant's largest physical peak after the step).
Each replay covers two phase-1 periods from its snapshot. Criteria per replay (LTspice minus plant):
 c0 the start state arrives (node voltages within 5 mV, phase currents within 0.05 A);
 c1 every high-side turn-off peak within 2.0 A;
 c2 one period later: phase currents within 1.5 A, flying-capacitor voltages within 20 mV, Vo within 0.5 mV;
 c3 every switch's largest V_DS over the section interval within 1.5 V;
 c4 every hard high-side turn-on: channel start within 0.3 ns and V_DS there within 1.0 V.
Post hoc diagnostics (no criteria; DIAG): the first three settled snapshots again with the low sides' turn-on
resistance at 0.3 and 1.0 ohm in LTspice (the plant's commands unchanged), to trace the one-period difference.
  python3 a205_analyze.py identity   the records' sections against A194's N0 record made before the snapshot code
  python3 a205_analyze.py run [--jobs 4]   the missing replays -> replays/<run>_<window>_k<k>_<rph>.json
  python3 a205_analyze.py            -> a205_summary.json"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "scripts"))
REP = HERE / "replays"
LIM = {"v0": 5e-3, "i0": 0.05, "peak": 2.0, "di": 1.5, "dvcs": 20e-3, "dvo": 0.5e-3, "vds": 1.5, "t_on": 0.3e-9, "v_on": 1.0}
PERIODS = 2


def groups(rec):
    """Snapshot indices by window (a gap above 5 us starts a new one)."""
    out, last = [], None
    for k, s in enumerate(rec["snaps"]):
        if last is None or s["t_s"] - last > 5e-6:
            out.append([])
        out[-1].append(k)
        last = s["t_s"]
    return out


def plan(name, rec):
    """[(label, k, rph)] by the registered rule."""
    g = groups(rec)
    if name == "N0_steady":
        assert len(g) == 2 and len(g[0]) >= 6 and len(g[1]) >= 8, [len(x) for x in g]
        return ([("S", g[0][q], "match") for q in range(4)] + [("P", g[1][q], "match") for q in range(6)]
                + [("P", g[1][q], "zero") for q in range(3)])
    ts = rec["cfg"]["line_step"]["t_us"] * 1e-6
    snaps = rec["snaps"]
    s = max(k for k in g[0] if snaps[k]["t_s"] < ts)
    pk = max((e for e in rec["gate_offs_last"] if e["t_s"] >= ts), key=lambda e: e["i_max_a"])
    p = max(k for k in g[0] if snaps[k]["t_s"] <= pk["t_s"] + 1e-9)
    ks = sorted({s, s + 1, p - 2, p - 1, p})
    assert ks[-1] + PERIODS <= g[0][-1], "the snapshot window ends before the last replay"
    return [("T", k, "match") for k in ks]


DIAG = (0.3, 1.0)                        # ohm: low-side turn-on resistance in the diagnostic replays


def diag_plan(name, rec):
    g = groups(rec)
    return [("P", g[1][q], "match", r) for q in range(3) for r in DIAG] if name == "N0_steady" else []


def fname(name, label, k, rph, r_ls=None):
    return f"{name}_{label}_k{k}_{rph}" + ("" if r_ls is None else f"_ls{r_ls:g}".replace(".", "p")) + ".json"


def one(arg):
    name, label, k, rph, r_ls = arg
    import p24_replay as R
    rec = R.load(HERE / "cosim" / f"run_{name}.json")
    o = R.replay(rec, k, PERIODS, rph, tag=f"a205_{name}_{label}", r_on_ls=r_ls)
    (REP / fname(name, label, k, rph, r_ls)).write_text(json.dumps(o, indent=1) + "\n")
    return f"{name} {label} {'' if r_ls is None else f'ls {r_ls} '}" + R.brief(o)


def run(jobs):
    REP.mkdir(exist_ok=True)
    todo = []
    for f in sorted((HERE / "cosim").glob("run_*.json")):
        name = f.stem[4:]
        rec = json.loads(f.read_text())
        todo += [(name, lab, k, rph, None) for lab, k, rph in plan(name, rec) if not (REP / fname(name, lab, k, rph)).exists()]
        todo += [(name, lab, k, rph, r) for lab, k, rph, r in diag_plan(name, rec) if not (REP / fname(name, lab, k, rph, r)).exists()]
    print(len(todo), "replays to run", flush=True)
    with ProcessPoolExecutor(jobs) as ex:
        for line in ex.map(one, todo):
            print(line, flush=True)


def judge(o):
    s1 = o["state"][0]
    pk = [abs(x["lt_a"] - x["plant_a"]) for x in o["peaks"] if x["plant_a"] is not None]
    vd = [abs(a - b) for r in o["vds_max"] if r["plant_v"] for a, b in zip(r["lt_v"], r["plant_v"])]
    hard = [x for x in o["turnons"] if x["plant_t_act_s"] is not None]
    t_on = [abs(x["lt_t_act_s"] - x["plant_t_act_s"]) if x["lt_t_act_s"] is not None else float("inf") for x in hard]
    v_on = [abs(x["lt_vds_act_v"] - x["plant_vds_act_v"]) if x["lt_vds_act_v"] is not None else float("inf") for x in hard]
    vsg = [a - b for r in o["vds_max"] if r["plant_v"] for a, b in zip(r["lt_v"], r["plant_v"])]
    ls, w = o["loss"], lambda uj: sum(uj) * 1e-6 / o["loss"]["period_s"]
    mean = lambda xs: sum(xs) / len(xs) if xs else None
    first = {}                                       # each phase's first hard turn-on in the replay (the least drifted)
    for x in hard:
        first.setdefault(x["phase"], x)
    m = {"start_v": o["start_err_v_max"], "start_i": o["start_err_i_max"], "peak_max": max(pk, default=None),
         "peak_signed": [x["lt_a"] - x["plant_a"] for x in o["peaks"] if x["plant_a"] is not None],
         "di": s1["di"], "dvcs": s1["dvcs"], "dvo": s1["dv"]["out"], "di_2": o["state"][1]["di"] if len(o["state"]) > 1 else None,
         "valley_signed": [x["lt_a"] - x["plant_a"] for x in o["valleys"]], "vds_max": max(vd, default=None),
         "t_on_max": max(t_on, default=None), "v_on_max": max(v_on, default=None), "hard_turnons": len(hard),
         "turnons": len(o["turnons"]), "plant_peak_max": max((x["plant_a"] for x in o["peaks"] if x["plant_a"] is not None), default=None),
         "lt_peak_max": max((x["lt_a"] for x in o["peaks"]), default=None),
         "vds_signed_extremes": [min(vsg), max(vsg)] if vsg else None,
         "vds_lt_max": max((v for r in o["vds_max"] for v in r["lt_v"]), default=None),
         "vds_plant_max": max((v for r in o["vds_max"] if r["plant_v"] for v in r["plant_v"]), default=None),
         "first_turn_on": {str(ph): {"dt_ns": 1e9 * (x["lt_t_act_s"] - x["plant_t_act_s"]), "dv_v": x["lt_vds_act_v"] - x["plant_vds_act_v"]}
                           for ph, x in first.items() if x["lt_t_act_s"] is not None},
         "loss_w": {"lt_channel": w(ls["lt_channel_uj"]), "lt_high": w(ls["lt_channel_uj"][:4]), "lt_low": w(ls["lt_channel_uj"][4:]),
                    "lt_rph": w(ls["lt_rph_uj"]), "plant_r": w(ls["plant_r_uj"]),
                    "plant_edge": w(ls["plant_edge_uj"]) if ls["plant_edge_uj"] else None,
                    "plant_rev": w(ls["plant_rev_uj"]) if ls["plant_rev_uj"] else None},
         "ls_turn_on": {"e_uj": mean([x["e_uj"] for x in ls["ls_turn_on"]]), "rev_nvs": mean([x["rev_nvs"] for x in ls["ls_turn_on"]]),
                        "r_only_nvs": mean([x["r_only_nvs"] for x in ls["ls_turn_on"]]), "i_a": mean([x["i_a"] for x in ls["ls_turn_on"]])},
         "period_ns": 1e9 * ls["period_s"], "vo_mean_v": ls["vo_mean_v"], "r_on_ls": o.get("r_on_ls")}
    ok = lambda v, lim: v is not None and v <= lim
    m["criteria"] = {"c0": o["start_err_v_max"] <= LIM["v0"] and o["start_err_i_max"] <= LIM["i0"],
                     "c1": ok(m["peak_max"], LIM["peak"]),
                     "c2": max(abs(x) for x in s1["di"]) <= LIM["di"] and max(abs(x) for x in s1["dvcs"]) <= LIM["dvcs"]
                     and abs(s1["dv"]["out"]) <= LIM["dvo"],
                     "c3": ok(m["vds_max"], LIM["vds"]),
                     "c4": (not hard) or (max(t_on) <= LIM["t_on"] and max(v_on) <= LIM["v_on"])}
    return m


def identity():
    ref = json.loads((TA / "A194_p24_final_plant_random_stimuli" / "cosim" / "run_r20_N0_25_rise.json").read_text())
    for name, t_stop in (("N0_steady", 296.9e-6), ("N0_step", 499.9e-6)):
        f = HERE / "cosim" / f"run_{name}.json"
        if not f.exists():
            continue
        r = json.loads(f.read_text())
        a = [q for q in r["sections"] if q["t_s"] < t_stop]
        b = [q for q in ref["sections"] if q["t_s"] < t_stop]
        same = len(a) == len(b) and all(x[k] == y[k] for x, y in zip(a, b) for k in ("t_s", "v", "i", "vo", "ton_lsb"))
        print(f"{name}: {len(a)} sections before {t_stop * 1e6:.1f} us, equal to A194 r20's: {same}")


def main():
    res = {}
    for f in sorted((HERE / "cosim").glob("run_*.json")):
        name = f.stem[4:]
        rec = json.loads(f.read_text())
        rows = {}
        for lab, k, rph in plan(name, rec):
            p = REP / fname(name, lab, k, rph)
            if p.exists():
                rows[f"{lab}_k{k}_{rph}"] = judge(json.loads(p.read_text()))
        diag = {}
        for lab, k, rph, r in diag_plan(name, rec):
            p = REP / fname(name, lab, k, rph, r)
            if p.exists():
                m = judge(json.loads(p.read_text()))
                m.pop("criteria")                                   # diagnostics are not judged
                diag[f"{lab}_k{k}_{rph}_ls{r:g}"] = m
        res[name] = {"snapshots": len(rec["snaps"]), "commit": rec["provenance"]["git_commit"][:7],
                     "sources_modified": rec["provenance"]["cosim_sources_modified"], "replays": rows,
                     "criteria": {k: v["criteria"] for k, v in rows.items()}, "diagnostics": diag}
    (HERE / "a205_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    f1 = lambda xs: " ".join(f"{x:+.2f}" for x in xs)
    for name, r in res.items():
        for k, m in list(r["replays"].items()) + [("diag " + a, b) for a, b in r["diagnostics"].items()]:
            print(f"{name:10s} {k:14s} start {m['start_v'] * 1e3:.2f} mV / {m['start_i']:.3f} A | peaks {f1(m['peak_signed'])} A "
                  f"(plant max {m['plant_peak_max']:.1f}) | 1 period di {f1(m['di'])} A dVcs {f1([x * 1e3 for x in m['dvcs']])} mV "
                  f"dVo {m['dvo'] * 1e3:+.3f} mV | V_DS {m['vds_max']} V | turn-on {m['hard_turnons']}/{m['turnons']} hard, "
                  f"t {None if m['t_on_max'] is None else round(m['t_on_max'] * 1e9, 3)} ns V {m['v_on_max']} | loss W: LT channel "
                  f"{m['loss_w']['lt_channel']:.2f} + Rph {m['loss_w']['lt_rph']:.2f}, plant R {m['loss_w']['plant_r']:.2f} + edge "
                  f"{m['loss_w']['plant_edge']} | {m.get('criteria', '')}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(int(sys.argv[3]) if sys.argv[2:3] == ["--jobs"] else 4)
    elif sys.argv[1:2] == ["identity"]:
        identity()
    else:
        main()
