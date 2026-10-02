"""D58: the P24 module's start-up with the averaged model (A103).

    python3 scripts/p24_startup_averaged.py

1. Validation: the reference start-up (open-loop mode S with no load during the input ramp, load and handover
   together at 88.61 us) against A100's comparator reference run (the adopted design; identical to its step-free
   counterpart before the step at 400 us).
2. Cases for A103: the load from t = 0 (a resistive boot load, as a processor's reset leakage), the handover at
   88.61 or 72 us (after the 68.61 us input ramp), mode S's Ton at 533 (16.667 ns) or 568 LSB (17.75 ns, the
   full-load steady state). Metrics against VRD 11.1's overshoot limits (50 mV, 25 us above VID).
Writes symbolic_derivations/03_P24_native/diagnostics/D58_startup_averaged.json and A103's d58_predictions.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from scb_ivr.p24_startup_averaged import Module, Sequence, metrics, run, validate  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
A103 = ROOT / "experiments" / "track_A_periodic_steady_state" / "A103_p24_startup_sequence"
REF = ROOT / "experiments" / "track_A_periodic_steady_state" / "A100_timed_turn_off_load_steps" / "cosim" / "run_ref_m62.json"
CASES = {
    "c0_reference": Sequence(),
    "c1_load_from_0": Sequence(t_load=0.0),
    "c1b_load_from_0_hand_72": Sequence(t_load=0.0, t_hand=72e-6),
    "c1d_load_from_0_hand_72_ton568": Sequence(t_load=0.0, t_hand=72e-6, ton_s=568.0),
}


def main():
    m = Module()
    out = {"conditions": {"module": {k: getattr(m, k) for k in m.__dataclass_fields__}, "k": m.k, "t_x_ns": m.t_x * 1e9,
                          "reference_run": str(REF.relative_to(ROOT))}}
    ref = json.loads(REF.read_text())
    secs = [s for s in ref["sections"] if s["t_s"] < 300e-6]
    print("1. validation against the reference co-simulation")
    rows = validate(secs, m)
    out["validation"] = rows
    for r in rows:
        print(f"   {r['t_us']:4d} us: model Vo {r['model_vo_v']:.3f} V, Ton {r['model_ton_lsb']:.0f} | co-simulation {r['cosim_vo_v']:.3f} V, {r['cosim_ton_lsb']}")
    t, vo, ton, _ = run(m, Sequence())
    mm = metrics(t, vo, Sequence())
    ts = [s["t_s"] for s in secs]; vs = [s["vo"] for s in secs]
    after = [(a, b) for a, b in zip(ts, vs) if a > 88.61e-6]
    cmin = min(after, key=lambda x: x[1])
    out["validation_extremes"] = {"model_min_v": mm["vo_min_after_handover_v"], "cosim_min_v": cmin[1], "cosim_min_us": cmin[0] * 1e6}
    print(f"   minimum after the handover: model {mm['vo_min_after_handover_v']:.3f} V, co-simulation {cmin[1]:.3f} V at {cmin[0] * 1e6:.1f} us")

    print("\n2. cases (VRD 11.1: overshoot <= VID + 50 mV, <= 25 us above VID)")
    pred = {}
    for name, sq in CASES.items():
        t, vo, ton, mode = run(m, sq)
        x = metrics(t, vo, sq)
        x.update(sequence={k: getattr(sq, k) for k in sq.__dataclass_fields__},
                 ton_at_handover_lsb=float(ton[mode == 1][0]), vo_at_handover_v=float(vo[mode == 1][0]))
        pred[name] = x
        print(f"   {name:32s}: max {x['vo_max_v']:.3f} V at {x['t_vo_max_us']:5.1f} us ({x['t_above_vid_us']:5.1f} us above 1 V); "
              f"Vo at the handover {x['vo_at_handover_v']:.3f} V; min after it {x['vo_min_after_handover_v']:.3f} V; "
              f"within 1% from {x['settle_1pct_us']:5.1f} us; final {x['vo_final_v']:.4f} V")
    out["cases"] = pred
    (DIAG / "D58_startup_averaged.json").write_text(json.dumps(out, indent=1, default=float))
    A103.mkdir(parents=True, exist_ok=True)
    (A103 / "d58_predictions.json").write_text(json.dumps(pred, indent=1, default=float))
    print(f"\nwrote {(DIAG / 'D58_startup_averaged.json').relative_to(ROOT)} and {(A103 / 'd58_predictions.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
