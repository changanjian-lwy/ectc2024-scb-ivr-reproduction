"""A136 predictions (registered, not criteria): D63 as A135 (a135_predict: L x m, RTL-exact scb_vff, A124's rows +
n0 + x_l_p80_10us) with the relative cap on ton's low-pass - tlp += (ton - tlp) >> sh20 in Q8 at each Vin sample, cap =
(tlp >> 8) x ((rss x 320) >> 8) / rail. D63 under-predicted A135's rising rows (r100 l_p48_1us 187 vs 203 A in cosim;
r130 195 vs 212 A), so these numbers rank, they do not bound. Writes a136_predictions.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("a135_predict", HERE.parent / "A135_p24_relative_cap" / "a135_predict.py")
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
REL = 320


class VffLP(P.VffRTL):
    def __init__(self, rel=REL):
        super().__init__(rel=rel)
        self.tlp = None

    def __call__(self, vin, ton_s):
        t8 = round(ton_s / P.LSB) << 8
        self.tlp = t8 if self.tlp is None else self.tlp + ((t8 - self.tlp) >> P.VFF["sh20"])
        return super().__call__(vin, (self.tlp >> 8) * P.LSB)


def main():
    out = {"rel_q8": REL, "rel_lp": 1, "ms": P.MS, "runs": {}}
    for m in P.MS:
        for row in P.ROWS:
            out["runs"][f"q{round(m * 100):03d}_{row}"] = P.run(m, VffLP(), row)
    (HERE / "a136_predictions.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for m in P.MS:
        rs = {row: out["runs"][f"q{round(m * 100):03d}_{row}"] for row in P.ROWS}
        a124 = [x["peak_a"] for row, x in rs.items() if not row.startswith("x_")]
        print(f"q L x{m:4.2f}: A124 rows pk {max(a124):4.0f} A (l_p48_1us {rs['l_p48_1us']['peak_a']:.0f}, 5us {rs['l_p48_5us']['peak_a']:.0f}), "
              f"+8V/10us {rs['x_l_p80_10us']['peak_a']:4.0f} A, bind pre/tail {max(x['bind_pre'] for x in rs.values())}/"
              f"{max(x['bind_tail'] for x in rs.values())}, not ok: {','.join(r for r, x in rs.items() if x['outcome'] != 'ok') or '-'}")


if __name__ == "__main__":
    main()
