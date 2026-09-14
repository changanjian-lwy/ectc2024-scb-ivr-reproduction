"""Compare phase-1 handoff/ZVS metrics for the P25 5/8/10% branches."""

from pathlib import Path

import numpy as np
from spicelib import RawRead


TRACK = Path(__file__).resolve().parent
CASES = {
    "A21_p25_all_inactive_lows_05pct": 0.05,
    "A22_p25_all_inactive_lows_08pct": 0.08,
    "A24_p25_all_inactive_lows_09pct": 0.09,
    "A23_p25_all_inactive_lows_10pct": 0.10,
}
VIN = 48.0
IPEAK = 125.0
T = 200e-9
TON = 16.6666666666667e-9
QH4_END = 150e-9 + TON


for name, fraction in CASES.items():
    raw_path = TRACK / name / f"{name}.raw"
    raw = RawRead(str(raw_path))
    time = np.real(raw.get_trace("time").get_wave(0))
    current = np.real(raw.get_trace("I(xmod:L1)").get_wave(0))
    a1 = np.real(raw.get_trace("V(xmod:a1)").get_wave(0))
    vds_high = VIN - a1

    zero_candidates = np.where((time > 100e-9) & (current <= 0.0))[0]
    if len(zero_candidates) == 0:
        print(name, "FAIL_NO_CURRENT_ZERO")
        continue
    zero = int(zero_candidates[0])
    threshold_candidates = np.where(
        (np.arange(len(time)) > zero) & (current <= -fraction * IPEAK)
    )[0]
    threshold = int(threshold_candidates[0]) if len(threshold_candidates) else None

    release = threshold if threshold is not None else int(
        np.argmin(np.abs(time - (QH4_END + 2e-12)))
    )
    search = np.where((time >= time[release]) & (time < T))[0]
    minimum = int(search[np.argmin(vds_high[search])])
    zvs = search[vds_high[search] <= 0.0]

    print(f"case={name}")
    print(f"target_pct={100*fraction:.1f}")
    print(f"current_zero_ns={time[zero]*1e9:.9f}")
    print(
        "threshold_event_ns="
        + ("NA" if threshold is None else f"{time[threshold]*1e9:.9f}")
    )
    print(
        "il1_at_threshold_A="
        + ("NA" if threshold is None else f"{current[threshold]:.9f}")
    )
    qh4_end_sample = int(np.argmin(np.abs(time - (QH4_END + 2e-12))))
    print(f"il1_at_qh4_end_A={current[qh4_end_sample]:.9f}")
    print(f"il1_at_release_A={current[release]:.9f}")
    print(f"minimum_vds_qh1_V={vds_high[minimum]:.9f}")
    print(f"minimum_vds_time_ns={time[minimum]*1e9:.9f}")
    print(f"natural_zvs_before_next_qh1={len(zvs)>0}")
    if len(zvs):
        first = int(zvs[0])
        print(f"first_zvs_ns={time[first]*1e9:.9f}")
        print(f"il1_at_first_zvs_A={current[first]:.9f}")
    print()
