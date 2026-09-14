"""Empirical commutation-energy audit for the two P24 inductance branches."""

from pathlib import Path

import numpy as np
from spicelib import RawRead

TRACK = Path(__file__).resolve().parent
CASES = {
    "A28_p24_phase2_event_scheduler": 1.466666666666667e-9,
    "A30_p24_table1_2p68nH_sensitivity": 2.68e-9,
}
IPEAK = 125.0
FRACTION = 0.02

for name, inductance in CASES.items():
    raw = RawRead(str(TRACK / name / f"{name}.raw"))
    time = np.real(raw.get_trace("time").get_wave(0))
    current = np.real(raw.get_trace("I(xmod:L2)").get_wave(0))
    vds = np.real(raw.get_trace("V(xmod:a1)").get_wave(0)) - np.real(
        raw.get_trace("V(xmod:a2)").get_wave(0)
    )
    state = np.real(raw.get_trace("V(xmod:st2)").get_wave(0))
    release_candidates = np.where(state >= 0.5)[0]
    release = int(release_candidates[0])
    search = np.where((time >= time[release]) & (time <= time[release] + 15e-9))[0]
    minimum = int(search[np.argmin(vds[search])])
    energy_at_target = 0.5 * inductance * (FRACTION * IPEAK) ** 2
    energy_at_release = 0.5 * inductance * current[release] ** 2
    print(f"case={name}")
    print(f"release_ns={time[release]*1e9:.9f}")
    print(f"i_at_release_A={current[release]:.9f}")
    print(f"negative_energy_target_nJ={energy_at_target*1e9:.9f}")
    print(f"negative_energy_release_nJ={energy_at_release*1e9:.9f}")
    print(f"minimum_vds_V={vds[minimum]:.9f}")
    print(f"minimum_vds_ns={time[minimum]*1e9:.9f}")
    print(f"reached_zero={bool(vds[minimum] <= 0)}")
    print()
