"""Extract every gate transition from the compiled A33 event ring."""

from pathlib import Path

import numpy as np
from spicelib import RawRead

HERE = Path(__file__).resolve().parent
raw = RawRead(str(HERE / "A33_p25_np4_compiled_event_ring_09pct.raw"))
time = np.real(raw.get_trace("time").get_wave(0))


def wave(name: str) -> np.ndarray:
    return np.real(raw.get_trace(name).get_wave(0))


def edges(signal: np.ndarray, rising: bool) -> list[int]:
    if rising:
        return list(np.where((signal[:-1] <= 2.5) & (signal[1:] > 2.5))[0] + 1)
    return list(np.where((signal[:-1] >= 2.5) & (signal[1:] < 2.5))[0] + 1)


for phase in range(1, 5):
    gate = wave(f"V(xmod:gh{phase})")
    print(f"H{phase}_rise_ns={[round(time[k]*1e9, 6) for k in edges(gate, True)]}")
    print(f"H{phase}_fall_ns={[round(time[k]*1e9, 6) for k in edges(gate, False)]}")

ordered = []
for phase in range(1, 5):
    for k in edges(wave(f"V(xmod:gh{phase})"), True):
        ordered.append((time[k], phase))
ordered.sort()
print("ordered_high_rises=", [(phase, round(t*1e9, 6)) for t, phase in ordered])
print("rise_gaps_ns=", [round((ordered[k+1][0]-ordered[k][0])*1e9, 6) for k in range(len(ordered)-1)])
