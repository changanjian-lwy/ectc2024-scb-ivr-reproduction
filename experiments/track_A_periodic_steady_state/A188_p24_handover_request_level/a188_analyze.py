"""A188 analysis (BOUNDARY Section 2): a184_analyze's per-run stats for the hot runs; c4' = Vo at mode-P entry in
0.99-1.17 V (A163's window applied where it guards: the entry); c5 within +-3 A; c6 against the t0 = 400 records;
c7 Vo <= 1.05 V over 0-300 us; g0 = the 25 C check run equals A185's S0 run up to 150 us. Writes a188_summary.json.
  python3 a188_analyze.py"""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a184_analyze", TA / "A184_p24_startup_own_ton" / "a184_analyze.py")
A = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A)
A185 = TA / "A185_p24_bumpless_loop_seed" / "cosim"


def main():
    res = {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        r = json.loads(Path(f).read_text())
        stem = Path(f).stem[4:]
        if stem == "S0_25_p0":                                   # the 25 C identity check
            o = json.loads((A185 / "run_S0_25_p0.json").read_text())
            a = [q for q in r["sections"] if q["t_s"] <= 150e-6]
            b = [q for q in o["sections"] if q["t_s"] <= 150e-6]
            n = min(len(a), len(b)) - 1
            res[stem] = {"criteria": {"g0": a[:n] == b[:n] and r.get("t_hand_req_s") is None}, "sections_compared": n,
                         "t_hand_req_s": r.get("t_hand_req_s")}
            continue
        _, o = A.run(f)
        tp = r["t_mode_p_s"]
        ent = next(q for q in r["sections"] if q["t_s"] > tp)
        vmax = max(q["vo"] for q in r["sections"] if q["t_s"] < 300e-6)
        o.update(t_hand_req_us=(r.get("t_hand_req_s") or 0) * 1e6 or None, t_entry_us=tp * 1e6, vin_entry_v=ent["vin_v"],
                 vo_entry_v=ent["vo"], vo_max_300us=vmax)
        c = o["criteria"]
        c.pop("g0", None)
        c["c4"] = 0.99 <= ent["vo"] <= 1.17
        c["c5"] = all(d <= 3.0 for d in o["c5_dev_a"]) if o["c5_dev_a"] else None
        c["c7"] = vmax <= 1.05
        res[stem] = o
    (HERE / "a188_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for s, o in res.items():
        if "modules" not in o:
            print(s, o)
            continue
        m = o["modules"][0]
        print(f"{s:10s} req {o['t_hand_req_us'] or 0:7.2f} entry {o['t_entry_us']:7.2f} us Vin {o['vin_entry_v']:5.2f} Vo {o['vo_entry_v']:.4f} "
              f"max {o['vo_max_300us']:.3f} | start {m['start_pk']:5.1f} hand {m['hand_pk']:5.1f} gap {m['gap_pk']:5.1f} "
              f"post {m['post_pk'] or 0:5.1f} V {m['vds_max_v']:.1f} Vo_min {m['vo_min_entry']:.3f}"
              + (f" (ref {o['c6'][0]['ref']:.3f}) dev {o['c5_dev_a'][0]:.2f}" if o["c6"] else ""))
        print("   ", o["criteria"])


if __name__ == "__main__":
    main()
