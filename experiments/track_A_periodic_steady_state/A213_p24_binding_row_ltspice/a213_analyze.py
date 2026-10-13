"""A213 analysis (BOUNDARY Section 2).
 i1 the cosim record's sections equal A206's B_S75_hot_p5 record bit for bit up to this run's end;
 c1-c4 per replay as A205 / A206 (a206_analyze.judge; its c0 is kept as a number, not a criterion);
 c5 on the peak replays: LTspice's largest peak <= the plant's largest peak + MARGIN_A.
Plan: P = the first three snapshots of the settled window; T = the last snapshot before the step and the next, and
the snapshot at the plant's largest peak with the two before it.
  python3 a213_analyze.py run [--jobs 2]   the missing replays -> replays/
  python3 a213_analyze.py                  -> a213_summary.json"""
from __future__ import annotations

import importlib.util
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "scripts"))


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A6 = _load("a206_analyze", TA / "A206_p24_low_side_zvs_turn_on" / "a206_analyze.py")
A5 = A6.A5
REC = HERE / "cosim" / "run_S75_hot_p5.json"
REF = TA / "A206_p24_low_side_zvs_turn_on" / "cosim" / "run_B_S75_hot_p5_ls0p3.json"
REP = HERE / "replays"
NAME, MARGIN_A = "S75_hot_p5", 2.4


def plan(rec):
    g = A5.groups(rec)
    assert len(g) == 2, [len(x) for x in g]
    ts = rec["cfg"]["line_step"]["t_us"] * 1e-6
    snaps = rec["snaps"]
    s = max(k for k in g[1] if snaps[k]["t_s"] < ts)
    pk = max((e for e in rec["gate_offs_last"] if e["t_s"] >= ts), key=lambda e: e["i_max_a"])
    p = max(k for k in g[1] if snaps[k]["t_s"] <= pk["t_s"] + 1e-9)
    assert p + A5.PERIODS <= g[1][-1], "the snapshot window ends before the last replay"
    return [("P", g[0][q]) for q in range(3)] + [("T", k) for k in sorted({s, s + 1})] + [("K", k) for k in (p - 2, p - 1, p)]


def one(arg):
    label, k = arg
    import p24_replay as R
    rec = R.load(REC)
    o = R.replay(rec, k, A5.PERIODS, "match", tag=f"a213_{label}")
    (REP / A5.fname(NAME, label, k, "match")).write_text(json.dumps(o, indent=1) + "\n")
    return f"{label} k{k} " + R.brief(o)


def run(jobs):
    REP.mkdir(exist_ok=True)
    rec = json.loads(REC.read_text())
    todo = [x for x in plan(rec) if not (REP / A5.fname(NAME, x[0], x[1], "match")).exists()]
    print(len(todo), "replays to run", flush=True)
    with ProcessPoolExecutor(jobs) as ex:
        for line in ex.map(one, todo):
            print(line, flush=True)


def main():
    rec = json.loads(REC.read_text())
    res = {"record": {"status": rec["status"], "commit": rec["provenance"]["git_commit"][:7],
                      "sources_modified": rec["provenance"]["cosim_sources_modified"], "snaps": len(rec["snaps"])}}
    if REF.exists():
        ref = json.loads(REF.read_text())
        n = len(rec["sections"])
        res["criteria_identity"] = {"i1": bool(ref["sections"][:n] == rec["sections"]), "sections": n}
    pk = max((e for e in rec["gate_offs_last"] if e["t_s"] >= rec["cfg"]["line_step"]["t_us"] * 1e-6), key=lambda e: e["i_max_a"])
    res["plant_peak"] = {"a": pk["i_max_a"], "phase": pk["phase"], "t_us": pk["t_s"] * 1e6}
    rows, c5 = {}, {"rows": {}}
    for label, k in plan(rec):
        f = REP / A5.fname(NAME, label, k, "match")
        if not f.exists():
            continue
        o = json.loads(f.read_text())
        m = A6.judge(o)
        m["c0_number"] = m["criteria"].pop("c0")
        lt = [x["lt_a"] for x in o["peaks"]]; pl = [x["plant_a"] for x in o["peaks"] if x["plant_a"] is not None]
        m["peak_max"] = {"lt_a": max(lt), "plant_a": max(pl)}
        rows[f"{label}_k{k}"] = m
        if label == "K":
            c5["rows"][f"K_k{k}"] = {"lt_a": max(lt), "plant_a": max(pl), "pass": bool(max(lt) <= max(pl) + MARGIN_A)}
    c5["pass"] = bool(c5["rows"]) and all(v["pass"] for v in c5["rows"].values())
    res["replays"] = rows
    res["criteria"] = {k: m["criteria"] for k, m in rows.items()}
    res["criteria_c5"] = c5
    (HERE / "a213_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    f1 = lambda xs: " ".join(f"{x:+.2f}" for x in xs)
    print("record", res["record"], "identity", res.get("criteria_identity"), "plant peak", res["plant_peak"])
    for k, m in rows.items():
        b = m["books_w"]
        print(f"{k:8s} start {m['start_i']:.3f} A {1e3 * m['start_vcs']:.2f} mV | peaks {f1(m['peak_signed'])} | largest LT {m['peak_max']['lt_a']:.2f} plant {m['peak_max']['plant_a']:.2f} | "
              f"1 period di {f1(m['di'])} A dVcs {f1([x * 1e3 for x in m['dvcs']])} mV dVo {m['dvo'] * 1e3:+.3f} mV | V_DS {m['vds_max']:.2f} | "
              f"t_on {None if m['t_on_max'] is None else round(m['t_on_max'] * 1e9, 3)} ns {m['v_on_max']} V | books plant {b['plant']['total']:.2f} LT {b['lt']['total']:.2f} W "
              f"({100 * b['rel']:+.1f} %) | {m['criteria']}")
    print("c5", c5)


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(int(sys.argv[3]) if sys.argv[2:3] == ["--jobs"] else 2)
    else:
        main()
