"""C14 cosim cfgs: D66's sharing-cost check on the frozen four-module design (C12 + lo_learn 4, as A143 g5 / C13).
Rows: n0, s_p62, l_p48_1us (A143's g5 cfgs) and l_m48_1us (C12's cfg + lo_learn 4 and records_last 16000, the
pattern of A143's g5; the row behind D66's +45 A transient increment). Spreads (cfg module_circuit, module 2 = slave 1
heavy): w5 (one at -5 %, three at +5 %), o10 (one at -10 %, three nominal), w10 (one at -10 %, three at +10 %), D66's
"worst" and "one low" cases. Plus nom_l_m48_1us (no spread); the other rows' nominal runs are A143's g5 records.
Writes cosim/cfg_*.json and cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TC = HERE.parent
A143C = TC.parent / "track_A_periodic_steady_state" / "A143_p24_short_comparator_phase" / "cosim"
ROWS = ("l_m48_1us", "l_p48_1us", "s_p62", "n0")
SPREADS = {"w10": (+0.10, -0.10), "o10": (0.0, -0.10), "w5": (+0.05, -0.05)}   # (the other three, the heavy module)
HEAVY = 1                                                                      # module index: slave 1


def base(row):
    if row == "l_m48_1us":
        c = json.loads((TC / "C12_floor_late_four_modules" / "cosim" / "cfg_l_m48_1us.json").read_text())
        return dict(c, lo_learn=4, records_last=16000)
    return json.loads((A143C / f"cfg_g5_{row}_k4.json").read_text())


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for sp, (e_rest, e_heavy) in SPREADS.items():
        for row in ROWS:
            c = base(row)
            l0 = c["circuit"]["L"]
            mc = [{"L": l0 * (1 + (e_heavy if m == HEAVY else e_rest))} if (e_heavy if m == HEAVY else e_rest) else {}
                  for m in range(c["modules"])]
            name = f"{sp}_{row}"
            c = dict(c, module_circuit=mc, out=f"run_{name}.json",
                     note=f"C14 {name}: frozen four-module design, L {e_heavy:+.0%} on module 2, {e_rest:+.0%} on the others")
            (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    c = dict(base("l_m48_1us"), out="run_nom_l_m48_1us.json", note="C14 nom_l_m48_1us: frozen four-module design, no spread")
    (COS / "cfg_nom_l_m48_1us.json").write_text(json.dumps(c, indent=1) + "\n")
    order.append("nom_l_m48_1us")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
