"""A207 predictions from the mathematical model (D63, p24_valley_map): the A124 design with the final configuration's
Ton limits (0.5 and 2 times cfg ton_ns = 44.48 ns, bridge.py) and the same load release. D63 has no gate delays: its
Ton is the effective on-time, about 2.3 ns shorter than the cosim's command at full load (38.59 against 40.85 ns).
  PYTHONPATH=src python3 a207_predict.py -> a207_predictions.json"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from scb_ivr.extensions.ml_rl_ff import design
from scb_ivr.p24_valley_map import simulate

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
TON_CFG_NS = 44.48
SHARES = (100, 75, 60, 55, 50, 45, 40, 30, 10)


def main():
    d = replace(design(PROJECT / "extensions/ml_design_assist/experiments/A126_ppo_line_feedforward/a126_design.json"),
                ton_cfg_ns=TON_CFG_NS)
    out = {"ton_min_ns": 0.5 * TON_CFG_NS, "rows": {}}
    for p in SHARES:
        recs = simulate(d, 170e-6, 20e-6, i_step=-250.0 * (100 - p) / 100.0)
        last = recs[-40:]
        vo = np.array([r["vo"] for r in recs])
        row = {"vo_end_v": float(np.mean([r["vo"] for r in last])), "vo_max_v": float(vo.max()),
               "ton_ns": 1e9 * float(np.mean([r["ton"] for r in last])),
               "period_ns": 1e9 * float(np.mean([r["period"] for r in last])),
               "peak_a": float(np.mean([r["peak"] for r in last])), "valley_a": float(np.mean([r["valley"] for r in last]))}
        row["at_limit"] = bool(row["ton_ns"] <= 0.5 * TON_CFG_NS + 0.02)
        out["rows"][f"f{p}"] = row
        print(f"f{p:<3d} Vo end {row['vo_end_v']:.4f} max {row['vo_max_v']:.4f} | Ton {row['ton_ns']:.2f} ns | T {row['period_ns']:.1f} ns "
              f"({1e3 / row['period_ns']:.2f} MHz) | peak {row['peak_a']:.1f} A valley {row['valley_a']:.1f} A | at limit {row['at_limit']}")
    (HERE / "a207_predictions.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
