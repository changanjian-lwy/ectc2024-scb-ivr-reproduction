"""A198 analysis: a194_analyze.run per run (c1 COMPLETED / 0 shoot-throughs / 0 overlaps, c2 whole-run peak <= 200 A,
c3 V_DS <= 40 V, c4 Vo within 1 V +- 50 mV from 20 us after the handover, c5 back inside 1 % at most 60 us after the
step ends), plus the step's distance from mode P's entry as it happened, the largest peak after the step with its
phase and time, and the board's handover-only peak (the same board's A194 record, no event within 25 us of the entry).
Writes a198_summary.json.
  python3 a198_analyze.py"""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a194", TA / "A194_p24_final_plant_random_stimuli" / "a194_analyze.py")
A194 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A194)
HAND_ONLY = {"S75_hot": 184.5, "S75_25": 154.0, "N0_25": 165.4}          # A194 r04 / r09 / r20, entry .. + 25 us


def main():
    res = {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json")), key=lambda p: (Path(p).stem.rsplit("_d", 1)[0], int(Path(p).stem.rsplit("_d", 1)[1]))):
        k, out = A194.run(f)
        r = json.loads(Path(f).read_text())
        t0 = r["cfg"]["line_step"]["t_us"] * 1e-6
        m = max((e for e in r["gate_offs_last"] if e["t_s"] >= t0), key=lambda e: e["i_max_a"])
        out.update(after_entry_us=(t0 - r["t_mode_p_s"]) * 1e6, post_phase=m["phase"], post_after_us=(m["t_s"] - t0) * 1e6,
                   hand_only_pk=HAND_ONLY[k.rsplit("_d", 1)[0]], commit=r["provenance"]["git_commit"][:7],
                   sources_modified=r["provenance"]["cosim_sources_modified"])
        res[k] = out
    (HERE / "a198_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, s in res.items():
        miss = [c for c, ok in s["criteria"].items() if not ok]
        print(f"{k:14s} step {s['after_entry_us']:5.1f} us after entry | start {s['start_pk']:5.1f} hand {s['hand_pk']:5.1f} (alone {s['hand_only_pk']:5.1f}) "
              f"post {s['post_pk']:5.1f} A ph{s['post_phase']} at +{s['post_after_us']:.1f} us | V {s['vds_whole']:.1f} | Vo {s['vo_post_min_mv']:+.1f}/"
              f"{s['vo_post_max_mv']:+.1f} mV back {s['back_1pct_us']:.1f} us | late {s['late_post']} NEW {s['oracle_new']} | "
              f"{'PASS' if not miss else 'MISS ' + ','.join(miss)} {s['commit']} mod {s['sources_modified']}")


if __name__ == "__main__":
    main()
