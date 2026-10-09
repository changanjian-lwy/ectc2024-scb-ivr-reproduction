"""A186 analysis: A184's criteria (a184_analyze) for every run and temperature, g0 against A185's run of the same
condition up to A186's mode-P entry (mode S is unchanged until the handover request), c6 against the t0 = 400 ns
records at 25 and 125 C, and c7: Vo <= 1.05 V from 0 to 300 us (start-up overshoot). Writes a186_summary.json.
  python3 a186_analyze.py"""
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
VO_MAX = 1.05


def identity(r, cond):
    f = A185 / f"run_{cond}_p0.json"
    if not f.exists():
        return None
    o = json.loads(f.read_text())
    tp = r["t_mode_p_s"]
    a = [q for q in r["sections"] if q["t_s"] <= tp]
    b = [q for q in o["sections"] if q["t_s"] <= tp]
    return a == b


def main():
    res = {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        stem, o = A.run(f)
        r = json.loads(Path(f).read_text())
        cond = stem.rsplit("_p", 1)[0]
        o["g0_identical_pre_entry"] = o["criteria"]["g0"] = identity(r, cond)
        tp = r["t_mode_p_s"]
        ent = next(q for q in r["sections"] if q["t_s"] > tp)
        vmax = [max(q["vo"] for q in m["sections"] if q["t_s"] < 300e-6) for m in A.modules(r)]
        o.update(t_hand_req_us=(r.get("t_hand_req_s") or 0) * 1e6 or None, t_entry_us=tp * 1e6, vin_entry_v=ent["vin_v"],
                 vo_max_300us=vmax)
        o["criteria"]["c7"] = all(v <= VO_MAX for v in vmax)
        res[stem] = o
    (HERE / "a186_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for s, o in res.items():
        print(f"{s:10s} hand req {o['t_hand_req_us'] or 0:7.2f} us entry {o['t_entry_us']:7.2f} us Vin {o['vin_entry_v']:5.2f} V "
              f"Vo max {max(o['vo_max_300us']):.3f}")
        for j, m in enumerate(o["modules"]):
            print(f"   m{j} start {m['start_pk']:5.1f} hand {m['hand_pk']:5.1f} gap {m['gap_pk']:5.1f} post {m['post_pk'] or 0:5.1f} "
                  f"V {m['vds_max_v']:.1f} Vo(143.5) {m['vo_143_5']:.3f} Vo_min {m['vo_min_entry']:.3f}"
                  + (f" (ref {o['c6'][j]['ref']:.3f}) dev {o['c5_dev_a'][j]:.2f}" if o["c6"] else "")
                  + f" Ton {m['ton_max_entry_ns']:.1f}/{m['ton_steady_ns']:.1f} ns")
        print("   ", o["criteria"])


if __name__ == "__main__":
    main()
