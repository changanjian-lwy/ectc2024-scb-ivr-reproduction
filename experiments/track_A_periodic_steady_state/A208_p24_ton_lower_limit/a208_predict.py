"""A208 predictions from the mathematical model (D63): A207's model with the lower limit moved. D63's Ton is the
on-time; the cosim's Ton register is OFFSET_NS shorter at the same load (A207: 38.59 against 32.85 ns at 250 A, 30.00
against 24.09 ns at 187.5 A - the 8 ns lead less the gate delays), so a register limit of TON_MIN_NS is an on-time
limit of TON_MIN_NS + OFFSET_NS here. D63 has no gate model: it cannot say where a short pulse stops working.
  PYTHONPATH=src python3 a208_predict.py -> a208_predictions.json"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

import scb_ivr.p24_valley_map as vm
from scb_ivr.extensions.ml_rl_ff import design

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
TON_CFG_NS, TON_MIN_NS, OFFSET_NS = 44.48, 2.0, 5.8
SHARES = (60, 50, 40, 30, 20, 10)


class Map(vm.ValleyMap):
    def __init__(self, d):
        super().__init__(d)
        self.ton_min = (TON_MIN_NS + OFFSET_NS) * 1e-9


def main():
    vm.ValleyMap = Map                                  # simulate() builds its maps from the module's name
    d = replace(design(PROJECT / "extensions/ml_design_assist/experiments/A126_ppo_line_feedforward/a126_design.json"),
                ton_cfg_ns=TON_CFG_NS)
    out = {"ton_min_register_ns": TON_MIN_NS, "offset_ns": OFFSET_NS, "rows": {}}
    for p in SHARES:
        recs = vm.simulate(d, 170e-6, 20e-6, i_step=-250.0 * (100 - p) / 100.0)
        last = recs[-40:]
        vo = np.array([r["vo"] for r in recs])
        ton = 1e9 * float(np.mean([r["ton"] for r in last]))
        row = {"vo_end_v": float(np.mean([r["vo"] for r in last])), "vo_max_v": float(vo.max()), "vo_min_v": float(vo.min()),
               "on_time_ns": ton, "register_ns": ton - OFFSET_NS, "register_min_ns": 1e9 * min(r["ton"] for r in recs) - OFFSET_NS,
               "period_ns": 1e9 * float(np.mean([r["period"] for r in last])), "peak_a": float(np.mean([r["peak"] for r in last])),
               "valley_a": float(np.mean([r["valley"] for r in last]))}
        row["at_limit"] = bool(row["register_ns"] <= TON_MIN_NS + 0.05)
        out["rows"][f"m{p}"] = row
        print(f"m{p:<3d} Vo end {row['vo_end_v']:.4f} max {row['vo_max_v']:.4f} | on-time {ton:.2f} ns = register {row['register_ns']:.2f} ns "
              f"(lowest {row['register_min_ns']:.2f}) | T {row['period_ns']:.1f} ns ({1e3 / row['period_ns']:.2f} MHz) | peak {row['peak_a']:.1f} A "
              f"| at limit {row['at_limit']}")
    (HERE / "a208_predictions.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
