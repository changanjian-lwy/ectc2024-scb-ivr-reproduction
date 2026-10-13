"""A206 analysis (BOUNDARY Section 2).
Replays (V runs, LTspice minus plant, A205's judge and limits):
 c0 start: phase currents within 0.05 A, flying-capacitor voltages and Vo within 5 mV;
 c1-c4 as A205 (a205_analyze.judge);
 c5 settled N0, first period: the plant's books (R i^2 and the conducting switches' r_sw i^2 on LTspice's currents,
    its own edge and reverse-fit energies) within 10 % of LTspice's channels + phase resistance.
Plan: V_*_ls3 = A205's plan without the "zero" variants; V_N0_steady_ls1 / ls0p3 = the first three settled snapshots.
Every cosim run (whole): c6 COMPLETED, 0 shoot-throughs, 0 overlaps, 0 forced edges, peak <= 200 A, V_DS <= 40 V,
Vo <= 1.05 V up to 300 us and within 1 V +- 50 mV from 20 us after the handover. With it: start-up, handover and
settled numbers, and the plant's loss books over the last WIN_US of a steady run from the record alone (conduction
rebuilt from the logged currents at every gate command; LS_q also carries phase q + 1 during its high side's on-time).
  python3 a206_analyze.py run [--jobs 3]   the missing replays -> replays/
  python3 a206_analyze.py                  -> a206_summary.json"""
from __future__ import annotations

import importlib.util
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "scripts"))
_s = importlib.util.spec_from_file_location("a205_analyze", TA / "A205_p24_ltspice_replay" / "a205_analyze.py")
A5 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A5)
REP, COS = HERE / "replays", HERE / "cosim"
V5_REC = TA / "A205_p24_ltspice_replay" / "cosim"
LIM0 = {"i0": 0.05, "v0": 5e-3}
LOSS_TOL, WIN_US, T_VO_US = 0.10, 10.0, 143.5
I_LIM, V_LIM, VO_START, VO_BAND = 200.0, 40.0, 1.05, 0.050


def parse(name):
    kind, rest = name.split("_", 1)
    base, ls = rest.rsplit("_ls", 1)
    return kind, base, float(ls.replace("p", "."))


def plan(name, rec):
    kind, base, r_ls = parse(name)
    if kind != "V":
        return []
    if r_ls == 3.0:
        return [x for x in A5.plan(base, rec) if x[2] == "match"]
    g = A5.groups(rec)
    return [("P", g[1][q], "match") for q in range(3)]


def one(arg):
    name, label, k, rph = arg
    import p24_replay as R
    rec = R.load(COS / f"run_{name}.json")
    o = R.replay(rec, k, A5.PERIODS, rph, tag=f"a206_{name}_{label}")
    (REP / A5.fname(name, label, k, rph)).write_text(json.dumps(o, indent=1) + "\n")
    return f"{name} {label} " + R.brief(o)


def run(jobs):
    REP.mkdir(exist_ok=True)
    todo = []
    for f in sorted(COS.glob("run_V_*.json")):
        name = f.stem[4:]
        rec = json.loads(f.read_text())
        todo += [(name, lab, k, rph) for lab, k, rph in plan(name, rec) if not (REP / A5.fname(name, lab, k, rph)).exists()]
    print(len(todo), "replays to run", flush=True)
    with ProcessPoolExecutor(jobs) as ex:
        for line in ex.map(one, todo):
            print(line, flush=True)


def judge(o):
    m = A5.judge(o)
    ls, per = o["loss"], o["loss"]["period_s"]
    w = lambda uj: sum(uj) * 1e-6 / per if uj else 0.0
    plant = {"r": w(ls["plant_r_uj"]), "switches": w(ls.get("plant_sw_uj")), "edges": w(ls["plant_edge_uj"]),
             "rev_fit": w(ls["plant_rev_uj"])}
    plant["total"] = sum(plant.values())
    lt = {"high": w(ls["lt_channel_uj"][:4]), "low": w(ls["lt_channel_uj"][4:]), "rph": w(ls["lt_rph_uj"])}
    lt["total"] = sum(lt.values())
    m["books_w"] = {"plant": plant, "lt": lt, "plant_edges_low_w": w(ls["plant_edge_uj"][4:]) if ls["plant_edge_uj"] else None,
                    "rel": plant["total"] / lt["total"] - 1.0}
    m["start_vcs"], m["start_vo"] = o.get("start_err_vcs_max"), o.get("start_err_vo")
    m["criteria"]["c0"] = (o["start_err_i_max"] <= LIM0["i0"] and o["start_err_vcs_max"] <= LIM0["v0"]
                           and o["start_err_vo"] <= LIM0["v0"])
    return m


def conduction(r, ta, tb):
    """The conducting switches' r_sw i^2 over [ta, tb] (W per switch), from the phase currents logged at every gate
    command (linear in between). High side q: from its channel start to its turn-off's activation. Low side q: from
    its turn-on command plus its mean zero-voltage edge time to its turn-off command; during high side q + 1's
    on-time it also carries phase q + 1."""
    rs = r.get("r_sw_ohm")
    ev = [e for e in r["edges_log"] if ta - 2e-6 <= e["t_s"] <= tb + 1e-6]
    t = np.array([e["t_s"] for e in ev]); cur = np.array([e["i"][:4] for e in ev])
    zs = r["gate_stats"].get("active_zvs_s")
    tz = [0.5 * (a + b) if zs and a is not None else 0.0 for a, b in (zs[4:] if zs else [[None, None]] * 4)]
    act = {(x["phase"], round(x["t_s"], 12)): x.get("t_act_s", x["t_s"]) for x in r["turnons_last"]}
    grid = np.linspace(ta, tb, int(round((tb - ta) / 0.1e-9)) + 1)
    i = np.array([np.interp(grid, t, cur[:, q]) for q in range(4)])
    lumped = [r["snap_circuit"]["R"] * float(np.mean(i[q] ** 2)) for q in range(4)]
    if not rs:
        return None, lumped
    on = np.zeros((8, grid.size), bool)
    for q in range(4):
        hs = [(e["t_s"], e["level"]) for e in ev if e["j"] == q]
        offs = sorted(x["t_s"] for x in r["gate_offs_last"] if x["phase"] == q + 1 and ta - 2e-6 <= x["t_s"] <= tb + 1e-6)
        for (t0, lv), (t1, _) in zip(hs, hs[1:] + [(tb + 1e-6, 0)]):
            if lv:
                a = act.get((q + 1, round(t0, 12)), t0)
                later = [x for x in offs if x >= t1 - 1e-12]
                on[q] |= (grid >= a) & (grid < (later[0] if later and later[0] - t1 < 10e-9 else t1))
        lsv = [(e["t_s"], e["level"]) for e in ev if e["j"] == 4 + q]
        for (t0, lv), (t1, _) in zip(lsv, lsv[1:] + [(tb + 1e-6, 0)]):
            if lv:
                on[4 + q] |= (grid >= t0 + tz[q]) & (grid < t1)
    p = []
    for q in range(4):
        p.append(rs[0] * float(np.mean(i[q] ** 2 * on[q])))
    for q in range(4):
        extra = i[q + 1] * on[q + 1] if q < 3 else 0.0
        p.append(rs[1] * float(np.mean((i[q] + extra) ** 2 * on[4 + q])))
    return p, lumped


def whole(path):
    r = json.loads(Path(path).read_text())
    cfg, tp, g = r["cfg"], r["t_mode_p_s"], r["gate_offs_last"]
    gs = r["gate_stats"]
    ev = cfg.get("line_step")
    t_ev = ev["t_us"] * 1e-6 if ev else None
    te = r["t_end_s"]
    pk = lambda a, b: max((e["i_max_a"] for e in g if a <= e["t_s"] < b), default=None)
    sec = r["sections"]
    ts = np.array([q["t_s"] for q in sec]); vo = np.array([q["vo"] for q in sec])
    out = {"status": r["status"], "commit": r["provenance"]["git_commit"][:7],
           "sources_modified": r["provenance"]["cosim_sources_modified"], "wall_s": r["wall_s"],
           "shoot_on": sum(gs["shoot_on"]), "overlaps": r["overlaps"], "forced": gs["forced"],
           "il_holds": sum(gs.get("il_holds") or [0]), "start_pk": pk(0.0, tp), "hand_pk": pk(tp, tp + 25e-6),
           "after_pk": pk(tp + 25e-6, t_ev if t_ev else te), "post_pk": pk(t_ev, 1.0) if t_ev else None,
           "vds_whole": max(r["vds_max_v"]), "vds_by_switch": r["vds_max_v"],
           "vo_max_to_300us": float(vo[ts <= 300e-6].max()), "vo_at_143p5_v": float(np.interp(T_VO_US * 1e-6, ts, vo)),
           "vo_dev_max_mv": 1e3 * float(np.abs(vo[ts >= tp + 20e-6] - 1.0).max()), "t_mode_p_us": tp * 1e6,
           "t_hand_req_us": None if r.get("t_hand_req_s") is None else r["t_hand_req_s"] * 1e6,
           "late_fires": r["late_fires"], "ls_hard_on": gs["on"][4:], "ls_zvs_on": gs["on_zvs"][4:],
           "zvs_edges": gs.get("zvs_edges"), "zvs_waits": gs.get("zvs_waits"), "active_zvs_s": gs.get("active_zvs_s"),
           "delay_on_s": gs["delay_on_s"], "active_on_ls_s": gs.get("active_on_ls_s"), "didt_on_max_a_ns": gs["didt_on_max_a_ns"],
           "gate_steps": gs["steps"], "steps": r["steps"]}
    pks = [x for x in (out["start_pk"], out["hand_pk"], out["after_pk"], out["post_pk"]) if x is not None]
    out["peak_whole"] = max(pks)
    out["criteria"] = {"c6": bool(r["status"] == "COMPLETED" and not out["shoot_on"] and not out["overlaps"] and not out["forced"]
                                  and out["peak_whole"] <= I_LIM and out["vds_whole"] <= V_LIM
                                  and out["vo_max_to_300us"] <= VO_START and out["vo_dev_max_mv"] <= 1e3 * VO_BAND)}
    if t_ev is None:                                  # a steady run: the settled window's books
        tb = float(ts[-1]); ta = float(ts[np.searchsorted(ts, tb - WIN_US * 1e-6)])
        m = (ts > ta) & (ts <= tb)
        e_edge = np.sum([q["edge_energy_j"] for q, k in zip(sec, m) if k], axis=0) / (tb - ta)
        e_rev = np.sum([q["rev_energy_j"] for q, k in zip(sec, m) if k], axis=0) / (tb - ta)
        cond, lumped = conduction(r, ta, tb)
        pg = [e["i_max_a"] for e in g if ta <= e["t_s"] < tb]
        tons = {}
        hs = [e for e in r["edges_log"] if e["j"] < 4 and ta <= e["t_s"] <= tb]
        on_t, last = [], {}
        for e in hs:
            if e["level"]:
                last[e["j"]] = e["t_s"]
            elif e["j"] in last:
                on_t.append(e["t_s"] - last.pop(e["j"]))
        p_out = float(np.mean(vo[m] ** 2)) / r["snap_circuit"]["r_load"]
        books = {"edges_high": float(e_edge[:4].sum()), "edges_low": float(e_edge[4:].sum()), "rev_fit": float(e_rev.sum()),
                 "switches_high": sum(cond[:4]) if cond else 0.0, "switches_low": sum(cond[4:]) if cond else 0.0,
                 "lumped_r": sum(lumped)}
        tot = sum(books.values())
        out["settled"] = {"window_us": [ta * 1e6, tb * 1e6], "periods": int(m.sum()), "period_ns": 1e9 * (tb - ta) / int(m.sum()),
                          "ton_cmd_ns": 1e9 * float(np.mean(on_t)), "peak_a": [min(pg), max(pg)], "vo_mean_v": float(vo[m].mean()),
                          "p_out_w": p_out, "books_w": books, "books_total_w": tot, "eff_books": p_out / (p_out + tot)}
    return out


def main():
    res = {"runs": {}, "replays": {}}
    for f in sorted(COS.glob("run_*.json")):
        name = f.stem[4:]
        res["runs"][name] = whole(f)
        rec = json.loads(f.read_text())
        rows = {}
        for lab, k, rph in plan(name, rec):
            p = REP / A5.fname(name, lab, k, rph)
            if p.exists():
                rows[f"{lab}_k{k}"] = judge(json.loads(p.read_text()))
        if rows:
            res["replays"][name] = rows
    v5 = {}
    for base in ("N0_steady", "N0_step", "N75_step"):
        p = V5_REC / f"run_{base}.json"
        if p.exists():
            v5[base] = whole(p)
    res["v5"] = v5
    res["criteria"] = {f"{n}:{k}": m["criteria"] for n, rows in res["replays"].items() for k, m in rows.items()}
    res["criteria_runs"] = {n: m["criteria"] for n, m in res["runs"].items()}
    c5 = {}
    for n, rows in res["replays"].items():
        if parse(n)[1] == "N0_steady":
            rel = [m["books_w"]["rel"] for k, m in rows.items() if k.startswith("P_")]
            c5[n] = {"rel": rel, "pass": bool(rel) and max(abs(x) for x in rel) <= LOSS_TOL}
    res["c5"] = c5
    (HERE / "a206_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    f1 = lambda xs: " ".join(f"{x:+.2f}" for x in xs)
    for n, m in list(res["v5"].items()) + list(res["runs"].items()):
        s = m.get("settled")
        print(f"{n:22s} {m['status'][:4]} pk start {m['start_pk']:.1f} hand {m['hand_pk']:.1f} after {m['after_pk']:.1f} post "
              f"{m['post_pk']} | V_DS {m['vds_whole']:.1f} | Vo max {m['vo_max_to_300us']:.4f} at 143.5 {m['vo_at_143p5_v']:.4f} dev "
              f"{m['vo_dev_max_mv']:.1f} mV | shoot {m['shoot_on']} forced {m['forced']} holds {m['il_holds']} late {m['late_fires']} | "
              f"{m['criteria']}" + (f" | settled: Ton {s['ton_cmd_ns']:.2f} ns T {s['period_ns']:.1f} ns peak {s['peak_a'][0]:.1f}-{s['peak_a'][1]:.1f} A "
                                    f"books {' '.join(f'{k} {v:.2f}' for k, v in s['books_w'].items())} total {s['books_total_w']:.2f} W "
                                    f"eff {100 * s['eff_books']:.2f} %" if s else ""))
    for n, rows in res["replays"].items():
        for k, m in rows.items():
            b = m["books_w"]
            print(f"{n:20s} {k:6s} start {m['start_i']:.3f} A {1e3 * m['start_vcs']:.2f} / {1e3 * m['start_vo']:.2f} mV | peaks {f1(m['peak_signed'])} | "
                  f"1 period di {f1(m['di'])} A dVcs {f1([x * 1e3 for x in m['dvcs']])} mV dVo {m['dvo'] * 1e3:+.3f} mV | V_DS {m['vds_max']:.2f} | "
                  f"t_on {None if m['t_on_max'] is None else round(m['t_on_max'] * 1e9, 3)} ns {m['v_on_max']} V | books plant "
                  f"{b['plant']['total']:.2f} W LT {b['lt']['total']:.2f} W ({100 * b['rel']:+.1f} %) | {m['criteria']}")
    print("c5", res["c5"])


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(int(sys.argv[3]) if sys.argv[2:3] == ["--jobs"] else 3)
    else:
        main()
