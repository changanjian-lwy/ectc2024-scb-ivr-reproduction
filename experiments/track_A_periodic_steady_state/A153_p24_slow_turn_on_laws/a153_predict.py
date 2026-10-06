"""A153 registered predictions from D68 (diagnostics/D68_slow_turn_on.json) -> a153_predictions.json.
Start-up rows: Vo(143.6 us) = Vo72(100 pH) - S K (d^-1/2 - 72^-1/2), band from D68's per-L K (14.6-16.7); A152's
36 A / di/dt rule alongside. Line-step rows: whole-run max V_DS = the co-simulated x-curve at x = L * d, +-1.0 V;
start-up: Vo before the handover = Vo72 at that L (interpolated over A145's 50 / 100 / 150 pH) +-0.015 V."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import make_cfgs as M  # noqa: E402


def main():
    d68 = json.loads((ROOT / "diagnostics" / "D68_slow_turn_on.json").read_text())
    s, k = d68["s_v_per_ns"], d68["k_cosim_all"]
    kl = [v for v in d68["k_cosim_by_l"].values() if v]
    vo72 = {r["l_ph"]: r["vo72"] for r in d68["startup_cosim"]}
    xs = [c[0] for c in d68["overshoot_curve"]]
    vs = [c[1] for c in d68["overshoot_curve"]]
    out = {"k": k, "k_band": [min(kl), max(kl)], "s_v_per_ns": s, "x_star_v": d68["x_star_v"], "start": {}, "line": {}}
    for d in M.UP:
        x = d ** -0.5 - 72.0 ** -0.5
        out["start"][f"u{d:02.0f}_l100"] = dict(didt=d, vo=vo72[100] - s * k * x,
                                                 band=[vo72[100] - s * max(kl) * x, vo72[100] - s * min(kl) * x],
                                                 vo_a152_rule=vo72[100] - s * 36.0 * (1 / d - 1 / 72.0))
    for l, d in M.VROWS:
        x = l * d * 1e-3
        v = float(np.interp(x, xs, vs))
        out["line"][f"v{l}_on{d:g}"] = dict(l_ph=l, didt=d, x_v=x, ton_ns=M.ton_s(d), vds_max_v=v, band=[v - 1.0, v + 1.0],
                                             le_40=v <= 40.0, vo_hand=float(np.interp(l, sorted(vo72), [vo72[q] for q in sorted(vo72)])))
    (HERE / "a153_predictions.json").write_text(json.dumps(out, indent=1) + "\n")
    for n, p in out["start"].items():
        print(f"{n}: Vo {p['vo']:.4f} [{p['band'][0]:.4f}, {p['band'][1]:.4f}], A152 rule {p['vo_a152_rule']:.4f}")
    for n, p in out["line"].items():
        print(f"{n}: x {p['x_v']:.2f} V -> max V_DS {p['vds_max_v']:.1f} V ({'<=' if p['le_40'] else '>'} 40), ton {p['ton_ns']} ns, "
              f"Vo at handover {p['vo_hand']:.4f}")


if __name__ == "__main__":
    main()
