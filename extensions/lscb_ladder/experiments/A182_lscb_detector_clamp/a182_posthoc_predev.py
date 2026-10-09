"""A182 post hoc (not registered): where the pre-step clamp deviation peaks.

Pass 1 found max |V(d(4-k)) - Vcs_k| = 1.129 V before the step in every run, above the 0.75 V threshold. Criterion 1
measured from t = 0, so it includes the settling from the .ic state. This reruns nowin_c20_up1 up to the step and keeps
the raw data, then prints the maximum per time window and where the overall maximum falls -> a182_posthoc_predev.json.
Run from the project root: PYTHONPATH=src:scripts python3 extensions/lscb_ladder/experiments/A182_lscb_detector_clamp/a182_posthoc_predev.py
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A180_lscb_ladder_open_loop"))
import a180_run as a180                                                   # noqa: E402
from scb_ivr.extensions import lscb_ladder as ll                          # noqa: E402


def main():
    p = dict(ll.PARAMS, save_ls=True, win=(-2.0, -1.0), t_end=ll.PARAMS["t_step"])
    (names, arr), log, rp = a180.run_lt("a182_posthoc_predev", ll.netlist("act_c20", "up1", p))
    t = arr[:, 0]
    dev = np.array(ll.deviations(names, arr))
    a = np.abs(dev)
    out = {"t_of_max_us": float(t[np.argmax(a.max(axis=0))] * 1e6), "max_v": float(a.max())}
    for lo, hi in ((0, 1), (1, 5), (5, 10), (10, 20), (20, 30), (30, 40)):
        m = (t >= lo * 1e-6) & (t < hi * 1e-6)
        out[f"{lo}-{hi}us"] = dict(max_abs_v=[float(x) for x in a[:, m].max(axis=1)],
                                   mean_v=[float(np.trapezoid(d[m], t[m]) / (t[m][-1] - t[m][0])) for d in dev])
    (HERE / "a182_posthoc_predev.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    rp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
