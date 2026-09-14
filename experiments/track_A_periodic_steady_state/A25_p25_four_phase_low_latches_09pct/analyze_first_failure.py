"""Diagnose A25 in physical-event order and print the earliest failed boundary."""

from pathlib import Path

import numpy as np
from spicelib import RawRead


HERE = Path(__file__).resolve().parent
RAW = HERE / "A25_p25_four_phase_low_latches_09pct.raw"
raw = RawRead(str(RAW))
time = np.real(raw.get_trace("time").get_wave(0))


def wave(name: str) -> np.ndarray:
    return np.real(raw.get_trace(name).get_wave(0))


a1, a2, a3 = (wave(f"V(xmod:a{i})") for i in range(1, 4))
x = [None] + [wave(f"V(xmod:x{i})") for i in range(1, 5)]
i_l = [None] + [wave(f"I(xmod:L{i})") for i in range(1, 5)]
gh = [None] + [wave(f"V(xmod:gh{i})") for i in range(1, 5)]
gl = [None] + [wave(f"V(xmod:gl{i})") for i in range(1, 5)]
state = [None] + [wave(f"V(xmod:st{i})") for i in range(1, 5)]
vds_h = [None, 48.0 - a1, a1 - a2, a2 - a3, a3 - x[4]]


def first_cross(signal: np.ndarray, level: float) -> int | None:
    indices = np.where((signal[:-1] < level) & (signal[1:] >= level))[0]
    return None if len(indices) == 0 else int(indices[0] + 1)


events = []

# At the selected periodic origin P25 Mode 1 requires lows 2-4 on. Sample at
# 2 ps, matching the established measurement rule, rather than at the exact
# ideal state-machine discontinuity t=0.
initial_sample = int(np.argmin(np.abs(time - 2e-12)))
for phase in (2, 3, 4):
    passed = gl[phase][initial_sample] > 2.5
    events.append(
        (time[initial_sample], passed, f"initial_SL{phase}_ON", gl[phase][initial_sample])
    )

# Fixed high-side commands for phases 2-4 and the next phase-1 cycle.
high_edges = {2: 50e-9, 3: 100e-9, 4: 150e-9, 1: 200e-9}
for phase, instant in high_edges.items():
    before = np.where(time < instant)[0][-1]
    passed = vds_h[phase][before] <= 0.0
    events.append(
        (instant, passed, f"SH{phase}_ZVS_before_fixed_command", vds_h[phase][before])
    )

# State crossings: phase 1 uses 0->1 admission and 1->2 release; phases 2-4
# use 0->1 release and 1->2 post-high re-admission.
for phase in range(1, 5):
    half = first_cross(state[phase], 0.5)
    one_half = first_cross(state[phase], 1.5)
    if phase == 1:
        if half is not None:
            events.append((time[half], abs(x[1][half]) <= 0.1, "SL1_ZVS_admission", x[1][half]))
        if one_half is not None:
            events.append((time[one_half], i_l[1][one_half] <= -11.25, "SL1_9pct_release", i_l[1][one_half]))
    else:
        if half is not None:
            events.append((time[half], i_l[phase][half] <= -11.25, f"SL{phase}_9pct_release", i_l[phase][half]))
        if one_half is not None:
            events.append((time[one_half], abs(x[phase][one_half]) <= 0.1, f"SL{phase}_ZVS_readmission", x[phase][one_half]))

for phase in range(1, 5):
    overlap = bool(np.any((gh[phase] > 2.5) & (gl[phase] > 2.5)))
    events.append((0.0, not overlap, f"leg{phase}_no_command_overlap", float(overlap)))

events.sort(key=lambda item: item[0])
print(f"source_raw={RAW}")
for instant, passed, name, value in events:
    print(f"event_ns={instant*1e9:.9f} pass={passed} name={name} value={value:.9f}")

failures = [event for event in events if not event[1]]
if failures:
    instant, _, name, value = failures[0]
    print(f"FIRST_FAILURE={name}")
    print(f"FIRST_FAILURE_TIME_NS={instant*1e9:.9f}")
    print(f"FIRST_FAILURE_VALUE={value:.9f}")
else:
    print("FIRST_FAILURE=NONE")
