"""A210 analysis (BOUNDARY Section 2): A208's per-row numbers (a208_analyze.one) with r4's valley band per board.
  python3 a210_analyze.py -> a210_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a208_analyze", HERE.parent / "A208_p24_ton_lower_limit" / "a208_analyze.py")
A8 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A8)
COS = HERE / "cosim"
BAND = {"N75": (-20.0, -12.0), "S75": (-22.0, -8.0)}


def one(path):
    m = A8.one(path)
    board = Path(path).stem.split("_")[2]
    lo, hi = BAND[board]
    va = [x for v in m["valley_end_a"].values() for x in v]
    m["valley_band_a"] = [lo, hi]
    m["criteria"]["r4"] = bool(len(m["valley_end_a"]) == 4 and min(va) >= lo and max(va) <= hi and not any(m["late_end"]))
    m["works"] = bool(m["criteria"]["r1"] and m["criteria"]["r2"] and m["criteria"]["r4"])
    # not a criterion (seen after the runs): high-side on-commands of the last 20 us whose turn-off the gate model did not
    # record as an edge of a conducting switch, i.e. the off-command came before the turn-on edge had finished
    r = json.loads(Path(path).read_text())
    te = r["sections"][-1]["t_s"]
    cmd = sum(1 for e in r["highoffs_last"] if e["t_s"] >= te - A8.T_WIN)
    done = sum(1 for e in r["gate_offs_last"] if e["t_s"] >= te - A8.T_WIN)
    ho = [e["i_a"] for e in r["highoffs_last"] if e["t_s"] >= te - A8.T_WIN]
    m.update(hs_off_commands_end=cmd, hs_off_edges_end=done, hs_incomplete_share=(cmd - done) / cmd if cmd else None,
             hs_off_cmd_current_a=[min(ho), max(ho)] if ho else None, hs_lead_ns=r["cfg"]["driver"]["hs_on_lead_ns"])
    return m


def main():
    res = {"runs": {f.stem[4:]: one(f) for f in sorted(COS.glob("run_r_*.json"))}}
    low = {}
    for n, m in res["runs"].items():
        key = "_".join(n.split("_")[1:3])
        if m["works"] and m["share"] < low.get(key, (9.0,))[0]:
            low[key] = (m["share"], n)
    res["lowest_working"] = {k: v[1] for k, v in low.items()}
    (HERE / "a210_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for n, m in res["runs"].items():
        b = m.get("books_w") or {}
        va = [x for v in m["valley_end_a"].values() for x in v]
        print(f"{n:16s} {m['status'][:4]} Vo end {m['vo_end_v']:.4f} ({m['vo_end_min_v']:.4f}..{m['vo_end_max_v']:.4f}) after "
              f"{m['vo_after_min_v']:.4f}..{m['vo_after_max_v']:.4f} | register {m['ton_reg_ns']:.2f} ns (end {m['ton_reg_end_ns'][0]:.2f}..{m['ton_reg_end_ns'][1]:.2f}; "
              f"lowest {m['ton_reg_min_after_ns']:.2f}; {m['sections_at_limit']} sections at {m['ton_min_ns']:.2f}) command {m.get('ton_cmd_ns', float('nan')):.2f} ns | "
              f"T {m.get('period_ns', float('nan')):.1f} ns {m.get('f_mhz', float('nan')):.2f} MHz | peak {[round(x, 1) for x in (m.get('peak_a') or [])]} "
              f"HS-off at {[round(x, 1) for x in m['hs_off_cmd_current_a']]} A, incomplete turn-ons {100 * m['hs_incomplete_share']:.0f} % whole {m['peak_whole']:.1f} | "
              f"V_DS {m['vds_whole']:.1f} | valleys {min(va):.1f}..{max(va):.1f} late {m['late_end']} holds {m['il_holds']} | Iout {m.get('i_out_a', float('nan')):.1f} A "
              f"loss {m.get('loss_w', float('nan')):.2f} W ({' '.join(f'{k} {v:.2f}' for k, v in b.items() if v)}) eff {100 * m.get('eff_books', float('nan')):.2f} % | "
              f"{m['criteria']} works {m['works']}")
    print("lowest working:", res["lowest_working"])


if __name__ == "__main__":
    main()
