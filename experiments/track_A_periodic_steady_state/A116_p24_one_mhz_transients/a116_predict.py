"""A116 registered predictions (before any run): D59 at A115's 1 MHz point for the 30 kHz and 60 kHz loops (gains at
the 5% point, as A115; steps at 10%), and the margin between the 10% target and D57's zero-voltage threshold.
Writes a116_predictions.json (make_cfgs.py's FC30 gains come from it)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A115 = HERE.parent / "A115_p24_one_mhz_design_point"
spec = importlib.util.spec_from_file_location("a115_predict", A115 / "a115_predict.py")
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)


def main():
    pr = json.loads((A115 / "a115_predictions.json").read_text())
    res = {"threshold_a": {f: pr["conditions"]["required_pct_phase1"][f] / 100 * P.PEAK for f in ("1MHz", "5MHz")}}
    for fc in (30e3, 60e3):
        P.FC = fc
        for tag in ("n5", "n10"):
            r = pr[f"1MHz_{tag}"]
            lp = P.loop(P.L1, r["ton_ns"] * 1e-9, r["period_ns"] * 1e-9, r["i_neg_a"])
            res[f"fc{fc / 1e3:.0f}_{tag}"] = lp
            print(f"fc {fc / 1e3:.0f} kHz, {tag}: kp {lp['kp_ns_per_v']:.3f} ns/V, ki {lp['ki_ns_per_v']:.4f} ns/V per sample "
                  f"(register {lp['ki_register']}), PM {lp['pm_deg']:.0f} deg; +62.5 A {lp['s_p62']['extreme_mv']:+.1f} mV / "
                  f"{lp['s_p62']['back_within_1pct_us']:.1f} us, -62.5 A {lp['s_m62']['extreme_mv']:+.1f} mV / {lp['s_m62']['back_within_1pct_us']:.1f} us")
    t = res["threshold_a"]
    print(f"zero-voltage threshold (D57, phase 1): 1 MHz {t['1MHz']:.1f} A against the 10% target 12.5 A; "
          f"5 MHz {t['5MHz']:.1f} A against 5% 6.25 A")
    (HERE / "a116_predictions.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
