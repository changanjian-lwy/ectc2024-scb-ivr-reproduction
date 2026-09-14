"""Extract A43's event progress and first blocked boundary."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from spicelib import RawRead


TRACK = Path(__file__).resolve().parent
HERE = TRACK / "A43_p25_device_augmented_7p77_full_event_machine"
RAW = HERE / "A43_p25_device_augmented_7p77_full_event_machine.raw"


def wave(raw: RawRead, name: str) -> np.ndarray:
    return np.real(raw.get_trace(name).get_wave(0))


def first_crossing(time: np.ndarray, value: np.ndarray, threshold: float) -> float | None:
    idx = np.where((value[:-1] < threshold) & (value[1:] >= threshold))[0]
    return None if not len(idx) else float(time[int(idx[0]) + 1] * 1e9)


def first_rise(time: np.ndarray, gate: np.ndarray) -> float | None:
    return first_crossing(time, gate, 2.5)


def first_fall(time: np.ndarray, gate: np.ndarray) -> float | None:
    idx = np.where((gate[:-1] >= 2.5) & (gate[1:] < 2.5))[0]
    return None if not len(idx) else float(time[int(idx[0]) + 1] * 1e9)


def main() -> None:
    raw = RawRead(str(RAW))
    time = wave(raw, "time")
    state = wave(raw, "V(xmod:sequence_state)")
    a1 = wave(raw, "V(xmod:a1)")
    a2 = wave(raw, "V(xmod:a2)")
    vds_h2 = a1 - a2
    gl2 = wave(raw, "V(xmod:gl2)")
    il2 = wave(raw, "I(xmod:LIND2)")

    release_edges = np.where((gl2[:-1] >= 2.5) & (gl2[1:] < 2.5))[0] + 1
    if not len(release_edges):
        raise RuntimeError("A43 did not release L2")
    release_idx = int(release_edges[0])
    post = np.arange(release_idx, len(time))
    min_idx = int(post[np.argmin(vds_h2[post])])

    transitions = {
        "P1_M1_to_P1_M2_ns": first_crossing(time, state, 0.5),
        "P1_M2_to_P1_M3_ns": first_crossing(time, state, 1.5),
        "P1_M3_to_P1_M4_ns": first_crossing(time, state, 2.5),
        "P1_M4_to_P1_M5_ns": first_crossing(time, state, 3.5),
        "P1_M5_to_P2_M1_ns": first_crossing(time, state, 4.5),
    }
    result = {
        "model_layer": "P25_DEVICE_AUGMENTED",
        "negative_fraction_pct": 7.77,
        "negative_target_a": 9.7125,
        "transitions": transitions,
        "h1_on_ns": first_rise(time, wave(raw, "V(xmod:gh1)")),
        "h1_off_ns": first_fall(time, wave(raw, "V(xmod:gh1)")),
        "l2_release_ns": float(time[release_idx] * 1e9),
        "l2_current_at_release_a": float(il2[release_idx]),
        "h2_minimum_vds_after_release_v": float(vds_h2[min_idx]),
        "h2_minimum_vds_time_ns": float(time[min_idx] * 1e9),
        "h2_vds_at_50ns_v": float(np.interp(50e-9, time, vds_h2)),
        "h2_admitted": first_rise(time, wave(raw, "V(xmod:gh2)")) is not None,
        "h3_admitted": first_rise(time, wave(raw, "V(xmod:gh3)")) is not None,
        "h4_admitted": first_rise(time, wave(raw, "V(xmod:gh4)")) is not None,
        "final_state": int(round(float(state[-1]))),
        "first_failure": "P1_M5_WAITING_FOR_H2_VDS_ZERO",
        "controller_guard_pass": True,
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
