"""A254 screen (BOUNDARY Section 1): which of the final configuration's 70 reference records a limit at LEVEL[L] could
act on. A pulse counts if its current, taken linear from its turn-on to its high-side turn-off, crosses the level more
than LAT_S before the turn-off. The slope rises toward the on-time's end (A253), so the linear crossing comes early and
the screen over-counts: on A253's 8 rows at 130 / 145 A and 11 ns it marks every row that fired (78 / 43 / 45 against
13 / 4 / 16) and also three that did not; it marks none where A253 had none. LAT_S 8 ns adds margin.
  python3 a254_screen.py -> a254_screen.json"""
from __future__ import annotations

import bisect
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A46, A51 = TA / "A246_p24_held_report_floor" / "cosim", TA / "A251_p24_hold_after_startup" / "cosim"
OVER_A, GATE_A, CAP_A, MARGIN_A, L_MEAS = 69.0, 14.0, 200.0, 5.0, 2.2   # A253: rise in 11 ns on 2.2 nH, gate record
LAT_S = 8e-9


def level(l_nh):
    """CAP - MARGIN - GATE - OVER x 2.2 / L, down to 5 A: 110 / 125 / 140 A on 2.2 / 2.933 / 3.813 nH."""
    return 5.0 * int((CAP_A - MARGIN_A - GATE_A - OVER_A * L_MEAS / l_nh) // 5)


def refs():
    """(name, reference cfg, reference record): A246's 46 + 4 position rows, A251's arm h on A245's 20 start-ups."""
    s = importlib.util.spec_from_file_location("a251_make_cfgs", TA / "A251_p24_hold_after_startup" / "make_cfgs.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    out = [(r, A46 / f"cfg_h_{r}.json", A46 / f"run_h_{r}.json") for r in m.STAGE1 + m.STAGE2]
    out += [(f"{r}_k{k}", A46 / f"cfg_ch_{r}_k{k}.json", A46 / f"run_ch_{r}_k{k}.json") for r, ks in m.POS.items() for k in ks]
    return out + [(r, A51 / f"cfg_h_{r}.json", A51 / f"run_h_{r}.json") for r in m.START]


def screen(f, lv, lat=LAT_S):
    d = json.loads(Path(f).read_text())
    n = 0
    for md in [d] + d.get("modules_rest", []):
        on = {k: sorted((x["t_s"], x["i_a"]) for x in md["turnons_last"] if x["phase"] == k) for k in range(1, 5)}
        for x in md["highoffs_last"]:
            o = on[x["phase"]]
            i = bisect.bisect_left(o, (x["t_s"],)) - 1
            if x["i_a"] <= lv or i < 0:
                continue
            t_on, i_on = o[i]
            tx = t_on if i_on >= lv else t_on + (lv - i_on) / (x["i_a"] - i_on) * (x["t_s"] - t_on)
            n += x["t_s"] - tx > lat
    return n


def main():
    res = {}
    for name, c, f in refs():
        l_nh = round(json.loads(c.read_text())["circuit"]["L"] * 1e9, 3)
        res[name] = {"cfg": str(c.relative_to(TA)), "L_nH": l_nh, "level_a": level(l_nh), "n": screen(f, level(l_nh))}
    (HERE / "a254_screen.json").write_text(json.dumps(res, indent=1) + "\n")
    print(sum(1 for x in res.values() if x["n"]), "of", len(res), "rows screened to act")


if __name__ == "__main__":
    main()
